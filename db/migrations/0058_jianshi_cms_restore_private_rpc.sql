-- F2.1 G2-G / STAGING ONLY / additive trusted RPC facade.
-- A trusted Edge handler verifies GoTrue JWT + unrevoked session BEFORE this.
-- The actor UUID is derived on server; browser cannot set or override it.
-- Preserve all Auth launch and CMS feature gates in the underlying function.
-- No schema or table grants to browser roles. Do not deploy to Production.
CREATE OR REPLACE FUNCTION public.cms_internal_restore_v01(
  p_actor uuid,
  p_payload jsonb
) RETURNS jsonb
LANGUAGE plpgsql SECURITY INVOKER
SET search_path=''
AS $$
DECLARE
  v_new integer;
  v_allowed text[] := ARRAY[
    'content_id','expected_revision','source_revision','request_id'
  ];
BEGIN
  -- Read/write-gate FIRST; neither unauthenticated nor disabled requests
  -- should get private row-existence or metadata oracle results.
  PERFORM jianshi_cms.ensure_write_gate(p_actor,ARRAY['EDITOR']);
  IF p_payload IS NULL OR jsonb_typeof(p_payload)<>'object'
    OR (SELECT count(*) FROM jsonb_object_keys(p_payload) AS k(key)
          WHERE NOT (k.key=ANY(v_allowed)))>0
    OR NOT (p_payload ?& v_allowed)
    OR coalesce(p_payload->>'content_id','') !~
          '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$'
    OR coalesce(p_payload->>'request_id','') !~
          '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$'
    OR jsonb_typeof(p_payload->'expected_revision')<>'number'
    OR jsonb_typeof(p_payload->'source_revision')<>'number'
    OR coalesce(p_payload->>'expected_revision','') !~ '^[0-9]{1,9}$'
    OR coalesce(p_payload->>'source_revision','') !~ '^[0-9]{1,9}$'
  THEN
    RAISE EXCEPTION 'CMS_INVALID_RESTORE_PAYLOAD' USING errcode='22023';
  END IF;

  -- Existing 0057 kernel still locks current row FOR UPDATE, checks owner,
  -- optimistic revision and request idempotency, and clears attestations.
  v_new:=jianshi_cms.restore_draft_revision(
    p_actor,
    (p_payload->>'content_id')::uuid,
    (p_payload->>'expected_revision')::integer,
    (p_payload->>'source_revision')::integer,
    (p_payload->>'request_id')::uuid
  );
  RETURN jsonb_build_object('revision',v_new);
END;
$$;

REVOKE ALL ON FUNCTION public.cms_internal_restore_v01(uuid,jsonb)
 FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.cms_internal_restore_v01(uuid,jsonb)
 TO service_role;
COMMENT ON FUNCTION public.cms_internal_restore_v01(uuid,jsonb) IS
 'G2-G Staging-only service RPC: restore OLD draft into NEW unapproved version. No browser role permission; feature/Auth gate and verified Edge JWT required.';
