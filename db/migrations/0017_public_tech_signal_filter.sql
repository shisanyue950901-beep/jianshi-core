create or replace view public_tech_signals_v01 as
select
  gh.github_repository_id,
  gh.full_name,
  gh.description,
  gh.html_url,
  gh.language,
  gh.stars,
  gh.forks,
  gh.quality_score,
  gh.heat_score,
  gh.rank_score,
  array_agg(distinct q.code order by q.code) as matched_queries
from github_hot_current gh
join github_repository_discoveries gd
  on gd.github_repository_id=gh.github_repository_id
join github_discovery_queries q
  on q.id=gd.query_id
where q.code in ('ai_agents','llm','saas')
group by
  gh.github_repository_id,gh.full_name,gh.description,gh.html_url,gh.language,
  gh.stars,gh.forks,gh.quality_score,gh.heat_score,gh.rank_score;

alter view public_tech_signals_v01 set (security_invoker=true);

comment on view public_tech_signals_v01 is
'Curated technical signals limited to opportunity-related discovery queries; generic breakout search is excluded from public homepage.';
