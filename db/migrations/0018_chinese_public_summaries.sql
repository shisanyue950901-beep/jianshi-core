alter table github_repositories
  add column if not exists summary_zh text,
  add column if not exists summary_zh_source text,
  add column if not exists summary_zh_updated_at timestamptz;

update github_repositories
set summary_zh = case full_name
  when 'NousResearch/hermes-agent' then '可持续成长的 AI Agent 框架，面向长期使用和能力扩展。'
  when 'affaan-m/ECC' then '面向 Claude Code、Codex、OpenCode、Cursor 等 AI 编程工具的 Agent 性能优化系统，覆盖技能、记忆、安全和研究式开发。'
  when 'DietrichGebert/ponytail' then '让 AI Agent 更像经验丰富的高级开发者：优先减少无效代码，用更少实现完成任务。'
  when 'career-ops-hq/career-ops' then '开源 AI 求职助手，可扫描职位、匹配简历、优化求职材料，并辅助面试准备和投递追踪。'
  when 'Graphify-Labs/graphify' then '把代码、文档、SQL、配置和 PDF 转成可查询的知识图谱，方便 AI 编程工具理解复杂代码库。'
  when 'rohitg00/ai-engineering-from-scratch' then '面向 AI 工程实践的开源学习项目，强调从学习、构建到真正交付。'
  when 'ZhuLinsen/daily_stock_analysis' then 'LLM 驱动的多市场股票智能分析系统，整合多源行情、实时新闻、决策看板和自动推送。'
  when 'HKUDS/nanobot' then '超轻量、可自托管的个人 AI Agent 框架，支持 WebUI、工具、记忆、MCP、多 Agent 工作流和自动化。'
  when 'JuliusBrussee/caveman' then '为 AI 编程 Agent 压缩上下文和表达，目标是在保持效果的同时显著降低 Token 消耗。'
  when 'TauricResearch/TradingAgents' then '基于多智能体和大模型协作的金融交易研究框架。'
  when 'bytedance/deer-flow' then '面向长任务的开源超级 Agent 框架，可结合沙箱、记忆、工具、技能和子 Agent 完成研究、编码与内容创作。'
  when 'HKUDS/Vibe-Trading' then '面向个人交易研究场景的 AI Agent 项目。'
  else summary_zh
end,
summary_zh_source = case
  when full_name in (
    'NousResearch/hermes-agent','affaan-m/ECC','DietrichGebert/ponytail',
    'career-ops-hq/career-ops','Graphify-Labs/graphify',
    'rohitg00/ai-engineering-from-scratch','ZhuLinsen/daily_stock_analysis',
    'HKUDS/nanobot','JuliusBrussee/caveman','TauricResearch/TradingAgents',
    'bytedance/deer-flow','HKUDS/Vibe-Trading'
  ) then 'CURATED_R6'
  else summary_zh_source
end,
summary_zh_updated_at = case
  when full_name in (
    'NousResearch/hermes-agent','affaan-m/ECC','DietrichGebert/ponytail',
    'career-ops-hq/career-ops','Graphify-Labs/graphify',
    'rohitg00/ai-engineering-from-scratch','ZhuLinsen/daily_stock_analysis',
    'HKUDS/nanobot','JuliusBrussee/caveman','TauricResearch/TradingAgents',
    'bytedance/deer-flow','HKUDS/Vibe-Trading'
  ) then now()
  else summary_zh_updated_at
end;

create or replace function refresh_github_summary_zh_v01()
returns integer
language plpgsql
security definer
set search_path=public
as $$
declare
  updated_count integer;
begin
  with target as (
    select
      gr.id,
      gr.description,
      array_agg(distinct q.code) as query_codes
    from github_repositories gr
    join github_repository_discoveries gd on gd.github_repository_id=gr.id
    join github_discovery_queries q on q.id=gd.query_id
    where q.code in ('ai_agents','llm','saas')
      and (gr.summary_zh is null or btrim(gr.summary_zh)='')
    group by gr.id,gr.description
  )
  update github_repositories gr
  set
    summary_zh = case
      when coalesce(t.description,'') ~ '[一-龥]'
        then left(regexp_replace(t.description, E'\\s+', ' ', 'g'), 160)
      when 'ai_agents'=any(t.query_codes) and 'llm'=any(t.query_codes)
        then 'AI Agent 与大模型相关开源项目，聚焦智能体能力、自动化和开发工作流。'
      when 'ai_agents'=any(t.query_codes)
        then 'AI Agent 相关开源项目，聚焦智能体框架、自动化或工具协作。'
      when 'saas'=any(t.query_codes)
        then 'SaaS 相关开源项目，聚焦在线软件产品、开发框架或商业化基础设施。'
      else '大模型相关开源项目，聚焦 LLM 应用、开发工具或工作流。'
    end,
    summary_zh_source = case
      when coalesce(t.description,'') ~ '[一-龥]' then 'SOURCE_ZH'
      else 'RULE_FALLBACK_R6'
    end,
    summary_zh_updated_at=now()
  from target t
  where gr.id=t.id;

  get diagnostics updated_count = row_count;
  return updated_count;
