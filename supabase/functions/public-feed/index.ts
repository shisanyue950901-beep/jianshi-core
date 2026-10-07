import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET,OPTIONS",
  "access-control-allow-headers": "content-type",
  "cache-control": "public, max-age=120, s-maxage=300, stale-while-revalidate=600",
  "content-type": "application/json; charset=utf-8",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: CORS });
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  if (req.method !== "GET") return json({ error: "GET_REQUIRED" }, 405);

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!supabaseUrl || !serviceKey) return json({ error: "SERVER_CONFIG_MISSING" }, 500);

  const db = createClient(supabaseUrl, serviceKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const url = new URL(req.url);
  const view = url.searchParams.get("view") || "home";

  try {
    if (view === "home") {
      const [statsQ, catalogQ, githubQ, featuresQ] = await Promise.all([
        db.from("public_system_stats_v01").select("*").single(),
        db.from("public_opportunity_catalog_v01")
          .select("*")
          .order("public_ready", { ascending: false })
          .order("overall_score", { ascending: false }),
        db.from("public_tech_signals_v01")
          .select("full_name,summary_zh,html_url,language,stars,forks,quality_score,heat_score,rank_score,matched_queries")
          .order("rank_score", { ascending: false })
          .limit(8),
        db.rpc("get_public_feature_flags_v01"),
      ]);

      if (statsQ.error) throw statsQ.error;
      if (catalogQ.error) throw catalogQ.error;
      if (githubQ.error) throw githubQ.error;
      if (featuresQ.error) throw featuresQ.error;

      const catalog = (catalogQ.data ?? []).map(({ opportunity_id, ...rest }: any) => rest);
      return json({
        product: {
          name: "见势",
          tagline: "看见正在发生的生意机会",
          engine_version: "OPP_V0.2",
        },
        generated_at: new Date().toISOString(),
        features: featuresQ.data ?? { account_auth: false },
        stats: statsQ.data,
        opportunities: catalog.filter((x: any) => x.public_ready),
        watchlist: catalog.filter((x: any) => !x.public_ready).slice(0, 8),
        tech_signals: githubQ.data ?? [],
      });
    }

    if (view === "daily") {
      const { data, error } = await db
        .from("public_daily_brief_v01")
        .select("*")
        .order("overall_rank", { ascending: true });
      if (error) throw error;

      const items = data ?? [];
      const now = new Date().toISOString();
      return json({
        generated_at: now,
        history_ready: {
          one_day: items.some((x: any) => x.previous_date !== null),
          seven_day: items.some((x: any) => x.seven_day_date !== null),
        },
        today: items.slice(0, 10),
        rising: [...items].sort((a: any,b: any) => Number(a.rising_rank)-Number(b.rising_rank)).slice(0, 10),
        build: [...items].sort((a: any,b: any) => Number(a.build_rank)-Number(b.build_rank)).slice(0, 10),
        content: [...items].sort((a: any,b: any) => Number(a.content_rank)-Number(b.content_rank)).slice(0, 10),
      });
    }

    if (view === "catalog") {
      const { data, error } = await db.from("public_opportunity_catalog_v01")
        .select("*")
        .order("public_ready", { ascending: false })
        .order("overall_score", { ascending: false });
      if (error) throw error;
      const items = (data ?? []).map(({ opportunity_id, ...rest }: any) => rest);
      return json({ generated_at: new Date().toISOString(), items });
    }

    if (view === "detail") {
      const slug = (url.searchParams.get("slug") || "").trim();
      if (!/^[a-z0-9-]{2,80}$/.test(slug)) return json({ error: "INVALID_SLUG" }, 400);

      const { data: item, error: itemError } = await db
        .from("public_opportunity_catalog_v01")
        .select("*")
        .eq("slug", slug)
        .maybeSingle();

      if (itemError) throw itemError;
      if (!item) return json({ error: "NOT_FOUND" }, 404);

      const [githubQ, marketQ, historyQ] = await Promise.all([
        db.from("public_github_evidence_v01")
          .select("*")
          .eq("opportunity_id", item.opportunity_id)
          .order("rank_score", { ascending: false })
          .limit(10),
        db.from("public_market_evidence_v01")
          .select("*")
          .eq("opportunity_id", item.opportunity_id)
          .order("average_monthly_net_profit", { ascending: false, nullsFirst: false })
          .limit(10),
        db.from("score_snapshots")
          .select("score_kind,score,score_version,calculated_at")
          .eq("opportunity_id", item.opportunity_id)
          .eq("score_version", "OPP_V0.2")
          .order("calculated_at", { ascending: false })
          .limit(40),
      ]);

      if (githubQ.error) throw githubQ.error;
      if (marketQ.error) throw marketQ.error;
      if (historyQ.error) throw historyQ.error;

      const { opportunity_id, ...publicItem } = item as any;
      const publicGithub = (githubQ.data ?? []).map(({ opportunity_id: _o, github_repository_id: _g, ...rest }: any) => rest);
      const publicMarketplace = (marketQ.data ?? []).map(({ opportunity_id: _o, marketplace_listing_id: _m, source_url: _s, ...rest }: any) => rest);
      return json({
        generated_at: new Date().toISOString(),
        item: publicItem,
        evidence: {
          github: publicGithub,
          marketplace: publicMarketplace,
        },
        score_history: historyQ.data ?? [],
        disclosure: item.public_ready
          ? "该机会已通过当前版本的多源共振 Gate。评分是研究工具，不代表收益承诺。"
          : "该条目仍处于单源观察池，尚未通过多源共振 Gate，不应视为已验证商业机会。",
      });
    }

    return json({ error: "UNKNOWN_VIEW" }, 404);
  } catch (error) {
    return json({ error: "PUBLIC_API_FAILED", detail: String(error) }, 500);
  }
});
