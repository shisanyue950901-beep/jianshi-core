import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const SITE_URL = "https://jianshi-bua.pages.dev";
const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET,POST,OPTIONS",
  "access-control-allow-headers": "content-type",
  "content-type": "application/json; charset=utf-8",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: CORS });
}

function redirect(state: string) {
  return Response.redirect(`${SITE_URL}/?newsletter=${encodeURIComponent(state)}#subscribe`, 302);
}

function normalizeEmail(value: unknown): string {
  return String(value ?? "").trim().toLowerCase();
}

function validEmail(email: string): boolean {
  if (email.length < 3 || email.length > 254) return false;
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function randomToken(bytes = 32): string {
  const raw = new Uint8Array(bytes);
  crypto.getRandomValues(raw);
  return btoa(String.fromCharCode(...raw))
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replaceAll("=", "");
}

async function sha256Hex(input: string): Promise<string> {
  const bytes = new TextEncoder().encode(input);
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
  return [...digest].map((b) => b.toString(16).padStart(2, "0")).join("");
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: CORS });
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!supabaseUrl || !serviceKey) return json({ ok: false, error: "SERVER_CONFIG_MISSING" }, 500);

  const db = createClient(supabaseUrl, serviceKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const url = new URL(req.url);

  if (req.method === "GET") {
    const mode = url.searchParams.get("mode");
    const token = String(url.searchParams.get("token") ?? "");
    if (!["confirm", "unsubscribe"].includes(String(mode)) || token.length < 20 || token.length > 256) {
      return redirect("invalid");
    }

    const hash = await sha256Hex(token);
    if (mode === "confirm") {
      const { data, error } = await db.rpc("confirm_newsletter_subscription_v01", {
        p_token_hash: hash,
      });
      if (error) return redirect("error");
      return redirect(data === true ? "confirmed" : "invalid");
    }

    const { data, error } = await db.rpc("unsubscribe_newsletter_v01", {
      p_token_hash: hash,
    });
    if (error) return redirect("error");
    return redirect(data === true ? "unsubscribed" : "invalid");
  }

  if (req.method !== "POST") return json({ ok: false, error: "POST_REQUIRED" }, 405);

  let body: any;
  try {
    body = await req.json();
  } catch {
    return json({ ok: false, error: "INVALID_JSON" }, 400);
  }

  // Honeypot: real users never fill this invisible field.
  if (String(body?.company ?? "").trim()) {
    return json({
      ok: true,
      state: "PENDING",
      message: "订阅请求已记录。",
    }, 202);
  }

  const email = normalizeEmail(body?.email);
  if (!validEmail(email)) {
    return json({ ok: false, error: "INVALID_EMAIL", message: "请输入有效邮箱地址。" }, 400);
  }

  const sourcePath = String(body?.source_path ?? "/").slice(0, 200);
  const confirmToken = randomToken();
  const unsubscribeToken = randomToken();
  const confirmHash = await sha256Hex(confirmToken);
  const unsubscribeHash = await sha256Hex(unsubscribeToken);

  const { data: requestState, error: requestError } = await db.rpc(
    "request_newsletter_subscription_v01",
    {
      p_email: email,
      p_source_path: sourcePath,
      p_confirmation_token_hash: confirmHash,
      p_unsubscribe_token_hash: unsubscribeHash,
    },
  );

  if (requestError) {
    return json({ ok: false, error: "SUBSCRIPTION_FAILED", message: "暂时无法提交，请稍后再试。" }, 500);
  }

  if (requestState?.status === "ACTIVE") {
    return json({
      ok: true,
      state: "ACTIVE",
      message: "这个邮箱已经完成订阅，无需重复提交。",
    });
  }

  if (requestState?.should_send !== true) {
    return json({
      ok: true,
      state: "PENDING_CONFIRMATION",
      message: "订阅请求已记录。若确认邮件已启用，请检查邮箱。",
    }, 202);
  }

  const { data: providerState, error: providerError } = await db.rpc(
    "queue_newsletter_confirmation_v01",
    {
      p_subscriber_id: requestState.subscriber_id,
      p_email: email,
      p_confirm_token: confirmToken,
      p_unsubscribe_token: unsubscribeToken,
    },
  );

  if (providerError || providerState?.sent !== true) {
    return json({
      ok: true,
      state: "WAITLIST",
      message: "已记录订阅意向。邮件确认通道正在启用，启用后会先向你发送确认邮件。",
    }, 202);
  }

  return json({
    ok: true,
    state: "CONFIRMATION_QUEUED",
    message: "确认邮件已进入发送队列，请稍后检查邮箱并完成确认。",
  }, 202);
});
