drop view if exists public_daily_brief_v01;
create view public_daily_brief_v01 as
select
  c.*,
  row_number() over (
    order by
      case when c.change_state='NEWLY_VALIDATED' then 0
           when c.change_state='EVIDENCE_ACCELERATING' then 1
           when c.change_state='RISING' then 2
           else 3 end,
      coalesce(c.heat_delta_1d,0) desc,
      c.heat_score desc
  ) as rising_rank,
  row_number() over (
    order by c.public_ready desc,c.build_score desc,c.business_score desc
  ) as build_rank,
  row_number() over (
    order by c.content_score desc,c.heat_score desc
  ) as content_rank,
  row_number() over (
    order by c.public_ready desc,c.overall_score desc
  ) as overall_rank
from public_opportunity_changes_v01 c;

alter view public_daily_brief_v01 set (security_invoker=true);

comment on view public_daily_brief_v01 is
'R7.1 ranking policy: Today and Build prioritize multi-source validated opportunities; Content remains content-first; Rising remains change-first.';
