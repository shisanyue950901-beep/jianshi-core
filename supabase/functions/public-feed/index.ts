import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET,OPTIONS",
  "access-control-allow-headers": "content-type",
  "cache-control": "public, max-age=120, s-maxage=300, stale-while-revalidate=600",
  "content-type": "application/json; charset=utf-8",
};

const RESEARCH_RULES: Record<string, { title: string; patterns: string[]; sampleDefinition: string }> = {
  "vertical-industry-saas": {
    title: "垂直行业软件订阅服务（SaaS）",
    patterns: ["SaaS Business"],
    sampleDefinition: "在售挂牌中，公开标题明确归类为 SaaS Business 的商业资产。",
  },
  "amazon-fba-niche-brand": {
    title: "亚马逊物流（FBA）细分品牌",
    patterns: ["Amazon FBA Business"],
    sampleDefinition: "在售挂牌中，公开标题明确归类为 Amazon FBA Business 的商业资产。",
  },
  "digital-product-business": {
    title: "数字产品业务",
    patterns: ["Digital Product Business"],
    sampleDefinition: "在售挂牌中，公开标题明确归类为 Digital Product Business 的商业资产。",
  },
  "affiliate-content-site": {
    title: "联盟营销 / 内容站",
    patterns: ["Affiliate Site", "Amazon Associates Site", "Display Advertising Site"],
    sampleDefinition: "在售挂牌中，公开标题明确归类为 Affiliate Site、Amazon Associates Site 或 Display Advertising Site 的商业资产。",
  },
  "amazon-kdp-publishing": {
    title: "亚马逊 KDP 数字出版",
    patterns: ["Amazon KDP Business"],
    sampleDefinition: "在售挂牌中，公开标题明确归类为 Amazon KDP Business 的商业资产。",
  },
  "agency-business": {
    title: "专业服务业务（Agency）",
    patterns: ["Agency Business"],
    sampleDefinition: "在售挂牌中，公开标题明确归类为 Agency Business 的商业资产。",
  },
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: CORS });
}

function toNumber(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function median(rows: any[], key: string): number | null {
  const values = rows
    .map((row) => toNumber(row[key]))
    .filter((value): value is number => value !== null)
    .sort((a, b) => a - b);
  if (!values.length) return null;
  const mid = Math.floor(values.length / 2);
  if (values.length % 2) return values[mid];
  return (values[mid - 1] + values[mid]) / 2;
}

function nicheDistribution(rows: any[]) {
  const counts = new Map<string, number>();
  for (const row of rows) {
    for (const niche of Array.isArray(row.niches) ? row.niches : []) {
      const label = String(niche || "").trim();
      if (!label) continue;
      counts.set(label, (counts.get(label) || 0) + 1);
    }
  }
  return [...counts.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
    .slice(0, 12);
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

    if (view === "research") {
      const slug = (url.searchParams.get("slug") || "").trim();
      const rule = RESEARCH_RULES[slug];
      if (!rule) return json({ error: "RESEARCH_NOT_FOUND" }, 404);

      let listingQ = db.from("marketplace_listings")
        .select([
          "listing_number",
          "public_title",
          "listing_status",
          "listing_price",
          "average_monthly_gross_revenue",
          "average_monthly_net_profit",
          "profit_margin",
          "hours_worked_per_week",
          "country_code",
          "niches",
          "first_made_money_at",
          "source_updated_at",
        ].join(","))
        .eq("active", true);

      if (rule.patterns.length === 1) {
        listingQ = listingQ.ilike("public_title", `%${rule.patterns[0]}%`);
      } else {
        listingQ = listingQ.or(
          rule.patterns.map((pattern) => `public_title.ilike.%${pattern}%`).join(","),
        );
      }

      const [listingResult, sourceResult] = await Promise.all([
        listingQ,
        db.from("data_sources")
          .select("name,homepage_url,access_method,last_success_at")
          .eq("code", "empire_flippers")
          .maybeSingle(),
      ]);

      if (listingResult.error) throw listingResult.error;
      if (sourceResult.error) throw sourceResult.error;

      const rows = listingResult.data ?? [];
      const priced = rows.filter((row: any) => toNumber(row.listing_price) !== null);
      const sorted = [...rows].sort((a: any, b: any) =>
        String(b.source_updated_at || "").localeCompare(String(a.source_updated_at || ""))
      );

      return json({
        generated_at: new Date().toISOString(),
        slug,
        title: rule.title,
        sample_definition: rule.sampleDefinition,
        evidence_source: sourceResult.data ?? {
          name: "Empire Flippers",
          homepage_url: "https://empireflippers.com",
          access_method: "OFFICIAL_API",
          last_success_at: null,
        },
        active_sample_count: rows.length,
        priced_sample_count: priced.length,
        metrics: {
          median_asking_price: median(rows, "listing_price"),
          median_monthly_gross_revenue: median(rows, "average_monthly_gross_revenue"),
          median_monthly_net_profit: median(rows, "average_monthly_net_profit"),
          median_profit_margin_pct: median(rows, "profit_margin"),
          median_hours_worked_per_week: median(rows, "hours_worked_per_week"),
        },
        niche_distribution: nicheDistribution(rows),
        samples: sorted.slice(0, 6).map((row: any) => ({
          listing_number: row.listing_number,
          public_title: row.public_title,
          listing_status: row.listing_status,
          listing_price: toNumber(row.listing_price),
          average_monthly_gross_revenue: toNumber(row.average_monthly_gross_revenue),
          average_monthly_net_profit: toNumber(row.average_monthly_net_profit),
          profit_margin: toNumber(row.profit_margin),
          hours_worked_per_week: toNumber(row.hours_worked_per_week),
          country_code: row.country_code,
          niches: row.niches ?? [],
          first_made_money_at: row.first_made_money_at,
          source_updated_at: row.source_updated_at,
        })),
        evidence_boundary: [
          "财务、工时和报价字段来自挂牌方公开披露，见势未对其进行独立审计。",
          "挂牌报价不等于最终成交价。",
          "当前该研究分类仅来自一个独立商业来源，不构成多源商业验证。",
          "这些样本不能用于证明团队规模、中国市场适配性、可复制性或未来收益。",
        ],
      });
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

      const [githubQ, marketQ, historyQ, accelerationQ] = await Promise.all([
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
        db.from("opportunity_github_acceleration_v01")
          .select("rising_repo_count,recent_stars_per_day_sum,recent_stars_per_day_avg,avg_recent_velocity_score,max_recent_velocity_score,avg_observation_window_hours")
          .eq("opportunity_id", item.opportunity_id)
          .maybeSingle(),
      ]);

      if (githubQ.error) throw githubQ.error;
      if (marketQ.error) throw marketQ.error;
      if (historyQ.error) throw historyQ.error;
      if (accelerationQ.error) throw accelerationQ.error;

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
        acceleration: accelerationQ.data ?? {
          rising_repo_count: 0,
          recent_stars_per_day_sum: 0,
          recent_stars_per_day_avg: 0,
          avg_recent_velocity_score: 0,
          max_recent_velocity_score: 0,
          avg_observation_window_hours: 0,
        },
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
