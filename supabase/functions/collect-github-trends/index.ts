import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const API = "https://api.github.com/search/repositories";
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

function isoDateDaysAgo(days: number): string {
  const d = new Date(Date.now() - days * 86400_000);
  return d.toISOString().slice(0, 10);
}

function compact(raw: Record<string, any>, sourceId: string) {
  return {
    source_id: sourceId,
    github_repo_id: Number(raw.id),
    full_name: String(raw.full_name),
    owner_login: String(raw.owner?.login ?? ""),
    owner_type: raw.owner?.type ?? null,
    name: String(raw.name ?? ""),
    repo_size_kb: Number(raw.size ?? 0),
    has_issues: Boolean(raw.has_issues),
    has_projects: Boolean(raw.has_projects),
    description: raw.description ?? null,
    html_url: raw.html_url,
    homepage_url: raw.homepage || null,
    language: raw.language ?? null,
    topics: Array.isArray(raw.topics) ? raw.topics : [],
    license_spdx: raw.license?.spdx_id && raw.license.spdx_id !== "NOASSERTION"
      ? raw.license.spdx_id
      : null,
    archived: Boolean(raw.archived),
    is_fork: Boolean(raw.fork),
    default_branch: raw.default_branch ?? null,
    stargazers_count: Number(raw.stargazers_count ?? 0),
    forks_count: Number(raw.forks_count ?? 0),
    open_issues_count: Number(raw.open_issues_count ?? 0),
    github_created_at: raw.created_at ?? null,
    github_updated_at: raw.updated_at ?? null,
    pushed_at: raw.pushed_at ?? null,
    last_seen_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

async function sha256(value: unknown): Promise<string> {
  const bytes = new TextEncoder().encode(JSON.stringify(value));
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "POST_REQUIRED" }), {
      status: 405,
      headers: { "content-type": "application/json" },
    });
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const githubToken = Deno.env.get("GITHUB_TOKEN");
  if (!supabaseUrl || !serviceKey) {
    return new Response(JSON.stringify({ error: "SERVER_CONFIG_MISSING" }), {
      status: 500,
      headers: { "content-type": "application/json" },
    });
  }

  const admin = createClient(supabaseUrl, serviceKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const { data: source, error: sourceError } = await admin
    .from("data_sources")
    .select("id,code,source_status,auto_collect")
    .eq("code", "github")
    .single();

  if (sourceError || !source) {
    return new Response(JSON.stringify({ error: "SOURCE_NOT_FOUND" }), {
      status: 500,
      headers: { "content-type": "application/json" },
    });
  }
  if (source.source_status !== "GREEN" || source.auto_collect !== true) {
    return new Response(JSON.stringify({ error: "SOURCE_GATE_BLOCKED" }), {
      status: 403,
      headers: { "content-type": "application/json" },
    });
  }

  const { data: queries, error: queryError } = await admin
    .from("github_discovery_queries")
    .select("id,code,query_template,sort_by,order_by,per_page")
    .eq("enabled", true)
    .order("code");

  if (queryError || !queries?.length) {
    return new Response(JSON.stringify({ error: "NO_DISCOVERY_QUERIES" }), {
      status: 500,
      headers: { "content-type": "application/json" },
    });
  }

  const { data: run, error: runError } = await admin
    .from("pipeline_runs")
    .insert({
      source_id: source.id,
      run_type: "GITHUB_TREND_COLLECTOR",
      status: "RUNNING",
      started_at: new Date().toISOString(),
      quality_gate_status: "PENDING",
    })
    .select("id")
    .single();

  if (runError || !run) {
    return new Response(JSON.stringify({ error: "RUN_CREATE_FAILED" }), {
      status: 500,
      headers: { "content-type": "application/json" },
    });
  }

  let fetched = 0;
  let parserErrors = 0;
  let incompleteResults = 0;
  let minRateRemaining: number | null = null;
  const repos = new Map<number, Record<string, any>>();
  const queryHits = new Map<number, Set<string>>();

  try {
    for (let i = 0; i < queries.length; i++) {
      const q = queries[i];
      const queryText = String(q.query_template)
        .replace("__DATE_90D__", isoDateDaysAgo(90));
      const url = new URL(API);
      url.searchParams.set("q", queryText);
      url.searchParams.set("sort", q.sort_by || "stars");
      url.searchParams.set("order", q.order_by || "desc");
      url.searchParams.set("per_page", String(Math.min(100, q.per_page || 50)));

      const headers: Record<string, string> = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "JianShi/0.1 public-metadata-trend-collector",
      };
      if (githubToken) headers["Authorization"] = `Bearer ${githubToken}`;

      const response = await fetch(url.toString(), {
        headers,
        signal: AbortSignal.timeout(25000),
      });

      const remainingHeader = response.headers.get("x-ratelimit-remaining");
      if (remainingHeader !== null) {
        const remaining = Number(remainingHeader);
        if (Number.isFinite(remaining)) {
          minRateRemaining = minRateRemaining === null
            ? remaining
            : Math.min(minRateRemaining, remaining);
        }
      }

      if (!response.ok) {
        throw new Error(`GITHUB_HTTP_${response.status}`);
      }

      const payload = await response.json();
      if (payload?.incomplete_results === true) incompleteResults += 1;
      const items = Array.isArray(payload?.items) ? payload.items : [];
      fetched += items.length;

      for (const raw of items) {
        try {
          if (!raw?.id || !raw?.full_name || !raw?.html_url) {
            throw new Error("MISSING_REQUIRED_FIELDS");
          }
          const repoKey = Number(raw.id);
          repos.set(repoKey, compact(raw, source.id));
          const hits = queryHits.get(repoKey) ?? new Set<string>();
          hits.add(String(q.code));
          queryHits.set(repoKey, hits);
        } catch {
          parserErrors += 1;
        }
      }

      if (i < queries.length - 1) await sleep(1300);
    }

    const normalized = [...repos.values()];
    const parserRate = fetched ? parserErrors / fetched : 1;
    const gatePass = normalized.length >= 20 && parserRate < 0.2;

    if (!gatePass) {
      throw new Error(
        `QUALITY_GATE_FAILED unique=${normalized.length} parser_rate=${parserRate}`,
      );
    }

    const { data: upserted, error: upsertError } = await admin
      .from("github_repositories")
      .upsert(normalized, { onConflict: "source_id,github_repo_id" })
      .select("id,github_repo_id");

    if (upsertError) throw upsertError;

    const idByGithubId = new Map(
      (upserted ?? []).map((row: any) => [Number(row.github_repo_id), row.id]),
    );

    const queryIdByCode = new Map(
      queries.map((q: any) => [String(q.code), q.id]),
    );
    const discoveryRows: Record<string, any>[] = [];
    for (const [githubId, codes] of queryHits.entries()) {
      const repoId = idByGithubId.get(githubId);
      if (!repoId) continue;
      for (const code of codes) {
        const queryId = queryIdByCode.get(code);
        if (!queryId) continue;
        discoveryRows.push({
          github_repository_id: repoId,
          query_id: queryId,
          last_seen_at: new Date().toISOString(),
        });
      }
    }
    if (discoveryRows.length) {
      const { error: discoveryError } = await admin
        .from("github_repository_discoveries")
        .upsert(discoveryRows, {
          onConflict: "github_repository_id,query_id",
        });
      if (discoveryError) throw discoveryError;
    }

    const snapshots = [];
    for (const row of normalized) {
      const repoId = idByGithubId.get(Number(row.github_repo_id));
      if (!repoId) continue;
      const snapshot = {
        stargazers_count: row.stargazers_count,
        forks_count: row.forks_count,
        open_issues_count: row.open_issues_count,
        pushed_at: row.pushed_at,
        github_updated_at: row.github_updated_at,
      };
      snapshots.push({
        github_repository_id: repoId,
        source_id: source.id,
        observed_at: new Date().toISOString(),
        snapshot_hash: await sha256(snapshot),
        stargazers_count: row.stargazers_count,
        forks_count: row.forks_count,
        open_issues_count: row.open_issues_count,
        pushed_at: row.pushed_at,
        github_updated_at: row.github_updated_at,
        snapshot,
      });
    }

    let newSnapshots = 0;
    if (snapshots.length) {
      const { data: inserted, error: snapshotError } = await admin
        .from("github_repository_snapshots")
        .upsert(snapshots, {
          onConflict: "github_repository_id,snapshot_hash",
          ignoreDuplicates: true,
        })
        .select("id");
      if (snapshotError) throw snapshotError;
      newSnapshots = inserted?.length ?? 0;
    }

    const { data: signalCount, error: signalError } = await admin
      .rpc("refresh_github_momentum_signals");
    if (signalError) throw signalError;

    await admin
      .from("pipeline_runs")
      .update({
        status: "SUCCESS",
        finished_at: new Date().toISOString(),
        fetched_count: fetched,
        accepted_count: normalized.length,
        duplicate_count: Math.max(0, normalized.length - newSnapshots),
        parser_error_count: parserErrors,
        quality_gate_status: "PASS",
        quality_gate_reason: {
          discovery_queries: queries.length,
          unique_repositories: normalized.length,
          new_snapshots: newSnapshots,
          signals_created: signalCount ?? 0,
          incomplete_result_queries: incompleteResults,
          min_rate_remaining: minRateRemaining,
          authenticated_github_api: Boolean(githubToken),
        },
      })
      .eq("id", run.id);

    await admin
      .from("data_sources")
      .update({ last_success_at: new Date().toISOString() })
      .eq("id", source.id);

    return new Response(JSON.stringify({
      ok: true,
      queries: queries.length,
      fetched,
      unique_repositories: normalized.length,
      parser_errors: parserErrors,
      new_snapshots: newSnapshots,
      signals_created: signalCount ?? 0,
      min_rate_remaining: minRateRemaining,
      authenticated_github_api: Boolean(githubToken),
    }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  } catch (error) {
    await admin
      .from("pipeline_runs")
      .update({
        status: "FAILED",
        finished_at: new Date().toISOString(),
        fetched_count: fetched,
        accepted_count: repos.size,
        parser_error_count: parserErrors,
        quality_gate_status: "FAIL",
        quality_gate_reason: {
          error: String(error),
          incomplete_result_queries: incompleteResults,
          min_rate_remaining: minRateRemaining,
        },
      })
      .eq("id", run.id);

    return new Response(JSON.stringify({
      error: "COLLECTOR_FAILED",
      detail: String(error),
    }), {
      status: 500,
      headers: { "content-type": "application/json" },
    });
  }
});
