import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const API = "https://registry.npmjs.org/-/v1/search";
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function sha256(value: unknown): Promise<string> {
  const bytes = new TextEncoder().encode(JSON.stringify(value));
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function compact(raw: Record<string, any>, sourceId: string) {
  const pkg = raw.package ?? {};
  const downloads = raw.downloads ?? {};
  const links = pkg.links ?? {};
  const name = String(pkg.name ?? "").trim();
  if (!name) throw new Error("PACKAGE_NAME_MISSING");
  return {
    source_id: sourceId,
    source_external_id: name,
    entity_type: "NPM_PACKAGE",
    title: name,
    source_url: links.npm || `https://www.npmjs.com/package/${encodeURIComponent(name)}`,
    metadata: {
      version: pkg.version ?? null,
      description: pkg.description ?? null,
      keywords: Array.isArray(pkg.keywords) ? pkg.keywords.slice(0, 30) : [],
      publisher: pkg.publisher?.username ?? null,
      updated: pkg.date ?? raw.updated ?? null,
      repository_url: links.repository ?? null,
      homepage_url: links.homepage ?? null,
    },
    last_seen_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    metrics: {
      downloads_weekly: Number(downloads.weekly ?? 0),
      downloads_monthly: Number(downloads.monthly ?? 0),
      dependents: Number(raw.dependents ?? 0),
      search_score: Number(raw.score?.final ?? raw.searchScore ?? 0),
    },
  };
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
    .from("source_policy_effective_v01")
    .select("source_id,code,source_status,auto_collect,source_redisplay_allowed,commercial_use_allowed,automated_collection_allowed,redisplay_allowed")
    .eq("code", "npm")
    .single();

  if (sourceError || !source) {
    return new Response(JSON.stringify({ error: "SOURCE_NOT_FOUND" }), {
      status: 500,
      headers: { "content-type": "application/json" },
    });
  }

  const allowed =
    source.source_status === "GREEN" &&
    source.auto_collect === true &&
    source.source_redisplay_allowed === true &&
    source.commercial_use_allowed === true &&
    source.automated_collection_allowed === true &&
    source.redisplay_allowed === true;

  if (!allowed) {
    return new Response(JSON.stringify({ error: "SOURCE_POLICY_GATE_BLOCKED" }), {
      status: 403,
      headers: { "content-type": "application/json" },
    });
  }

  const { data: queries, error: queryError } = await admin
    .from("external_signal_queries")
    .select("id,code,query_spec")
    .eq("source_id", source.source_id)
    .eq("query_type", "NPM_SEARCH")
    .eq("enabled", true)
    .order("code");

  if (queryError || !queries?.length) {
    return new Response(JSON.stringify({ error: "NO_NPM_QUERIES" }), {
      status: 500,
      headers: { "content-type": "application/json" },
    });
  }

  const { data: run, error: runError } = await admin
    .from("pipeline_runs")
    .insert({
      source_id: source.source_id,
      run_type: "NPM_SIGNAL_COLLECTOR",
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
  let newSnapshots = 0;
  const entities = new Map<string, Record<string, any>>();
  const queryHits = new Map<string, Set<string>>();

  try {
    for (let i = 0; i < queries.length; i++) {
      const q = queries[i] as any;
      const text = String(q.query_spec?.text ?? "").trim();
      const size = Math.max(10, Math.min(100, Number(q.query_spec?.size ?? 50)));
      if (!text) continue;

      const url = new URL(API);
      url.searchParams.set("text", text);
      url.searchParams.set("size", String(size));
      url.searchParams.set("from", "0");

      const response = await fetch(url.toString(), {
        headers: {
          "accept": "application/json",
          "user-agent": "JianShi/0.1 npm-public-registry-signal-collector",
        },
        signal: AbortSignal.timeout(25000),
      });
      if (!response.ok) throw new Error(`NPM_HTTP_${response.status}`);

      const payload = await response.json();
      const objects = Array.isArray(payload?.objects) ? payload.objects : [];
      fetched += objects.length;

      for (const raw of objects) {
        try {
          const row = compact(raw, source.source_id);
          entities.set(row.source_external_id, row);
          const hits = queryHits.get(row.source_external_id) ?? new Set<string>();
          hits.add(String(q.code));
          queryHits.set(row.source_external_id, hits);
        } catch {
          parserErrors += 1;
        }
      }
      if (i < queries.length - 1) await sleep(350);
    }

    const normalized = [...entities.values()];
    const parserRate = fetched ? parserErrors / fetched : 1;
    const gatePass = normalized.length >= 20 && parserRate < 0.20;
    if (!gatePass) {
      throw new Error(`QUALITY_GATE_FAILED unique=${normalized.length} parser_rate=${parserRate}`);
    }

    const entityRows = normalized.map(({ metrics: _metrics, ...row }) => row);
    const { data: upserted, error: upsertError } = await admin
      .from("external_signal_entities")
      .upsert(entityRows, { onConflict: "source_id,source_external_id" })
      .select("id,source_external_id");

    if (upsertError) throw upsertError;

    const idByExternal = new Map(
      (upserted ?? []).map((x: any) => [String(x.source_external_id), x.id]),
    );
    const queryIdByCode = new Map(
      queries.map((q: any) => [String(q.code), q.id]),
    );

    const discoveryRows: Record<string, any>[] = [];
    for (const [externalId, codes] of queryHits.entries()) {
      const entityId = idByExternal.get(externalId);
      if (!entityId) continue;
      for (const code of codes) {
        const queryId = queryIdByCode.get(code);
        if (!queryId) continue;
        discoveryRows.push({
          entity_id: entityId,
          query_id: queryId,
          last_seen_at: new Date().toISOString(),
        });
      }
    }

    if (discoveryRows.length) {
      const { error } = await admin
        .from("external_signal_discoveries")
        .upsert(discoveryRows, { onConflict: "entity_id,query_id" });
      if (error) throw error;
    }

    const snapshots = [];
    for (const row of normalized) {
      const entityId = idByExternal.get(row.source_external_id);
      if (!entityId) continue;
      const snapshot = {
        metrics: row.metrics,
        version: row.metadata?.version ?? null,
        updated: row.metadata?.updated ?? null,
      };
      snapshots.push({
        entity_id: entityId,
        source_id: source.source_id,
        observed_at: new Date().toISOString(),
        snapshot_hash: await sha256(snapshot),
        metrics: row.metrics,
        metadata: {
          version: row.metadata?.version ?? null,
          updated: row.metadata?.updated ?? null,
        },
      });
    }

    if (snapshots.length) {
      const { data: inserted, error } = await admin
        .from("external_signal_snapshots")
        .upsert(snapshots, {
          onConflict: "entity_id,snapshot_hash",
          ignoreDuplicates: true,
        })
        .select("id");
      if (error) throw error;
      newSnapshots = inserted?.length ?? 0;
    }

    await admin.from("pipeline_runs").update({
      status: "SUCCESS",
      finished_at: new Date().toISOString(),
      fetched_count: fetched,
      accepted_count: normalized.length,
      duplicate_count: Math.max(0, normalized.length - newSnapshots),
      parser_error_count: parserErrors,
      quality_gate_status: "PASS",
      quality_gate_reason: {
        queries: queries.length,
        unique_entities: normalized.length,
        new_snapshots: newSnapshots,
        parser_error_rate: parserRate,
        source_role: "TECHNICAL_ADOPTION_SHADOW_ONLY",
        scoring_changed: false,
      },
    }).eq("id", run.id);

    await admin.from("data_sources")
      .update({ last_success_at: new Date().toISOString() })
      .eq("id", source.source_id);

    return new Response(JSON.stringify({
      ok: true,
      queries: queries.length,
      fetched,
      unique_entities: normalized.length,
      new_snapshots: newSnapshots,
      parser_errors: parserErrors,
      scoring_changed: false,
    }), {
      headers: { "content-type": "application/json" },
      status: 200,
    });
  } catch (error) {
    await admin.from("pipeline_runs").update({
      status: "FAILED",
      finished_at: new Date().toISOString(),
      fetched_count: fetched,
      accepted_count: entities.size,
      parser_error_count: parserErrors,
      quality_gate_status: "FAIL",
      quality_gate_reason: { error: String(error), scoring_changed: false },
    }).eq("id", run.id);

    return new Response(JSON.stringify({
      error: "COLLECTOR_FAILED",
      detail: String(error),
    }), {
      headers: { "content-type": "application/json" },
      status: 500,
    });
  }
});
