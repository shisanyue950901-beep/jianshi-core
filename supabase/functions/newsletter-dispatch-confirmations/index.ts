import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
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
  if (req.method !== "POST") return json({ ok: false, error: "POST_REQUIRED" }, 405);

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!supabaseUrl || !serviceKey) return json({ ok: false, error: "SERVER_CONFIG_MISSING" }, 500);

  const db = createClient(supabaseUrl, serviceKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const body = await req.json().catch(() => ({}));
  const limit = Math.max(1, Math.min(50, Number(body.limit ?? 20)));

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

  const { data: rows, error: rowsError } = await db
    .from("newsletter_subscribers")
    .select("id,email")
    .eq("status", "WAITLIST")
    .order("consent_at", { ascending: true })
    .limit(limit);

  if (rowsError) return json({ ok: false, error: "WAITLIST_QUERY_FAILED" }, 500);

  let prepared = 0;
  let queued = 0;
  let reverted = 0;
  let errors = 0;

  for (const row of rows ?? []) {
    const confirmToken = randomToken();
    const confirmHash = await sha256Hex(confirmToken);

    const { data: didPrepare, error: prepareError } = await db.rpc(
      "prepare_waitlist_confirmation_v01",
      {
        p_subscriber_id: row.id,
        p_confirmation_token_hash: confirmHash,
      },
    );

    if (prepareError || didPrepare !== true) {
      errors += 1;
      continue;
    }
    prepared += 1;

    const { data: sendState, error: sendError } = await db.rpc(
      "queue_newsletter_confirmation_v02",
      {
        p_subscriber_id: row.id,
        p_email: row.email,
        p_confirm_token: confirmToken,
      },
    );

    if (sendError || sendState?.sent !== true) {
      const { data: didRevert } = await db.rpc(
        "revert_pending_confirmation_to_waitlist_v01",
        {
          p_subscriber_id: row.id,
          p_confirmation_token_hash: confirmHash,
        },
      );
      if (didRevert === true) reverted += 1;
      errors += 1;
      continue;
    }

    queued += 1;
  }

  return json({
    ok: errors === 0,
    launch_ready: true,
    selected: rows?.length ?? 0,
    prepared,
    queued,
    reverted,
    errors,
  }, errors === 0 ? 200 : 207);
});