end;
$$;

revoke all on function refresh_github_summary_zh_v01() from public,anon,authenticated;

select refresh_github_summary_zh_v01();

drop view if exists public_tech_signals_v01;
create view public_tech_signals_v01 as
select
  gh.github_repository_id,
  gh.full_name,
  gr.summary_zh,
  gr.summary_zh_source,
  gh.description as description_en,
  gh.html_url,
  gh.language,
  gh.stars,
  gh.forks,
  gh.quality_score,
  gh.heat_score,
  gh.rank_score,
  array_agg(distinct q.code order by q.code) as matched_queries
from github_hot_current gh
join github_repositories gr
  on gr.id=gh.github_repository_id
join github_repository_discoveries gd
  on gd.github_repository_id=gh.github_repository_id
join github_discovery_queries q
  on q.id=gd.query_id
where q.code in ('ai_agents','llm','saas')
group by
  gh.github_repository_id,gh.full_name,gr.summary_zh,gr.summary_zh_source,
  gh.description,gh.html_url,gh.language,gh.stars,gh.forks,
  gh.quality_score,gh.heat_score,gh.rank_score;

alter view public_tech_signals_v01 set (security_invoker=true);

drop view if exists public_market_evidence_v01;
create view public_market_evidence_v01 as
select
  oe.opportunity_id,
  ml.id as marketplace_listing_id,
  ml.listing_number,
  ml.public_title as source_title_en,
  case
    when ml.monetizations ? 'SaaS'
      then 'SaaS 商业样本 #' || ml.listing_number::text
    when ml.monetizations ?| array['YouTube','Newsletter','Digital Product','Info Product']
      then '创作者与数字媒体商业样本 #' || ml.listing_number::text
    when ml.monetizations ?| array['Amazon FBA','Amazon FBM','eCommerce','DropShipping']
      then '电商品牌商业样本 #' || ml.listing_number::text
    when ml.monetizations ?| array['Affiliate','Amazon Associates','Display Advertising']
      then '内容与联盟营销商业样本 #' || ml.listing_number::text
    else '互联网商业样本 #' || ml.listing_number::text
  end as display_title_zh,
  ml.listing_status,
  ml.listing_price,
  ml.unpriced,
  ml.average_monthly_net_profit,
  ml.average_monthly_gross_revenue,
  ml.profit_margin,
  ml.listing_multiple,
  ml.annual_listing_multiple,
  ml.hours_worked_per_week,
  ml.monetizations,
  ml.niches,
  ml.source_url,
  oe.rule_code,
  oe.last_seen_at
from opportunity_evidence oe
join marketplace_listings ml on ml.id=oe.entity_id
where oe.active=true
  and oe.rule_version='OPP_V0.1'
  and oe.evidence_type='MARKETPLACE_LISTING'
  and ml.active=true;

alter view public_market_evidence_v01 set (security_invoker=true);


drop view if exists public_github_evidence_v01;
create view public_github_evidence_v01 as
select
  oe.opportunity_id,
  gr.id as github_repository_id,
  gr.full_name,
  gr.summary_zh,
  gr.summary_zh_source,
  gr.description as description_en,
  gr.html_url,
  gh.language,
  gh.stars,
  gh.forks,
  gh.quality_score,
  gh.heat_score,
  gh.rank_score,
  oe.rule_code,
  oe.last_seen_at
from opportunity_evidence oe
join github_repositories gr on gr.id=oe.entity_id
join github_hot_current gh on gh.github_repository_id=gr.id
where oe.active=true
  and oe.rule_version='OPP_V0.1'
  and oe.evidence_type='GITHUB_REPOSITORY';

alter view public_github_evidence_v01 set (security_invoker=true);
