-- F2.1 G2-H.7B: isolated server-side email token_hash state; NOT PKCE verifier.
-- Additive only. Never apply to Production. Staging flags MUST stay disabled.
-- The token_hash is NOT stored; a signed+encrypted temporary browser intent
-- (not this table) preserves it until the user explicitly confirms a POST.
CREATE TABLE IF NOT EXISTS jianshi_cms.bff_email_challenges (
  state_digest text PRIMARY KEY CHECK (state_digest ~ '^[a-f0-9]{64}$'),
  cookie_digest text NOT NULL CHECK (cookie_digest ~ '^[a-f0-9]{64}$'),
  issued_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  consumed_at timestamptz,
  CHECK (expires_at > issued_at),
  CHECK (expires_at <= issued_at + interval '5 minutes')
);
ALTER TABLE jianshi_cms.bff_email_challenges ENABLE ROW LEVEL SECURITY;
ALTER TABLE jianshi_cms.bff_email_challenges FORCE ROW LEVEL SECURITY;
REVOKE ALL ON jianshi_cms.bff_email_challenges FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT,UPDATE ON jianshi_cms.bff_email_challenges TO service_role;
CREATE INDEX IF NOT EXISTS bff_email_expiry_idx ON jianshi_cms.bff_email_challenges(expires_at);

CREATE OR REPLACE FUNCTION jianshi_cms.bff_issue_email_state_v01(
  p_state_digest text,p_cookie_digest text,p_expires_at timestamptz
) RETURNS boolean LANGUAGE plpgsql SECURITY INVOKER SET search_path=''
AS $$
BEGIN
  -- Requires service_role + account_auth/cms_editor + all eight Auth launch gates.
  PERFORM jianshi_cms.bff_pkce_gate_v01();
  IF p_state_digest IS NULL OR p_state_digest !~ '^[a-f0-9]{64}$'
    OR p_cookie_digest IS NULL OR p_cookie_digest !~ '^[a-f0-9]{64}$'
    OR p_expires_at IS NULL OR p_expires_at <= now()
    OR p_expires_at > now()+interval '5 minutes' THEN
    RAISE EXCEPTION 'CMS_EMAIL_STATE_INVALID' USING errcode='22023';
  END IF;
  INSERT INTO jianshi_cms.bff_email_challenges(state_digest,cookie_digest,expires_at)
    VALUES(p_state_digest,p_cookie_digest,p_expires_at);
  RETURN true;
END;
$$;

CREATE OR REPLACE FUNCTION jianshi_cms.bff_consume_email_state_v01(
  p_state_digest text,p_cookie_digest text
) RETURNS jsonb LANGUAGE plpgsql SECURITY INVOKER SET search_path=''
AS $$
DECLARE
  consumed text;
BEGIN
  PERFORM jianshi_cms.bff_pkce_gate_v01();
  IF p_state_digest IS NULL OR p_state_digest !~ '^[a-f0-9]{64}$'
    OR p_cookie_digest IS NULL OR p_cookie_digest !~ '^[a-f0-9]{64}$' THEN
    RAISE EXCEPTION 'CMS_EMAIL_STATE_INVALID' USING errcode='22023';
  END IF;
  -- Atomic conditional UPDATE: across instances exactly one can exchange OTP.
  -- A wrong cookie, expired state or replay NEVER consumes a valid challenge.
  UPDATE jianshi_cms.bff_email_challenges
    SET consumed_at=now()
    WHERE state_digest=p_state_digest AND cookie_digest=p_cookie_digest
      AND consumed_at IS NULL AND expires_at>now()
    RETURNING state_digest INTO consumed;
  RETURN jsonb_build_object('used',consumed IS NOT NULL);
END;
$$;
REVOKE ALL ON FUNCTION jianshi_cms.bff_issue_email_state_v01(text,text,timestamptz)
  FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION jianshi_cms.bff_consume_email_state_v01(text,text)
  FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION jianshi_cms.bff_issue_email_state_v01(text,text,timestamptz)
  TO service_role;
GRANT EXECUTE ON FUNCTION jianshi_cms.bff_consume_email_state_v01(text,text)
  TO service_role;
COMMENT ON TABLE jianshi_cms.bff_email_challenges IS
  'Private 5-minute HMAC browser state for token_hash email confirmation; no token, email or verifier stored.';
