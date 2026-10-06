import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const API = "https://api.empireflippers.com/api/v1/listings/list";
const PAGE_SIZE = 100;
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

function num(v: unknown): number | null {
  if (v === null || v === undefined || v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function dateDaysAgo(days: number): string {
  const d = new Date(Date.now() - days * 86400000);
  return d.toISOString().slice(0, 10);
}

function compact(raw: Record<string, any>, sourceId: string) {
  const status = raw.listing_status ?? null;
  return {
    source_id: sourceId,
    source_external_id: String(raw.id),
    listing_number: raw.listing_number ?? null,
    public_title: raw.public_title ?? null,
    listing_status: status,
    listing_price: num(raw.listing_price),
    unpriced: Boolean(raw.unpriced),
    average_monthly_net_profit: num(raw.average_monthly_net_profit),
    average_monthly_expenses: num(raw.average_monthly_expenses),
    average_monthly_gross_revenue: num(raw.average_monthly_gross_revenue),
    average_annual_net_profit: num(raw.average_annual_net_profit),
    average_annual_expenses: num(raw.average_annual_expenses),
    average_annual_gross_revenue: num(raw.average_annual_gross_revenue),
    listing_multiple: num(raw.listing_multiple),
    annual_listing_multiple: num(raw.annual_listing_multiple),
    listing_multiple_type: raw.listing_multiple_type ?? null,
    profit_margin: num(raw.profit_margin),
    mrr: num(raw.mrr),
    churn_percent: num(raw.churn_percent),
    growth_percent: num(raw.growth_percent),
    hours_worked_per_week: num(raw.hours_worked_per_week),
    days_on_marketplace: raw.days_on_marketplace ?? null,
    country_code: raw.country ?? null,
    countries: Array.isArray(raw.countries) ? raw.countries : [],
    monetizations: Array.isArray(raw.monetizations)
      ? raw.monetizations.map((x: any) => x?.monetization).filter(Boolean)
      : [],
    niches: Array.isArray(raw.niches)
      ? raw.niches.map((x: any) => x?.niche).filter(Boolean)
      : [],
    first_made_money_at: raw.first_made_money_at ?? null,
    first_listed_at: raw.first_listed_at ?? null,
    reason_for_sale: raw.reason_for_sale ?? null,
    source_updated_at: raw.updated_at ?? null,
    source_url: API,
    last_seen_at: new Date().toISOString(),
    active: status === "For Sale",
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
  if (!supabaseUrl || !serviceKey) {
    return new Response(JSON.stringify({ error: "SERVER_CONFIG_MISSING" }), {
      status: 500,
      headers: { "content-type": "application/json" },
    });
  }

  const admin = createClient(supabaseUrl, serviceKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const body = await req.json().catch(() => ({}));
  const startPage = Math.max(1, Math.min(100, Number(body.start_page ?? 1)));
  const activeMaxPages = Math.max(1, Math.min(10, Number(body.active_max_pages ?? body.max_pages ?? 5)));
  const soldMaxPages = Math.max(1, Math.min(10, Number(body.sold_max_pages ?? 5)));
  const includeSold = body.include_sold !== false;
  const soldLookbackDays = Math.max(7, Math.min(365, Number(body.sold_lookback_days ?? 120)));
  const soldAtFrom = dateDaysAgo(soldLookbackDays);

  const { data: source, error: sourceError } = await admin
    .from("data_sources")
    .select("id,code,source_status,auto_collect")
    .eq("code", "empire_flippers")
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

  const { data: run, error: runError } = await admin
    .from("pipeline_runs")
    .insert({
      source_id: source.id,
      run_type: "EMPIRE_FLIPPERS_COLLECTOR",
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
  let accepted = 0;
  let parserErrors = 0;
  let newSnapshots = 0;
  let totalPages = 0;
  let requestCount = 0;
  let soldWarning: string | null = null;
  const statusCounts: Record<string, { pages: number; fetched: number; accepted: number }> = {
    "For Sale": { pages: 0, fetched: 0, accepted: 0 },
    Sold: { pages: 0, fetched: 0, accepted: 0 },
  };

  async function collectStatus(
    status: "For Sale" | "Sold",
    maxPages: number,
    extra: Record<string, string> = {},
  ) {
    for (let page = startPage; page < startPage + maxPages; page++) {
      if (requestCount > 0) await sleep(1050);

      const params = new URLSearchParams({
        page: String(page),
        limit: String(PAGE_SIZE),
        listing_status: status,
        ...extra,
      });
      const response = await fetch(`${API}?${params.toString()}`, {
        headers: { "User-Agent": "JianShi/0.2 official-api-collector" },
        signal: AbortSignal.timeout(25000),
      });
      requestCount += 1;
      if (!response.ok) throw new Error(`${status.replace(" ", "_")}_UPSTREAM_HTTP_${response.status}`);

      const payload = await response.json();
      const listings = payload?.data?.listings ?? [];
      if (!Array.isArray(listings)) throw new Error(`${status.replace(" ", "_")}_UPSTREAM_SCHEMA_INVALID`);
      if (listings.length === 0) break;

      totalPages += 1;
      statusCounts[status].pages += 1;
      fetched += listings.length;
      statusCounts[status].fetched += listings.length;

      const normalized: Record<string, any>[] = [];
      for (const raw of listings) {
        try {
          if (!raw?.id) throw new Error("MISSING_ID");
          normalized.push(compact(raw, source.id));
        } catch {
          parserErrors += 1;
        }
      }

      if (normalized.length) {
        const { data: upserted, error: upsertError } = await admin
          .from("marketplace_listings")
          .upsert(normalized, { onConflict: "source_id,source_external_id" })
          .select("id,source_external_id");

        if (upsertError) throw upsertError;
        const acceptedHere = upserted?.length ?? 0;
        accepted += acceptedHere;
        statusCounts[status].accepted += acceptedHere;

        const idByExternal = new Map(
          (upserted ?? []).map((row: any) => [String(row.source_external_id), row.id]),
        );

        const snapshots = [];
        for (const row of normalized) {
          const listingId = idByExternal.get(String(row.source_external_id));
          if (!listingId) continue;
          const snapshot = {
            listing_number: row.listing_number,
            listing_price: row.listing_price,
            monthly_profit: row.average_monthly_net_profit,
            monthly_revenue: row.average_monthly_gross_revenue,
            annual_profit: row.average_annual_net_profit,
            annual_revenue: row.average_annual_gross_revenue,
            listing_multiple: row.listing_multiple,
            annual_listing_multiple: row.annual_listing_multiple,
            profit_margin: row.profit_margin,
            mrr: row.mrr,
            churn_percent: row.churn_percent,
            growth_percent: row.growth_percent,
            days_on_marketplace: row.days_on_marketplace,
            status: row.listing_status,
            source_updated_at: row.source_updated_at,
          };
          snapshots.push({
            marketplace_listing_id: listingId,
            source_id: source.id,
            observed_at: new Date().toISOString(),
            snapshot_hash: await sha256(snapshot),
            snapshot,
          });
        }

        if (snapshots.length) {
          const { data: inserted, error: snapshotError } = await admin
            .from("marketplace_listing_snapshots")
            .upsert(snapshots, {
              onConflict: "marketplace_listing_id,snapshot_hash",
              ignoreDuplicates: true,
            })
            .select("id");
          if (snapshotError) throw snapshotError;
          newSnapshots += inserted?.length ?? 0;
        }
      }

      if (listings.length < PAGE_SIZE) break;
    }
  }

  try {
    await collectStatus("For Sale", activeMaxPages);

    if (includeSold) {
      try {
        await collectStatus("Sold", soldMaxPages, { sold_at_from: soldAtFrom });
      } catch (error) {
        soldWarning = String(error);
      }
    }

    const parserRate = fetched ? parserErrors / fetched : 1;
    const gatePass = statusCounts["For Sale"].fetched > 0 && parserRate < 0.2;
    const qualityStatus = gatePass
      ? (soldWarning ? "PASS_WITH_WARNINGS" : "PASS")
      : "FAIL";

    await admin
      .from("pipeline_runs")
      .update({
        status: gatePass ? "SUCCESS" : "FAILED",
        finished_at: new Date().toISOString(),
        fetched_count: fetched,
        accepted_count: accepted,
        duplicate_count: Math.max(0, accepted - newSnapshots),
        parser_error_count: parserErrors,
        quality_gate_status: qualityStatus,
        quality_gate_reason: {
          total_pages: totalPages,
          page_size: PAGE_SIZE,
          start_page: startPage,
          active_max_pages: activeMaxPages,
          sold_max_pages: soldMaxPages,
          include_sold: includeSold,
          sold_lookback_days: soldLookbackDays,
          sold_at_from: soldAtFrom,
          status_counts: statusCounts,
          sold_warning: soldWarning,
          new_snapshots: newSnapshots,
          parser_error_rate: parserRate,
          sold_values_are_observed_status_not_transaction_price: true,
        },
      })
      .eq("id", run.id);

    if (gatePass) {
      await admin
        .from("data_sources")
        .update({ last_success_at: new Date().toISOString() })
        .eq("id", source.id);
    }

    return new Response(
      JSON.stringify({
        ok: gatePass,
        quality_status: qualityStatus,
        pages: totalPages,
        fetched,
        accepted,
        parser_errors: parserErrors,
        new_snapshots: newSnapshots,
        status_counts: statusCounts,
        sold_warning: soldWarning,
        sold_lookback_days: soldLookbackDays,
      }),
      {
        status: gatePass ? 200 : 503,
        headers: { "content-type": "application/json" },
      },
    );
  } catch (error) {
    await admin
      .from("pipeline_runs")
      .update({
        status: "FAILED",
        finished_at: new Date().toISOString(),
        fetched_count: fetched,
        accepted_count: accepted,
        parser_error_count: parserErrors,
        quality_gate_status: "FAIL",
        quality_gate_reason: { error: String(error), status_counts: statusCounts },
      })
      .eq("id", run.id);

    return new Response(JSON.stringify({ error: "COLLECTOR_FAILED" }), {
      status: 500,
      headers: { "content-type": "application/json" },
    });
  }
});
