import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const DEFAULT_SITE_ORIGIN = "https://jianshi-bua.pages.dev";
const ALLOWED_EVENTS = new Set([
  "PAGE_VIEW",
  "OPPORTUNITY_CARD_CLICK",
  "OPPORTUNITY_DETAIL_VIEW",
  "SECOND_OPPORTUNITY_VIEW",
  "CATALOG_SEARCH",
  "CATALOG_FILTER",
  "SOURCE_OUTBOUND_CLICK",
  "ENGAGED_30S",
  "SCROLL_50",
  "SCROLL_90",
]);

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const SLUG_RE = /^[a-z0-9-]{2,80}$/;
const TOKEN_RE = /^[A-Za-z0-9._~-]{1,80}$/;
const HOST_RE = /^(?=.{1,253}$)([A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$/;

function originAllowed(origin: string | null): boolean {
  if (!origin) return false;
  const configured = Deno.env.get("JIANSHI_SITE_ORIGIN") || DEFAULT_SITE_ORIGIN;
  return origin === configured ||
    origin === "http://localhost:8000" ||
    origin === "http://127.0.0.1:8000";
}

function cors(origin: string | null): HeadersInit {
  return {
    "access-control-allow-origin": originAllowed(origin) ? String(origin) : DEFAULT_SITE_ORIGIN,
    "access-control-allow-methods": "POST,OPTIONS",
    "access-control-allow-headers": "content-type",
    "access-control-max-age": "86400",
    "vary": "Origin",
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
  };
}

function json(origin: string | null, body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: cors(origin) });
}

function cleanToken(v: unknown): string | null {
  if (typeof v !== "string") return null;
  const x = v.trim();
  return TOKEN_RE.test(x) ? x : null;
}

function cleanHost(v: unknown): string | null {
  if (typeof v !== "string") return null;
  const x = v.trim().toLowerCase().replace(/\.$/, "");
  return HOST_RE.test(x) ? x : null;
}

function cleanMetadata(eventType: string, raw: unknown): Record<string, unknown> {
  const m = raw && typeof raw === "object" && !Array.isArray(raw)
    ? raw as Record<string, unknown>
    : {};
  const out: Record<string, unknown> = {};

  if (eventType === "OPPORTUNITY_CARD_CLICK") {
    if (m.state === "validated" || m.state === "watch") out.state = m.state;
  }

  if (eventType === "CATALOG_SEARCH") {
    const ql = Number(m.query_length);
    const rc = Number(m.results_count);
    if (Number.isInteger(ql) && ql >= 0 && ql <= 200) out.query_length = ql;
    if (Number.isInteger(rc) && rc >= 0 && rc <= 5000) out.results_count = rc;
  }

  if (eventType === "CATALOG_FILTER") {
    if (["all", "validated", "watch"].includes(String(m.filter))) {
      out.filter = String(m.filter);
    }
  }

  if (eventType === "SOURCE_OUTBOUND_CLICK") {
    const host = cleanHost(m.target_host);
    if (host) out.target_host = host;
    if (["GITHUB", "MARKETPLACE", "SOURCE", "OTHER"].includes(String(m.target_kind))) {
      out.target_kind = String(m.target_kind);
    }
  }

  return out;
}

Deno.serve(async (req: Request) => {
  const origin = req.headers.get("origin");

  if (req.method === "OPTIONS") {
    if (!originAllowed(origin)) return json(origin, { error: "ORIGIN_FORBIDDEN" }, 403);
    return new Response(null, { status: 204, headers: cors(origin) });
  }

  if (req.method !== "POST") return json(origin, { error: "POST_REQUIRED" }, 405);
  if (!originAllowed(origin)) return json(origin, { error: "ORIGIN_FORBIDDEN" }, 403);

  const contentLength = Number(req.headers.get("content-length") || "0");
  if (contentLength > 8192) return json(origin, { error: "PAYLOAD_TOO_LARGE" }, 413);

  const text = await req.text();
  if (!text || text.length > 8192) return json(origin, { error: "INVALID_PAYLOAD" }, 400);

  let body: Record<string, unknown>;
  try {
    body = JSON.parse(text);
  } catch {
    return json(origin, { error: "INVALID_JSON" }, 400);
  }

  const eventId = String(body.event_id || "");
  const visitorId = String(body.visitor_id || "");
  const sessionId = String(body.session_id || "");
  const eventType = String(body.event_type || "");
  const pagePath = String(body.page_path || "");
  const opportunitySlug = body.opportunity_slug == null ? null : String(body.opportunity_slug);
  const deviceClass = ["MOBILE", "TABLET", "DESKTOP", "UNKNOWN"].includes(String(body.device_class))
    ? String(body.device_class)
    : "UNKNOWN";

  if (!UUID_RE.test(eventId) || !UUID_RE.test(visitorId) || !UUID_RE.test(sessionId)) {
    return json(origin, { error: "INVALID_IDENTIFIER" }, 400);
  }
  if (!ALLOWED_EVENTS.has(eventType)) return json(origin, { error: "INVALID_EVENT_TYPE" }, 400);
  if (!pagePath.startsWith("/") || pagePath.length > 200) {
    return json(origin, { error: "INVALID_PAGE_PATH" }, 400);
  }
  if (opportunitySlug !== null && !SLUG_RE.test(opportunitySlug)) {
    return json(origin, { error: "INVALID_OPPORTUNITY_SLUG" }, 400);
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!supabaseUrl || !serviceKey) {
    return json(origin, { error: "SERVER_CONFIG_MISSING" }, 500);
  }

  const admin = createClient(supabaseUrl, serviceKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const { data, error } = await admin.rpc("record_behavior_event_v01", {
    p_event_id: eventId,
    p_visitor_id: visitorId,
    p_session_id: sessionId,
    p_event_type: eventType,
    p_page_path: pagePath,
    p_opportunity_slug: opportunitySlug,
    p_referrer_domain: cleanHost(body.referrer_domain),
    p_utm_source: cleanToken(body.utm_source),
    p_utm_medium: cleanToken(body.utm_medium),
    p_utm_campaign: cleanToken(body.utm_campaign),
    p_device_class: deviceClass,
    p_metadata: cleanMetadata(eventType, body.metadata),
  });

  if (error) {
    console.error("behavior-track insert failed", error.code);
    return json(origin, { error: "TRACKING_WRITE_FAILED" }, 500);
  }

  if (data === "RATE_LIMITED") {
    return json(origin, { ok: false, state: "RATE_LIMITED" }, 429);
  }

  return json(origin, { ok: true, state: data || "RECORDED" }, 200);
});
