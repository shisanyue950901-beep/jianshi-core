-- JIANSHI F2.1 G2-H.4 / STAGING ONLY. Additive private durable CMS sessions.
-- No production installation, browser grants, login endpoints, tokens or accounts.
-- All test identities/keys are SYNTHETIC and used ONLY in disposable Postgres.
-- The caller (future trusted BFF) must verify GoTrue user+JWT before ISSUE;
-- this schema is NOT by itself authentication or a public CMS launch.
CREATE TABLE IF NOT EXISTS jianshi_cms.bff_sessions (
  cookie_digest text PRIMARY KEY
    CHECK (cookie_digest ~ '^[a-f0-9]{64}$'),
  actor_user_id uuid NOT NULL REFERENCES auth.users(id),
  auth_session_id uuid NOT NULL,
  encrypted_jwt text NOT NULL
    CHECK (length(encrypted_jwt) BETWEEN 24 AND 9000),
  encryption_key_id text NOT NULL
    CHECK (encryption_key_id ~ '^[a-zA-Z0-9_-]{1,32}$'),
  csrf_digest text NOT NULL
    CHECK (csrf_digest ~ '^[a-f0-9]{64}$'),
  issued_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  rate_window_at timestamptz NOT NULL DEFAULT now(),
  write_count integer NOT NULL DEFAULT 0
    CHECK (write_count >= 0 AND write_count <= 8),
  CHECK (expires_at > issued_at),
  CHECK (expires_at <= issued_at + interval '15 minutes')
);
ALTER TABLE jianshi_cms.bff_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE jianshi_cms.bff_sessions FORCE ROW LEVEL SECURITY;
REVOKE ALL ON jianshi_cms.bff_sessions FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON jianshi_cms.bff_sessions TO service_role;
CREATE INDEX IF NOT EXISTS bff_sessions_expiry_idx
  ON jianshi_cms.bff_sessions (expires_at);

-- All functions are INVOKER; browser roles have neither USAGE nor EXECUTE.
CREATE OR REPLACE FUNCTION jianshi_cms.bff_issue_session(
  p_actor uuid, p_auth_session uuid, p_cookie_digest text,
  p_encrypted_jwt text, p_key_id text, p_csrf_digest text,
  p_expires_at timestamptz
) RETURNS boolean
LANGUAGE plpgsql SECURITY INVOKER SET search_path = ''
AS $$
BEGIN
  -- Current authenticated editor role + ALL Auth launch gates are required.
  PERFORM jianshi_cms.ensure_write_gate(
    p_actor, ARRAY['EDITOR','REVIEWER','PUBLISHER']::text[]);
  IF p_auth_session IS NULL
     OR NOT jianshi_cms.session_is_active(p_actor,p_auth_session) THEN
    RAISE EXCEPTION 'CMS_SESSION_REVOKED' USING errcode='42501';
  END IF;
  IF p_cookie_digest IS NULL OR p_cookie_digest !~ '^[a-f0-9]{64}$'
    OR p_csrf_digest IS NULL OR p_csrf_digest !~ '^[a-f0-9]{64}$'
    OR p_encrypted_jwt IS NULL
    OR length(p_encrypted_jwt) NOT BETWEEN 24 AND 9000
    OR p_key_id IS NULL OR p_key_id !~ '^[a-zA-Z0-9_-]{1,32}$'
    OR p_expires_at IS NULL OR p_expires_at <= now()
    OR p_expires_at > now() + interval '15 minutes' THEN
    RAISE EXCEPTION 'CMS_SESSION_INPUT_INVALID' USING errcode='22023';
  END IF;
  INSERT INTO jianshi_cms.bff_sessions
    (cookie_digest, actor_user_id, auth_session_id, encrypted_jwt,
     encryption_key_id, csrf_digest, expires_at)
    VALUES (p_cookie_digest,p_actor,p_auth_session,p_encrypted_jwt,
            p_key_id,p_csrf_digest,p_expires_at);
  RETURN true;
END;
$$;

CREATE OR REPLACE FUNCTION jianshi_cms.bff_consume_session(
  p_cookie_digest text, p_is_write boolean, p_csrf_digest text DEFAULT NULL
) RETURNS jsonb
LANGUAGE plpgsql SECURITY INVOKER SET search_path = ''
AS $$
DECLARE
  v jianshi_cms.bff_sessions%rowtype;
  v_window timestamptz;
