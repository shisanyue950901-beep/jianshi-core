create or replace function refresh_opportunity_scores_v01()
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
  active_evidence_total integer;
  inserted_count integer;
begin
  active_evidence_total := refresh_opportunity_evidence_v01();

  with scores as (
    select v.opportunity_id,'HEAT'::score_kind as score_kind,v.heat_score as score,
           jsonb_build_object(
             'github_repo_count',v.github_repo_count,
             'market_listing_count',v.market_listing_count,
             'github_strength',v.github_strength,
             'market_activity_score',v.market_activity_score,
             'source_count',v.source_count
           ) as reason_json
    from opportunity_scored_v01 v
    union all
    select v.opportunity_id,'BUSINESS'::score_kind,v.business_score,
           jsonb_build_object(
             'avg_monthly_profit',v.avg_monthly_profit,
             'avg_profit_margin',v.avg_profit_margin,
             'avg_listing_multiple',v.avg_listing_multiple,
             'market_listing_count',v.market_listing_count
           )
    from opportunity_scored_v01 v
    union all
    select v.opportunity_id,'BUILD'::score_kind,v.build_score,
           jsonb_build_object(
             'github_strength',v.github_strength,
             'solo_founder_fit',v.solo_founder_fit,
             'china_fit',v.china_fit,
             'market_activity_score',v.market_activity_score
           )
    from opportunity_scored_v01 v
    union all
    select v.opportunity_id,'CONTENT'::score_kind,v.content_score,
           jsonb_build_object(
             'heat_score',v.heat_score,
             'content_prior',v.content_prior,
             'evidence_breadth_score',v.evidence_breadth_score,
             'evidence_count',v.evidence_count
           )
    from opportunity_scored_v01 v
  )
  insert into score_snapshots(opportunity_id,score_kind,score,score_version,reason_json)
  select s.opportunity_id,s.score_kind,s.score,'OPP_V0.1',s.reason_json
  from scores s
  where not exists (
    select 1
    from latest_scores ls
    where ls.opportunity_id=s.opportunity_id
      and ls.score_kind=s.score_kind
      and ls.score_version='OPP_V0.1'
      and abs(ls.score-s.score)<0.01
  );

  get diagnostics inserted_count = row_count;

  return jsonb_build_object(
    'engine_version','OPP_V0.1',
    'active_evidence',active_evidence_total,
    'score_snapshots_inserted',inserted_count
  );
end;
$$;

revoke all on function refresh_opportunity_scores_v01() from public,anon,authenticated;
