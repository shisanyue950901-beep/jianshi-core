import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const API = "https://dalfvgehosxfyxkptxwx.supabase.co/functions/v1/public-feed";

const CSS = `
:root{--bg:#f3f0e8;--paper:#fffdf8;--ink:#151515;--muted:#716d66;--line:#dcd6cb;--accent:#d94b2b;--good:#267356;--watch:#9a6424;--max:1180px}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,"PingFang SC","Microsoft YaHei",system-ui,sans-serif;line-height:1.65}
a{color:inherit;text-decoration:none}.wrap{max-width:var(--max);margin:auto;padding:0 24px}
header{position:sticky;top:0;z-index:5;background:rgba(243,240,232,.92);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.nav{height:68px;display:flex;align-items:center;justify-content:space-between}.brand{font-size:25px;font-weight:850;letter-spacing:-1px}.brand small{font-size:11px;margin-left:10px;color:var(--muted)}
nav a{font-size:14px;color:var(--muted);margin-left:24px}.hero{padding:90px 0 56px}.eyebrow{font-size:12px;font-weight:800;letter-spacing:.16em;color:var(--accent)}
.hero h1{font-size:clamp(42px,7vw,82px);line-height:1.02;letter-spacing:-.055em;margin:14px 0 22px;max-width:900px}.hero p{font-size:20px;color:var(--muted);max-width:780px}
.stats{display:grid;grid-template-columns:repeat(5,1fr);border:1px solid var(--line);background:var(--paper);margin:10px 0 70px}.stat{padding:22px;border-right:1px solid var(--line)}.stat:last-child{border-right:0}.stat b{font-size:28px;display:block}.stat span{font-size:12px;color:var(--muted)}
.section{margin:0 0 74px}.section-head{display:flex;justify-content:space-between;align-items:end;border-bottom:1px solid var(--ink);padding-bottom:12px;margin-bottom:18px}.section h2{font-size:27px;margin:0}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.card,.panel{background:var(--paper);border:1px solid var(--line);padding:22px}.card{min-height:220px}.card h3{font-size:21px;line-height:1.3;margin:16px 0 9px}.card p{font-size:14px;color:var(--muted);margin:0 0 18px}.badge{display:inline-flex;border:1px solid currentColor;border-radius:999px;padding:4px 9px;font-size:11px;font-weight:800}.good{color:var(--good)}.watch{color:var(--watch)}
.score-row{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;border-top:1px solid var(--line);padding-top:14px}.score b{font-size:17px}.score span{font-size:10px;color:var(--muted);display:block}.meta{font-size:12px;color:var(--muted);margin-top:14px}
.detail-hero{padding:72px 0 34px}.detail-hero h1{font-size:clamp(38px,6vw,68px);line-height:1.05;letter-spacing:-.045em;margin:16px 0}.detail-grid{display:grid;grid-template-columns:1.7fr .8fr;gap:18px}.kv{display:grid;grid-template-columns:160px 1fr;border-top:1px solid var(--line)}.kv div{padding:11px 0;border-bottom:1px solid var(--line)}.kv div:nth-child(odd){color:var(--muted);font-size:13px}.evidence{padding:12px 0;border-bottom:1px solid var(--line)}.evidence small{display:block;color:var(--muted)}
footer{border-top:1px solid var(--line);padding:35px 0 50px;color:var(--muted);font-size:12px}
@media(max-width:800px){nav{display:none}.stats{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.detail-grid{grid-template-columns:1fr}.score-row{grid-template-columns:repeat(2,1fr)}}
`;