BEGIN
  IF current_user <> 'service_role' THEN
    RAISE EXCEPTION 'CMS_TRUSTED_SERVER_ONLY' USING errcode='42501';
  END IF;
  IF p_cookie_digest IS NULL OR p_cookie_digest !~ '^[a-f0-9]{64}$'
     OR p_is_write IS NULL THEN
    RAISE EXCEPTION 'CMS_SESSION_INPUT_INVALID' USING errcode='22023';
  END IF;
  -- A real row lock across all BFF instances, not per-Node process memory.
  SELECT * INTO v FROM jianshi_cms.bff_sessions
    WHERE cookie_digest=p_cookie_digest FOR UPDATE;
  IF NOT FOUND OR v.revoked_at IS NOT NULL OR v.expires_at <= now() THEN
    RAISE EXCEPTION 'CMS_SESSION_INVALID' USING errcode='28000';
  END IF;
  -- Every request rechecks the DB's actual Auth session AND live CMS role gate.
  IF NOT jianshi_cms.session_is_active(v.actor_user_id,v.auth_session_id) THEN
    RAISE EXCEPTION 'CMS_SESSION_REVOKED' USING errcode='42501';
  END IF;
  PERFORM jianshi_cms.ensure_write_gate(
    v.actor_user_id, ARRAY['EDITOR','REVIEWER','PUBLISHER']::text[]);
  IF p_is_write THEN
    IF p_csrf_digest IS NULL OR p_csrf_digest <> v.csrf_digest THEN
      RAISE EXCEPTION 'CMS_CSRF_DENIED' USING errcode='42501';
    END IF;
    v_window := v.rate_window_at;
    IF v_window <= now() - interval '1 minute' THEN
      v.write_count := 0;
      v_window := now();
    END IF;
    IF v.write_count >= 8 THEN
      -- Do NOT RAISE after a counter update: PostgreSQL would roll it back.
      RETURN jsonb_build_object('allowed',false,'status','CMS_RATE_LIMITED');
    END IF;
    UPDATE jianshi_cms.bff_sessions
      SET write_count=v.write_count+1, rate_window_at=v_window
      WHERE cookie_digest=p_cookie_digest;
  END IF;
  -- Opaque encrypted envelope ONLY to service_role. No plaintext JWT/PII
  -- is ever stored or returned by the database. Decryption happens in BFF.
  RETURN jsonb_build_object(
    'allowed',true,'user_id',v.actor_user_id,
    'auth_session_id',v.auth_session_id,
    'encrypted_jwt',v.encrypted_jwt,
    'encryption_key_id',v.encryption_key_id,
    'csrf_digest',v.csrf_digest,
    'expires_at',v.expires_at);
END;
$$;

-- Emergency revocation works even if CMS feature flags were disabled.
-- This must not reveal whether a cookie exists to a browser caller.
CREATE OR REPLACE FUNCTION jianshi_cms.bff_revoke_session(
  p_cookie_digest text
) RETURNS boolean
LANGUAGE plpgsql SECURITY INVOKER SET search_path = ''
AS $$
BEGIN
  IF current_user <> 'service_role' THEN
    RAISE EXCEPTION 'CMS_TRUSTED_SERVER_ONLY' USING errcode='42501';
  END IF;
  IF p_cookie_digest IS NULL OR p_cookie_digest !~ '^[a-f0-9]{64}$' THEN
    RAISE EXCEPTION 'CMS_SESSION_INPUT_INVALID' USING errcode='22023';
  END IF;
  UPDATE jianshi_cms.bff_sessions SET revoked_at=now()
    WHERE cookie_digest=p_cookie_digest AND revoked_at IS NULL;
  RETURN true;
END;
$$;

REVOKE ALL ON FUNCTION jianshi_cms.bff_issue_session(
  uuid,uuid,text,text,text,text,timestamptz) FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION jianshi_cms.bff_consume_session(
  text,boolean,text) FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION jianshi_cms.bff_revoke_session(
  text) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION jianshi_cms.bff_issue_session(
  uuid,uuid,text,text,text,text,timestamptz) TO service_role;
GRANT EXECUTE ON FUNCTION jianshi_cms.bff_consume_session(
  text,boolean,text) TO service_role;
GRANT EXECUTE ON FUNCTION jianshi_cms.bff_revoke_session(
  text) TO service_role;

COMMENT ON TABLE jianshi_cms.bff_sessions IS
  'STAGING ONLY private hashed-cookie session storage, AES-GCM envelope encrypted in trusted BFF, 15m TTL, locked atomic write quotas. No real sessions until security approval.';
