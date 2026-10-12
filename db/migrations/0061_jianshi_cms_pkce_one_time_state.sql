-- JIANSHI F2.1 G2-H.6: PRIVATE STAGING-ONLY pending PKCE login challenges.
-- No browser access; no real Auth launch; no email address or raw OAuth verifier.
-- HTTPS controller stores only HMAC digests and AES-GCM verifier envelope.
CREATE TABLE IF NOT EXISTS jianshi_cms.bff_pkce_challenges (
  state_digest text PRIMARY KEY CHECK (state_digest ~ '^[a-f0-9]{64}$'),
  cookie_digest text NOT NULL CHECK (cookie_digest ~ '^[a-f0-9]{64}$'),
  encrypted_verifier text NOT NULL CHECK (length(encrypted_verifier) BETWEEN 60 AND 400),
  issued_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  consumed_at timestamptz,
  CHECK (expires_at>issued_at),
  CHECK (expires_at<=issued_at+interval '5 minutes')
);
ALTER TABLE jianshi_cms.bff_pkce_challenges ENABLE ROW LEVEL SECURITY;
ALTER TABLE jianshi_cms.bff_pkce_challenges FORCE ROW LEVEL SECURITY;
REVOKE ALL ON jianshi_cms.bff_pkce_challenges FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT,UPDATE ON jianshi_cms.bff_pkce_challenges TO service_role;
CREATE INDEX IF NOT EXISTS bff_pkce_expiry_idx ON jianshi_cms.bff_pkce_challenges (expires_at);

CREATE OR REPLACE FUNCTION jianshi_cms.bff_pkce_gate_v01()
RETURNS boolean LANGUAGE plpgsql SECURITY INVOKER SET search_path=''
AS $$
BEGIN
  IF current_user <> 'service_role' THEN
    RAISE EXCEPTION 'CMS_TRUSTED_SERVER_ONLY' USING errcode='42501';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.product_feature_flags WHERE feature_key='account_auth' AND enabled=true
  ) OR NOT EXISTS (
    SELECT 1 FROM public.product_feature_flags WHERE feature_key='cms_editor' AND enabled=true
  ) THEN
    RAISE EXCEPTION 'CMS_WRITE_DISABLED' USING errcode='42501';
  END IF;
  IF public.auth_launch_ready_v01() IS DISTINCT FROM true THEN
    RAISE EXCEPTION 'CMS_AUTH_NOT_READY' USING errcode='42501';
  END IF;
  RETURN true;
END;
$$;

CREATE OR REPLACE FUNCTION jianshi_cms.bff_issue_pkce_v01(
  p_state_digest text,p_cookie_digest text,p_encrypted_verifier text,p_expires_at timestamptz
) RETURNS boolean LANGUAGE plpgsql SECURITY INVOKER SET search_path=''
AS $$
BEGIN
  PERFORM jianshi_cms.bff_pkce_gate_v01();
  IF p_state_digest IS NULL OR p_state_digest !~ '^[a-f0-9]{64}$'
    OR p_cookie_digest IS NULL OR p_cookie_digest !~ '^[a-f0-9]{64}$'
    OR p_encrypted_verifier IS NULL OR length(p_encrypted_verifier) NOT BETWEEN 60 AND 400
    OR p_encrypted_verifier NOT LIKE 'v1.%'
    OR p_expires_at IS NULL OR p_expires_at<=now()
    OR p_expires_at>now()+interval '5 minutes' THEN
    RAISE EXCEPTION 'CMS_PKCE_INPUT_INVALID' USING errcode='22023';
  END IF;
  INSERT INTO jianshi_cms.bff_pkce_challenges(
    state_digest,cookie_digest,encrypted_verifier,expires_at
  ) VALUES(p_state_digest,p_cookie_digest,p_encrypted_verifier,p_expires_at);
  RETURN true;
END;
$$;

CREATE OR REPLACE FUNCTION jianshi_cms.bff_consume_pkce_v01(
  p_state_digest text,p_cookie_digest text
) RETURNS jsonb LANGUAGE plpgsql SECURITY INVOKER SET search_path=''
AS $$
DECLARE
  envelope text;
BEGIN
  PERFORM jianshi_cms.bff_pkce_gate_v01();
  IF p_state_digest IS NULL OR p_state_digest !~ '^[a-f0-9]{64}$'
    OR p_cookie_digest IS NULL OR p_cookie_digest !~ '^[a-f0-9]{64}$' THEN
    RAISE EXCEPTION 'CMS_PKCE_INPUT_INVALID' USING errcode='22023';
  END IF;
  -- Single conditional SQL UPDATE atomically consumes the challenge across
  -- multiple PostgreSQL connections. An invalid cookie NEVER burns a valid state.
  UPDATE jianshi_cms.bff_pkce_challenges
    SET consumed_at=now()
    WHERE state_digest=p_state_digest
      AND cookie_digest=p_cookie_digest
      AND consumed_at IS NULL AND expires_at>now()
    RETURNING encrypted_verifier INTO envelope;
  IF NOT FOUND THEN
    RETURN jsonb_build_object('used',false);
  END IF;
  RETURN jsonb_build_object('used',true,'encryptedVerifier',envelope);
END;
$$;
REVOKE ALL ON FUNCTION jianshi_cms.bff_pkce_gate_v01() FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION jianshi_cms.bff_issue_pkce_v01(text,text,text,timestamptz) FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION jianshi_cms.bff_consume_pkce_v01(text,text) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION jianshi_cms.bff_pkce_gate_v01() TO service_role;
GRANT EXECUTE ON FUNCTION jianshi_cms.bff_issue_pkce_v01(text,text,text,timestamptz) TO service_role;
GRANT EXECUTE ON FUNCTION jianshi_cms.bff_consume_pkce_v01(text,text) TO service_role;
COMMENT ON TABLE jianshi_cms.bff_pkce_challenges IS
  'Private non-public one-time PKCE state, HMAC cookie binding, encrypted verifier, five minute expiry. No real account launch.';
