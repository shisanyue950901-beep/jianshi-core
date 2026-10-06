create table if not exists opportunity_profiles (
  opportunity_id uuid primary key references opportunities(id) on delete cascade,
  engine_version text not null,
  content_prior numeric(5,2) not null check (content_prior between 0 and 100),
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists opportunity_evidence (
  id uuid primary key default gen_random_uuid(),
  opportunity_id uuid not null references opportunities(id) on delete cascade,
  source_id uuid not null references data_sources(id),
  evidence_type text not null,
  entity_id uuid not null,
  weight numeric(6,3) not null default 1.0,
  rule_code text not null,
  rule_version text not null,
  active boolean not null default true,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique(opportunity_id,evidence_type,entity_id,rule_version)
);
create index if not exists idx_opportunity_evidence_active
  on opportunity_evidence(opportunity_id,active,last_seen_at desc);
create index if not exists idx_opportunity_evidence_source
  on opportunity_evidence(source_id);

alter table opportunity_profiles enable row level security;
alter table opportunity_evidence enable row level security;
revoke all on opportunity_profiles,opportunity_evidence from anon,authenticated;

insert into opportunities(
  slug,title,category,thesis,problem,target_customer,business_model,china_fit,solo_founder_fit,status
)
values
('ai-agent-tools','AI Agent 工具与自动化','AI_AGENT',
 'Agent 正从演示走向可执行工作流，开源生态是早期技术供给信号。',
 '企业和个人需要把多步骤知识工作自动化。','开发者、中小企业、知识工作者',
 'SaaS / API / 企业服务',85,75,'ACTIVE'),
('llm-tools','LLM 应用与工具','LLM',
 '模型能力持续下沉，围绕调用、工作流、评测和垂直应用仍会产生产品机会。',
 '通用模型与真实业务流程之间存在产品化缺口。','开发者、团队、垂直行业用户',
 'SaaS / API / 开源商业化',85,75,'ACTIVE'),
('solo-saas','一人公司 SaaS','SAAS',
 'SaaS 同时具备开源供给与真实交易市场现金流证据，是见势首个天然多源赛道。',
 '细分业务软件仍存在大量小而稳定的付费需求。','小微企业、专业人士、垂直团队',
 '订阅制 SaaS',80,82,'ACTIVE'),
('ecommerce-brands','轻量电商品牌与 Amazon 资产','ECOMMERCE',
 '大量可交易电商资产提供真实收入、利润和估值样本。',
 '细分消费需求可以通过品牌、供应链与渠道运营变现。','电商创业者、品牌运营者',
 '商品毛利 / Amazon / DTC',55,45,'ACTIVE'),
('affiliate-content','联盟营销与内容资产','AFFILIATE_CONTENT',
 '内容站、联盟营销与展示广告仍存在可交易现金流资产。',
 '高意图搜索与内容流量可以被广告和联盟佣金货币化。','内容创业者、SEO 团队、一人公司',
 'Affiliate / Ads / Content',55,80,'ACTIVE'),
('creator-media','创作者媒体资产','CREATOR_MEDIA',
 'YouTube、Newsletter 等媒体资产可以形成可出售的长期现金流。',
 '垂直受众与内容分发能力可以沉淀为媒体资产。','创作者、小团队、个人品牌',
 '广告 / 订阅 / 数字产品',75,85,'ACTIVE')
on conflict (slug) do update set
  title=excluded.title,
  category=excluded.category,
  thesis=excluded.thesis,
  problem=excluded.problem,
  target_customer=excluded.target_customer,
  business_model=excluded.business_model,
  china_fit=excluded.china_fit,
  solo_founder_fit=excluded.solo_founder_fit,
  status=excluded.status,
  updated_at=now();

insert into opportunity_profiles(opportunity_id,engine_version,content_prior,notes)
select id,'OPP_V0.1',
  case slug
    when 'ai-agent-tools' then 92
    when 'llm-tools' then 88
    when 'solo-saas' then 80
    when 'ecommerce-brands' then 72
    when 'affiliate-content' then 82
    when 'creator-media' then 88
  end,
  'Rule-based priors; no paid LLM required in R4 v0.1.'
from opportunities
where slug in ('ai-agent-tools','llm-tools','solo-saas','ecommerce-brands','affiliate-content','creator-media')
on conflict (opportunity_id) do update set
  engine_version=excluded.engine_version,
  content_prior=excluded.content_prior,
  notes=excluded.notes,
  updated_at=now();
