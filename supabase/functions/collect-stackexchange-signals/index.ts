import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const API = "https://api.stackexchange.com/2.3/search";
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

function epochDaysAgo(days: number): string {
  return String(Math.floor((Date.now() - days * 86400_000) / 1000));
}

async function sha256(value: unknown): Promise<string> {
  const bytes = new TextEncoder().encode(JSON.stringify(value));
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function stackSiteUrl(site: string): string {
  return site === "stackoverflow"
    ? "https://stackoverflow.com"
    : `https://${site}.stackexchange.com`;
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
    .eq("code", "stack_exchange")
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
    .eq("query_type", "STACKEXCHANGE_TAG_COUNT")
    .eq("enabled", true)
    .order("code");

  if (queryError || !queries?.length) {
    return new Response(JSON.stringify({ error: "NO_STACKEXCHANGE_QUERIES" }), {
      status: 500,
      headers: { "content-type": "application/json" },
    });
  }

  const { data: run, error: runError } = await admin
    .from("pipeline_runs")
    .insert({
      source_id: source.source_id,
      run_type: "STACKEXCHANGE_SIGNAL_COLLECTOR",
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

  let requestCount = 0;
  let parserErrors = 0;
  let newSnapshots = 0;
  let minQuotaRemaining: number | null = null;
  const rows: Record<string, any>[] = [];

  try {
    for (let i = 0; i < queries.length; i++) {
      const q = queries[i] as any;
      const site = String(q.query_spec?.site || "stackoverflow");
      const tag = String(q.query_spec?.tag || "").trim().toLowerCase();
      if (!/^[a-z0-9.+#-]{1,50}$/.test(tag)) {
        parserErrors += 1;
        continue;
      }

      const counts: Record<string, number> = {};
      for (const days of [7, 30]) {
        if (requestCount > 0) await sleep(250);

        const url = new URL(API);
        url.searchParams.set("site", site);
        url.searchParams.set("tagged", tag);
        url.searchParams.set("fromdate", epochDaysAgo(days));
        url.searchParams.set("order", "desc");
        url.searchParams.set("sort", "creation");
        url.searchParams.set("pagesize", "1");
        url.searchParams.set("filter", "total");

        const response = await fetch(url.toString(), {
          headers: {
            "accept": "application/json",
            "user-agent": "JianShi/0.1 StackExchange-demand-signal",
          },
          signal: AbortSignal.timeout(25000),
        });
        requestCount += 1;

        if (!response.ok) throw new Error(`STACKEXCHANGE_HTTP_${response.status}`);
        const payload = await response.json();

        if (Number.isFinite(Number(payload?.quota_remaining))) {
          const qr = Number(payload.quota_remaining);
          minQuotaRemaining = minQuotaRemaining === null ? qr : Math.min(minQuotaRemaining, qr);
        }
        if (Number(payload?.backoff) > 0) {
          const seconds = Number(payload.backoff);
          if (seconds <= 3) await sleep(seconds * 1000);
          else throw new Error(`STACKEXCHANGE_BACKOFF_${seconds}`);
        }

        const total = Number(payload?.total);
        if (!Number.isFinite(total) || total < 0) {
          throw new Error(`STACKEXCHANGE_TOTAL_INVALID_${q.code}_${days}D`);
        }
        counts[String(days)] = total;
      }

      if (counts["30"] < counts["7"]) {
        throw new Error(`STACKEXCHANGE_WINDOW_INCONSISTENT_${q.code}`);
      }

      const recentDaily = counts["7"] / 7;
      const monthlyDaily = counts["30"] / 30;
      rows.push({
        query_id: q.id,
        query_code: q.code,
        source_external_id: `${site}:${tag}`,
        title: `Stack Overflow #${tag}`,
        source_url: `${stackSiteUrl(site)}/questions/tagged/${encodeURIComponent(tag)}`,
        metadata: {
          site,
          tag,
          attribution: "Stack Overflow / Stack Exchange API",
          fulltext_stored: false,
        },
        metrics: {
          questions_7d: counts["7"],
          questions_30d: counts["30"],
          recent_questions_per_day: Number(recentDaily.toFixed(4)),
          thirty_day_questions_per_day: Number(monthlyDaily.toFixed(4)),
          recency_ratio: monthlyDaily > 0
            ? Number((recentDaily / monthlyDaily).toFixed(4))
            : 0,
        },
      });
    }

    const gatePass = rows.length >= 4 && parserErrors / Math.max(queries.length, 1) < 0.20;
    if (!gatePass) {
      throw new Error(`QUALITY_GATE_FAILED rows=${rows.length} parser_errors=${parserErrors}`);
    }

    const entityRows = rows.map((row) => ({
      source_id: source.source_id,
      source_external_id: row.source_external_id,
      entity_type: "STACKEXCHANGE_TAG",
      title: row.title,
      source_url: row.source_url,
      metadata: row.metadata,
      last_seen_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }));

    const { data: upserted, error: upsertError } = await admin
      .from("external_signal_entities")
      .upsert(entityRows, { onConflict: "source_id,source_external_id" })
      .select("id,source_external_id");

    if (upsertError) throw upsertError;

    const idByExternal = new Map(
      (upserted ?? []).map((x: any) => [String(x.source_external_id), x.id]),
    );

    const discoveries = rows
      .map((row) => ({
        entity_id: idByExternal.get(row.source_external_id),
        query_id: row.query_id,
        last_seen_at: new Date().toISOString(),
      }))
      .filter((x) => Boolean(x.entity_id));

    if (discoveries.length) {
      const { error } = await admin
        .from("external_signal_discoveries")
        .upsert(discoveries, { onConflict: "entity_id,query_id" });
      if (error) throw error;
    }

    const snapshots = [];
    for (const row of rows) {
      const entityId = idByExternal.get(row.source_external_id);
      if (!entityId) continue;
      snapshots.push({
        entity_id: entityId,
        source_id: source.source_id,
        observed_at: new Date().toISOString(),
        snapshot_hash: await sha256(row.metrics),
        metrics: row.metrics,
        metadata: {
          query_code: row.query_code,
          fulltext_stored: false,
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
      fetched_count: requestCount,
      accepted_count: rows.length,
      parser_error_count: parserErrors,
      quality_gate_status: "PASS",
      quality_gate_reason: {
        queries: queries.length,
        api_requests: requestCount,
        accepted_tag_signals: rows.length,
        new_snapshots: newSnapshots,
        min_quota_remaining: minQuotaRemaining,
        fulltext_stored: false,
        source_role: "DEMAND_SIGNAL_SHADOW_ONLY",
        scoring_changed: false,
      },
    }).eq("id", run.id);

    await admin.from("data_sources")
      .update({ last_success_at: new Date().toISOString() })
      .eq("id", source.source_id);

    return new Response(JSON.stringify({
      ok: true,
      queries: queries.length,
      api_requests: requestCount,
      accepted_tag_signals: rows.length,
      new_snapshots: newSnapshots,
      parser_errors: parserErrors,
      min_quota_remaining: minQuotaRemaining,
      fulltext_stored: false,
      scoring_changed: false,
    }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  } catch (error) {
    await admin.from("pipeline_runs").update({
      status: "FAILED",
      finished_at: new Date().toISOString(),
      fetched_count: requestCount,
      accepted_count: rows.length,
      parser_error_count: parserErrors,
      quality_gate_status: "FAIL",
      quality_gate_reason: {
        error: String(error),
        api_requests: requestCount,
        fulltext_stored: false,
        scoring_changed: false,
      },
    }).eq("id", run.id);

    return new Response(JSON.stringify({
      error: "COLLECTOR_FAILED",
      detail: String(error),
    }), {
      status: 500,
      headers: { "content-type": "application/json" },
    });
  }
});