function esc(v: unknown): string {
  return String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c]!));
}
function n(v: unknown): string { const x=Number(v); return Number.isFinite(x)?x.toFixed(1):"0.0"; }
function i(v: unknown): string { const x=Number(v); return Number.isFinite(x)?Math.round(x).toLocaleString("en-US"):"0"; }
function money(v: unknown): string {
  const x=Number(v); if(!Number.isFinite(x)) return "—";
  if(x>=1e6) return "$"+(x/1e6).toFixed(2)+"M";
  if(x>=1e3) return "$"+(x/1e3).toFixed(1)+"K";
  return "$"+Math.round(x).toLocaleString("en-US");
}
function scores(x:any){return `<div class="score-row">
<div class="score"><b>${n(x.heat_score)}</b><span>热度</span></div>
<div class="score"><b>${n(x.content_score)}</b><span>内容</span></div>
<div class="score"><b>${n(x.build_score)}</b><span>可做</span></div>
<div class="score"><b>${n(x.business_score)}</b><span>商业</span></div></div>`;}
function shell(title:string, body:string, desc="见势：看见正在发生的生意机会。"){
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title><meta name="description" content="${esc(desc)}"><meta name="robots" content="index,follow"><style>${CSS}</style></head><body>
<header><div class="wrap nav"><a class="brand" href="./">见势 <small>JIANSHI</small></a><nav><a href="./">首页</a></nav></div></header>
${body}<footer><div class="wrap">见势｜商业机会与趋势情报。数据和评分用于研究与发现，不构成投资、收益或经营承诺。</div></footer></body></html>`;
}
async function api(view:string, slug?:string){
  const u=new URL(API);u.searchParams.set("view",view);if(slug)u.searchParams.set("slug",slug);
  const r=await fetch(u.toString(),{headers:{"User-Agent":"JianShi-Web-Fallback/0.1"}});
  if(!r.ok) throw new Error(`PUBLIC_FEED_${r.status}`);
  return await r.json();
}
function card(x:any){
  const watch=!x.public_ready;
  return `<a class="card" href="?slug=${encodeURIComponent(x.slug)}"><span class="badge ${watch?"watch":"good"}">${watch?"单源观察":"多源机会"}</span>
<h3>${esc(x.title)}</h3><p>${esc(x.thesis)}</p>${scores(x)}<div class="meta">${i(x.evidence_count)} 条证据 · ${i(x.source_count)} 类数据源 · 综合 ${n(x.overall_score)}</div></a>`;
}
async function home(){
  const d=await api("home");const s=d.stats||{};
  const opp=(d.opportunities||[]).map(card).join(""); const watch=(d.watchlist||[]).map(card).join("");
  return shell("见势｜看见正在发生的生意机会",`<main class="wrap"><section class="hero"><div class="eyebrow">BUSINESS SIGNAL INTELLIGENCE</div>
<h1>看见正在发生的<br>生意机会。</h1><p>追踪全球产品、开源项目与真实商业市场。只有通过多源共振 Gate 的条目才进入机会榜。</p></section>
<section class="stats"><div class="stat"><b>${i(s.marketplace_listings)}</b><span>商业挂牌样本</span></div><div class="stat"><b>${i(s.github_repositories)}</b><span>GitHub 趋势仓库</span></div><div class="stat"><b>${i(s.signals)}</b><span>已识别信号</span></div><div class="stat"><b>${i(s.validated_opportunities)}</b><span>多源验证机会</span></div><div class="stat"><b>${i(s.watch_opportunities)}</b><span>单源观察</span></div></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">VALIDATED</div><h2>已通过多源验证</h2></div></div><div class="grid">${opp}</div></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">WATCHLIST</div><h2>值得继续盯</h2></div></div><div class="grid">${watch}</div></section></main>`);
}
async function detail(slug:string){
  const d=await api("detail",slug);const x=d.item;const gh=d.evidence?.github||[];const mk=d.evidence?.marketplace||[];
  const ghHtml=gh.map((e:any)=>`<div class="evidence"><b>${esc(e.full_name)}</b><small>${esc(e.language||"—")} · ${i(e.stars)} Stars · 技术排名 ${n(e.rank_score)}</small></div>`).join("")||"<p>暂无 GitHub 证据。</p>";
  const mkHtml=mk.map((e:any)=>`<div class="evidence"><b>#${esc(e.listing_number)} ${esc(e.public_title)}</b><small>售价 ${money(e.listing_price)} · 月利润 ${money(e.average_monthly_net_profit)} · 利润率 ${n(e.profit_margin)}% · 每周 ${n(e.hours_worked_per_week)}h</small></div>`).join("")||"<p>暂无交易市场证据。</p>";
  return shell(`${esc(x.title)}｜见势`,`<main class="wrap"><section class="detail-hero"><span class="badge ${x.public_ready?"good":"watch"}">${x.public_ready?"多源机会":"单源观察"}</span><h1>${esc(x.title)}</h1><p>${esc(x.thesis)}</p></section>
<div class="detail-grid"><div><section class="panel"><h2>机会判断</h2>${scores(x)}<div class="kv"><div>要解决的问题</div><div>${esc(x.problem||"—")}</div><div>目标用户</div><div>${esc(x.target_customer||"—")}</div><div>商业模式</div><div>${esc(x.business_model||"—")}</div><div>中国化适配</div><div>${n(x.china_fit)}/100</div><div>一人公司适配</div><div>${n(x.solo_founder_fit)}/100</div></div></section>
<section class="panel"><h2>GitHub 技术证据</h2>${ghHtml}</section><section class="panel"><h2>真实商业市场证据</h2>${mkHtml}</section></div>
<aside><section class="panel"><h3>证据强度</h3><div class="kv"><div>数据源</div><div>${i(x.source_count)}</div><div>有效证据</div><div>${i(x.evidence_count)}</div><div>GitHub</div><div>${i(x.github_repo_count)}</div><div>商业挂牌</div><div>${i(x.market_listing_count)}</div><div>综合分</div><div>${n(x.overall_score)}</div></div></section><section class="panel"><small>${esc(d.disclosure||"")}</small></section></aside></div></main>`,x.thesis||"见势机会研究");
}

Deno.serve(async(req)=>{
  if(req.method!=="GET") return new Response("GET required",{status:405});
  try{
    const u=new URL(req.url);const slug=u.searchParams.get("slug");
    const html=slug?await detail(slug):await home();
    return new Response(html,{status:200,headers:{"content-type":"text/html; charset=utf-8","cache-control":"public, max-age=120, s-maxage=300, stale-while-revalidate=600"}});
  }catch(e){
    return new Response(shell("见势｜暂时不可用",`<main class="wrap"><section class="hero"><h1>数据暂时不可用。</h1><p>${esc(String(e))}</p></section></main>`),{status:503,headers:{"content-type":"text/html; charset=utf-8"}});
  }
});
