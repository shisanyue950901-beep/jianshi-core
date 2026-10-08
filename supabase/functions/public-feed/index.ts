import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET,OPTIONS",
  "access-control-allow-headers": "content-type",
  "cache-control": "no-store, max-age=0",
  "content-type": "application/json; charset=utf-8",
};

const RESEARCH_RULES: Record<string, { title: string; patterns: string[] }> = {
  "vertical-industry-saas": { title: "行业软件订阅项目", patterns: ["SaaS Business"] },
  "amazon-fba-niche-brand": { title: "亚马逊物流（FBA）品牌项目", patterns: ["Amazon FBA Business"] },
  "digital-product-business": { title: "数字产品项目", patterns: ["Digital Product Business"] },
  "affiliate-content-site": { title: "联盟营销与内容网站", patterns: ["Affiliate Site","Amazon Associates Site","Display Advertising Site"] },
  "amazon-kdp-publishing": { title: "亚马逊 KDP 出版项目", patterns: ["Amazon KDP Business"] },
  "agency-business": { title: "专业服务项目", patterns: ["Agency Business"] },
};

// 英文原始分类仅用于服务端匹配，公开接口绝不返回原词或原始记录。
const NICHE_ZH: Record<string,string> = {
  "Personal Care":"个人护理","Medical":"医疗健康","Health & Fitness":"健康健身",
  "Sports":"体育运动","Information":"信息服务","Business":"商业服务",
  "Technology":"科技","News & Education":"资讯教育","Gaming":"游戏",
  "Employment":"招聘就业","Lifestyle":"生活方式","Art":"艺术",
  "Hobbies":"兴趣爱好","Design":"设计","Digital Media":"数字媒体",
  "SEO":"搜索引擎优化","Advertising":"广告营销","Home":"家居",
  "Children":"母婴儿童","Books":"图书","Romance":"文学小说",
  "Occasions & Gifts":"礼品","Culinary":"食品烹饪",
  "Religion & Spirituality":"宗教与文化","Office Supply":"办公用品",
  "Retail & Wholesale":"零售批发","Survival & Security":"安全防护",
  "Pet Care":"宠物护理","Outdoors":"户外","Automotive":"汽车用品",
  "Finance":"金融服务","Travel":"旅行","Beauty":"美容",
  "Equipment":"设备用品","Kitchenware":"厨具","Supplements":"营养补充",
  "Apparel & Accessories":"服饰配件","Bed & Bath":"家纺卫浴",
  "Electronics":"电子产品","Pets":"宠物用品"
};
function localizedNiche(raw: unknown): string {
  const text = String(raw || "").trim();
  return NICHE_ZH[text] || "其他领域";
}
function amountBand(v: unknown): string {
  const value = toNumber(v);
  if (value === null) return "未披露";
  if (value < 10000) return "不足1万美元";
  if (value < 50000) return "1万—5万美元";
  if (value < 100000) return "5万—10万美元";
  if (value < 500000) return "10万—50万美元";
  return "50万美元及以上";
}

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
  const counts = new Map<string,number>();
  for (const row of rows) {
    const labels = new Set<string>((Array.isArray(row.niches) ? row.niches : []).map(localizedNiche));
    for (const label of labels) counts.set(label, (counts.get(label) || 0) + 1);
  }
  return [...counts.entries()].map(([name,count]) => ({name,count}))
    .sort((a,b) => b.count - a.count || a.name.localeCompare(b.name,"zh")).slice(0,12);
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
        tech_signals: [], // 原始仓库、来源及发现路径不公开
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
      if (!rule) return json({error:"RESEARCH_NOT_FOUND"},404);
      let q = db.from("marketplace_listings")
        .select("public_title,listing_price,average_monthly_gross_revenue,average_monthly_net_profit,profit_margin,hours_worked_per_week,niches,source_updated_at")
        .eq("active",true);
      if (rule.patterns.length === 1) {
        q = q.ilike("public_title",`%${rule.patterns[0]}%`);
      } else {
        q = q.or(rule.patterns.map(x => `public_title.ilike.%${x}%`).join(","));
      }
      const {data,error} = await q;
      if (error) throw error;
      const rows = data ?? [];
      const priced = rows.filter((r:any) => toNumber(r.listing_price) !== null);
      // 服务端先完成归类和统计：不可向客户端发送原始标题、平台名、
      // 接口地址、原始分类、挂牌编号、精确逐条财务或更新时间。
      const examples = [...rows]
        .sort((a:any,b:any) => String(b.source_updated_at||"").localeCompare(String(a.source_updated_at||"")))
        .slice(0,6)
        .map((r:any,idx:number) => ({
          display_name: `${localizedNiche((r.niches||[])[0])} · ${rule.title}`,
          display_order: idx + 1,
          monthly_revenue_band: amountBand(r.average_monthly_gross_revenue),
          monthly_profit_band: amountBand(r.average_monthly_net_profit),
          asking_price_band: amountBand(r.listing_price),
        }));
      return json({
        slug,
        title:rule.title,
        sample_definition:"按照公开项目的业务形态归类并去重统计；原始渠道和项目标识不对外展示。",
        active_sample_count:rows.length,
        priced_sample_count:priced.length,
        metrics:{
          median_asking_price:median(rows,"listing_price"),
          median_monthly_gross_revenue:median(rows,"average_monthly_gross_revenue"),
          median_monthly_net_profit:median(rows,"average_monthly_net_profit"),
          median_profit_margin_pct:median(rows,"profit_margin"),
          median_hours_worked_per_week:median(rows,"hours_worked_per_week"),
        },
        niche_distribution:nicheDistribution(rows),
        samples:examples,
        evidence_boundary:[
          "财务和工时为第三方公开项目资料中的披露值，见势未独立审计。",
          "挂牌报价不等于最终成交价。",
          "统计代表被观察到的项目，不代表总体市场表现或收益预期。",
          "具体数据渠道、原始标识及采集方式属于内部研究资产，不对外公布。"
        ]
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
          github: [],
          marketplace: [],
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
    return json({ error: "PUBLIC_API_FAILED" }, 500);
  }
});
