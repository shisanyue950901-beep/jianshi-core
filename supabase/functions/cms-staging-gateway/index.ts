// JIANSHI F2.1 G1-E: STAGING-only CMS HTTP gateway.
// Deploy ONLY to apuibjhxinumxbfnqlkp with verify_jwt=true.
// NO public client grants. NO deployment to jianshi-prod.
// All operations fail closed until independent Auth E2E and release gate.
//
// Security: trusted GoTrue getUser(token), fresh auth.sessions lookup via
// service-only RPC, server-derived actor ID, private DB invoker transactions.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.75.1";

const STAGING_REF = "apuibjhxinumxbfnqlkp";
const MAX_BODY = 12000;
const ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const TYPE = new Set([
  "SOLUTION_GUIDE", "PROJECT_RESEARCH", "COURSE", "LESSON",
  "RESOURCE", "EVENT", "CASE_STUDY",
]);
const STATES = new Set([
  "IN_REVIEW", "APPROVED", "REJECTED", "DRAFT",
  "PUBLISHED", "UNPUBLISHED",
]);
const DRAFT_KEYS = new Set(["content_key","content_type","content","sources","request_id"]);
const EDIT_KEYS = new Set([
  "content_id","expected_revision","content","sources",
  "rights_declared","facts_checked","request_id",
]);
const STATE_KEYS = new Set([
  "content_id","expected_revision","next_state","request_id","reason",
]);

function response(code: number, status: string): Response {
  return new Response(JSON.stringify({ status, code }), {
    status: code,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store, max-age=0",
      "x-content-type-options": "nosniff",
      "x-frame-options": "DENY",
      "referrer-policy": "no-referrer",
      "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
    },
  });
}
function limitedKeys(value: unknown, allowed: Set<string>): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value) &&
    Object.keys(value).every((key) => allowed.has(key));
}
function isUuid(value: unknown): value is string {
  return typeof value === "string" && ID.test(value);
}
function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}
function isPositiveInt(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 1 && value <= 1000000000;
}
function bodyValid(operation: string, body: unknown): body is Record<string, unknown> {
  if (operation === "CREATE") {
    return limitedKeys(body, DRAFT_KEYS) && isUuid(body.request_id) &&
      typeof body.content_key === "string" && body.content_key.length >= 6 &&
      body.content_key.length <= 100 && TYPE.has(String(body.content_type)) &&
      isRecord(body.content) && Array.isArray(body.sources) && body.sources.length <= 30;
  }
  if (operation === "EDIT") {
    return limitedKeys(body, EDIT_KEYS) && isUuid(body.request_id) &&
      isUuid(body.content_id) && isPositiveInt(body.expected_revision) &&
      isRecord(body.content) && Array.isArray(body.sources) && body.sources.length <= 30 &&
      typeof body.rights_declared === "boolean" && typeof body.facts_checked === "boolean";
  }
  if (operation === "STATE") {
    return limitedKeys(body, STATE_KEYS) && isUuid(body.request_id) &&
      isUuid(body.content_id) && isPositiveInt(body.expected_revision) &&
      STATES.has(String(body.next_state)) &&
      (body.reason === undefined || (typeof body.reason === "string" && body.reason.length <= 1800));
  }
  return false;
}
// Only AFTER getUser validates JWT signature and user do we trust the
// decoded session_id field (which we still cross-check against auth.sessions).
function validatedClaims(jwt: string, userId: string): string | null {
  try {
    const fragment = jwt.split(".");
    if (fragment.length !== 3 || fragment[1].length > 12000) return null;
    const b64 = fragment[1].replace(/-/g, "+").replace(/_/g, "/");
    const claims = JSON.parse(atob(b64.padEnd(Math.ceil(b64.length / 4) * 4, "=")));
    if (claims.sub !== userId || claims.role !== "authenticated" ||
        (claims.aud !== "authenticated" &&
         !(Array.isArray(claims.aud) && claims.aud.includes("authenticated"))) ||
        claims.is_anonymous === true || !isUuid(claims.session_id) ||
        !Number.isFinite(claims.exp) || claims.exp * 1000 <= Date.now() ||
        typeof claims.iss !== "string" || !claims.iss.startsWith(
          "https://" + STAGING_REF + ".supabase.co/auth/v1")) return null;
    return claims.session_id;
  } catch (_err) {
    return null;
  }
}

