import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const SITE = "https://jianshi-bua.pages.dev";

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

function esc(v: unknown): string {
  return String(v ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function score(v: unknown): string {
  const n = Number(v);
  return Number.isFinite(n) ? n.toFixed(1) : "—";
}

function buildHtml(items: any[], sendDate: string, unsubscribeUrl: string): string {
  const rows = items.map((x, i) => {
    const state = x.public_ready ? "已验证" : "持续观察";
    const change = x.change_summary_zh || "继续积累证据。";
    return `<div style="padding:18px 0;border-bottom:1px solid #e8e6df">
      <div style="font-size:12px;color:#8b4b35;margin-bottom:5px">#${i + 1} · ${esc(state)}</div>
      <a href="${SITE}/opportunity/${encodeURIComponent(String(x.slug))}/" style="font-size:18px;font-weight:700;color:#171714;text-decoration:none">${esc(x.title)}</a>
      <p style="margin:7px 0;color:#666;line-height:1.6">${esc(change)}</p>
      <div style="font-size:12px;color:#777">综合 ${score(x.overall_score)} · 趋势 ${score(x.heat_score)} · 值得做 ${score(x.build_score)} · 商业 ${score(x.business_score)}</div>
    </div>`;
  }).join("");

  return `<!doctype html><html><body style="margin:0;background:#f5f3ed;color:#171714">
    <div style="max-width:660px;margin:auto;padding:28px 20px;font-family:Arial,'Microsoft YaHei',sans-serif">
      <div style="font-size:13px;font-weight:800;letter-spacing:.08em">见势 JIANSHI</div>
      <h1 style="font-size:30px;margin:10px 0 8px">今日 Top 10 商业机会</h1>
      <p style="color:#666;margin:0 0 22px">${esc(sendDate)} · 从技术趋势、真实商业样本和历史变化中筛选。</p>
      <div style="background:white;padding:4px 22px 8px;border:1px solid #dedbd2">${rows}</div>
      <p style="margin:22px 0"><a href="${SITE}/today/" style="color:#171714;font-weight:700">查看完整今日机会 →</a></p>
      <p style="font-size:11px;color:#8a887f;line-height:1.6">见势的数据和评分用于研究与发现，不构成投资、收益或经营承诺。你收到这封邮件，是因为你主动订阅并完成了邮箱确认。</p>
      <p style="font-size:11px"><a href="${esc(unsubscribeUrl)}" style="color:#777">退订每日机会</a> · <a href="${SITE}/privacy/" style="color:#777">隐私说明</a></p>
    </div>
  </body></html>`;
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return json({ ok: false, error: "POST_REQUIRED" }, 405);

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!supabaseUrl || !serviceKey) return json({ ok: false, error: "SERVER_CONFIG_MISSING" }, 500);

  const db = createClient(supabaseUrl, serviceKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const body = await req.json().catch(() => ({}));
  const subscriberLimit = Math.max(1, Math.min(500, Number(body.subscriber_limit ?? 100)));

  const { data: ready, error: readyError } = await db.rpc("newsletter_launch_ready_v01");
  if (readyError) return json({ ok: false, error: "PROVIDER_STATE_FAILED" }, 500);
  if (ready !== true) {
    return json({
      ok: true,
      launch_ready: false,
      queued: 0,
      message: "NEWSLETTER_LAUNCH_GATE_CLOSED",
    });
  }

  const { data: items, error: itemsError } = await db
    .from("public_daily_brief_v01")
    .select("slug,title,snapshot_date,public_ready,change_summary_zh,overall_score,heat_score,build_score,business_score,overall_rank")
    .order("overall_rank", { ascending: true })
    .limit(10);

  if (itemsError) return json({ ok: false, error: "DAILY_BRIEF_QUERY_FAILED" }, 500);
  if (!items?.length) return json({ ok: false, error: "DAILY_BRIEF_EMPTY" }, 503);

  const sendDate = String(items[0].snapshot_date);
  const subject = `见势每日 Top 10｜${sendDate}｜今天值得关注的商业机会`;

  const { data: subscribers, error: subscribersError } = await db
    .from("newsletter_subscribers")
    .select("id,email")
    .eq("status", "ACTIVE")
    .order("confirmed_at", { ascending: true })
    .limit(subscriberLimit);

  if (subscribersError) return json({ ok: false, error: "ACTIVE_SUBSCRIBER_QUERY_FAILED" }, 500);

  let queued = 0;
  let alreadyProcessed = 0;
  let errors = 0;

  for (const subscriber of subscribers ?? []) {
    const { data: unsubscribeToken, error: tokenError } = await db.rpc(
      "newsletter_unsubscribe_token_v01",
      { p_subscriber_id: subscriber.id },
    );
    if (tokenError || !unsubscribeToken) {
      errors += 1;
      continue;
    }

    const unsubscribeUrl =
      `${supabaseUrl}/functions/v1/newsletter-subscribe?mode=unsubscribe&token=${encodeURIComponent(String(unsubscribeToken))}`;
    const html = buildHtml(items, sendDate, unsubscribeUrl);

    const { data: sendState, error: sendError } = await db.rpc(
      "queue_newsletter_daily_v01",
      {
        p_subscriber_id: subscriber.id,
        p_email: subscriber.email,
        p_send_date: sendDate,
        p_subject: subject,
        p_html: html,
      },
    );

    if (sendError) {
      errors += 1;
      continue;
    }
    if (sendState?.sent === true) queued += 1;
    else if (sendState?.reason === "ALREADY_PROCESSED") alreadyProcessed += 1;
    else errors += 1;
  }

  return json({
    ok: errors === 0,
    launch_ready: true,
    send_date: sendDate,
    top_items: items.length,
    active_selected: subscribers?.length ?? 0,
    queued,
    already_processed: alreadyProcessed,
    errors,
  }, errors === 0 ? 200 : 207);
});
