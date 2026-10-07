-- P4.1.2 Stack Exchange demand-signal queries.
-- Uses official Stack Exchange API counts only; no question body/title/user data.
-- Shadow-only: does not alter OPP_V0.2 or public_ready.

insert into external_signal_queries(
  source_id,code,query_type,query_spec,evidence_type,enabled,notes
)
select ds.id,x.code,'STACKEXCHANGE_TAG_COUNT',
       jsonb_build_object(
         'site','stackoverflow',
         'tag',x.tag,
         'windows_days',jsonb_build_array(7,30)
       ),
       'STACKEXCHANGE_TAG',true,x.notes
from data_sources ds
cross join (
  values
  ('se_openai_api','openai-api','OpenAI API developer demand proxy'),
  ('se_langchain','langchain','LangChain implementation demand proxy'),
  ('se_shopify','shopify','Shopify/eCommerce implementation demand proxy'),
  ('se_stripe','stripe','Payments/SaaS implementation demand proxy'),
  ('se_saas','saas','SaaS-tagged implementation demand proxy'),
  ('se_youtube_api','youtube-api','Creator/video API implementation demand proxy')
) as x(code,tag,notes)
where ds.code='stack_exchange'
on conflict(code) do update set
  query_spec=excluded.query_spec,
  evidence_type=excluded.evidence_type,
  enabled=true,
  notes=excluded.notes,
  updated_at=now();

insert into opportunity_external_query_map(
  opportunity_id,query_id,weight,rule_code,active,updated_at
)
select o.id,q.id,x.weight,x.rule_code,true,now()
from (
  values
  ('ai-agent-tools','se_langchain',0.70::numeric,'se_demand_langchain'),
  ('ai-agent-tools','se_openai_api',0.55::numeric,'se_demand_openai_api'),
  ('llm-tools','se_openai_api',0.70::numeric,'se_demand_openai_api'),
  ('llm-tools','se_langchain',0.60::numeric,'se_demand_langchain'),
  ('solo-saas','se_saas',0.60::numeric,'se_demand_saas'),
  ('solo-saas','se_stripe',0.50::numeric,'se_demand_stripe'),
  ('ecommerce-brands','se_shopify',0.70::numeric,'se_demand_shopify'),
  ('creator-media','se_youtube_api',0.55::numeric,'se_demand_youtube_api')
) as x(opportunity_slug,query_code,weight,rule_code)
join opportunities o on o.slug=x.opportunity_slug
join external_signal_queries q on q.code=x.query_code
on conflict(opportunity_id,query_id) do update set
  weight=excluded.weight,
  rule_code=excluded.rule_code,
  active=true,
  updated_at=now();

comment on table external_signal_queries is
'Generic external signal query registry. P4.1.2 adds Stack Exchange tag-count queries using official API totals only.';