Deno.serve(async (req: Request): Promise<Response> => {
  try {
    // Server-to-server only: never grant cross-origin browser access.
    if (req.headers.has("origin")) return response(403, "CMS_BROWSER_ACCESS_DENIED");
    if (req.method !== "POST") return response(405, "CMS_METHOD_DENIED");
    const path = new URL(req.url).pathname;
    const operation = path.endsWith("/drafts") ? "CREATE" :
      path.endsWith("/edit") ? "EDIT" :
      path.endsWith("/review") ? "STATE" : null;
    if (!operation) return response(404, "CMS_ROUTE_NOT_FOUND");

    const url = Deno.env.get("SUPABASE_URL") || "";
    const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
    // This explicit operator-controlled gate defaults to DISABLED.
    if (url !== "https://" + STAGING_REF + ".supabase.co" ||
        !serviceKey || Deno.env.get("JIANSHI_G1E_API_GATE") !== "AUTH_E2E_APPROVED") {
      return response(503, "CMS_STAGING_LOCKED");
    }
    const admin = createClient(url, serviceKey, {
      auth: { persistSession:false, autoRefreshToken:false, detectSessionInUrl:false },
    });
    const {data: features, error: flagError} = await admin.from("product_feature_flags")
      .select("feature_key,enabled").in("feature_key",["cms_editor","account_auth"]);
    if (flagError || !features || features.length !== 2 ||
        features.some((f) => f.enabled !== true)) {
      return response(503, "CMS_WRITE_DISABLED");
    }
    const { data: ready, error: readyError } = await admin.rpc("auth_launch_ready_v01");
    if (readyError || ready !== true) return response(503, "CMS_AUTH_NOT_READY");

    const authorization = req.headers.get("authorization") || "";
    const jwt = /^Bearer ([A-Za-z0-9_.-]{20,9000})$/.exec(authorization)?.[1];
    if (!jwt) return response(401, "CMS_AUTH_REQUIRED");
    const { data: verified, error: authError } = await admin.auth.getUser(jwt);
    if (authError || !verified.user?.id) return response(401, "CMS_AUTH_INVALID");
    const userId = verified.user.id;
    const sessionId = validatedClaims(jwt,userId);
    if (!sessionId) return response(401, "CMS_SESSION_INVALID");
    const {data: active, error: sessionError} = await admin.rpc(
      "cms_internal_session_v01", {p_user_id:userId, p_session_id:sessionId});
    if (sessionError || active !== true) return response(401, "CMS_SESSION_REVOKED");

    const contentType = req.headers.get("content-type") || "";
    if (!contentType.toLowerCase().startsWith("application/json"))
      return response(415, "CMS_JSON_REQUIRED");
    if (Number(req.headers.get("content-length") || 0) > MAX_BODY)
      return response(413, "CMS_BODY_TOO_LARGE");
    const raw = await req.text();
    if (raw.length > MAX_BODY) return response(413, "CMS_BODY_TOO_LARGE");
    let payload: unknown;
    try {payload = JSON.parse(raw);} catch (_err) {
      return response(400, "CMS_INVALID_JSON");
    }
    if (!bodyValid(operation,payload))
      return response(422, "CMS_INVALID_PAYLOAD");

    // Actor comes ONLY from verified Auth, never p_actor in request JSON.
    const { data, error } = await admin.rpc("cms_internal_write_v01", {
      p_actor:userId, p_operation:operation, p_payload:payload,
    });
    if (error) {
      // Do not expose SQL text, private row contents, keys or permissions.
      if (error.code === "40001" || error.code === "23505")
        return response(409, "CMS_VERSION_OR_DUPLICATE");
      if (error.code === "42501") return response(403, "CMS_ACTION_FORBIDDEN");
      return response(422, "CMS_OPERATION_REJECTED");
    }
    return new Response(JSON.stringify({status:"OK", result:data}), {
      status:200, headers: {
        "content-type":"application/json; charset=utf-8",
        "cache-control":"no-store",
        "x-content-type-options":"nosniff",
      },
    });
  } catch (_err) {
    // No token, SQL text, private content or stack traces in response or logs.
    return response(503, "CMS_FAIL_CLOSED");
  }
});
