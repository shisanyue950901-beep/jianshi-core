-- R7.7 Observed sold outcomes from the official Empire Flippers API.
-- Important: "last asking price before sold" is NOT a transaction price.

alter table marketplace_listings
  add column if not exists first_observed_sold_at timestamptz,
  add column if not exists last_asking_price_before_sold numeric,
  add column if not exists last_asking_annual_multiple_before_sold numeric,
  add column if not exists last_asking_monthly_profit_before_sold numeric,
  add column if not exists last_asking_annual_profit_before_sold numeric;

create table if not exists marketplace_listing_status_events (
  id bigserial primary key,
  marketplace_listing_id uuid not null references marketplace_listings(id) on delete cascade,
  source_id uuid not null references data_sources(id),
  from_status text,
  to_status text not null,
  observed_at timestamptz not null default now(),
  prior_listing_price numeric,
  prior_annual_listing_multiple numeric,
  prior_average_monthly_net_profit numeric,
  prior_average_annual_net_profit numeric,
  created_at timestamptz not null default now()
);
create index if not exists idx_marketplace_status_events_listing_time
  on marketplace_listing_status_events(marketplace_listing_id,observed_at desc);
create index if not exists idx_marketplace_status_events_transition
  on marketplace_listing_status_events(source_id,from_status,to_status,observed_at desc);

alter table marketplace_listing_status_events enable row level security;
revoke all on marketplace_listing_status_events from anon,authenticated;
revoke all on sequence marketplace_listing_status_events_id_seq from anon,authenticated;

create or replace function prepare_marketplace_status_transition_v01()
returns trigger
language plpgsql
set search_path=public
as $$
begin
  if tg_op='INSERT' then
    if new.listing_status='Sold' then
      new.first_observed_sold_at=coalesce(new.first_observed_sold_at,now());
      new.active=false;
    end if;
    return new;
  end if;

  if old.listing_status is distinct from new.listing_status
     and new.listing_status='Sold' then
    new.first_observed_sold_at=coalesce(old.first_observed_sold_at,now());
    new.last_asking_price_before_sold=coalesce(old.listing_price,old.last_asking_price_before_sold);
    new.last_asking_annual_multiple_before_sold=coalesce(old.annual_listing_multiple,old.last_asking_annual_multiple_before_sold);
    new.last_asking_monthly_profit_before_sold=coalesce(old.average_monthly_net_profit,old.last_asking_monthly_profit_before_sold);
    new.last_asking_annual_profit_before_sold=coalesce(old.average_annual_net_profit,old.last_asking_annual_profit_before_sold);
    new.active=false;
  end if;

  return new;
end;
$$;

drop trigger if exists trg_prepare_marketplace_status_transition_v01 on marketplace_listings;
create trigger trg_prepare_marketplace_status_transition_v01
before insert or update on marketplace_listings
for each row execute function prepare_marketplace_status_transition_v01();

create or replace function log_marketplace_status_transition_v01()
returns trigger
language plpgsql
set search_path=public
as $$
begin
  if tg_op='INSERT' then
    if new.listing_status is not null then
      insert into marketplace_listing_status_events(
        marketplace_listing_id,source_id,from_status,to_status,observed_at
      ) values(new.id,new.source_id,null,new.listing_status,now());
    end if;
    return new;
  end if;

  if old.listing_status is distinct from new.listing_status then
    insert into marketplace_listing_status_events(
      marketplace_listing_id,source_id,from_status,to_status,observed_at,
      prior_listing_price,prior_annual_listing_multiple,
      prior_average_monthly_net_profit,prior_average_annual_net_profit
    ) values(
      new.id,new.source_id,old.listing_status,new.listing_status,now(),
      old.listing_price,old.annual_listing_multiple,
      old.average_monthly_net_profit,old.average_annual_net_profit
    );
  end if;
  return new;
end;
$$;

drop trigger if exists trg_log_marketplace_status_transition_v01 on marketplace_listings;
create trigger trg_log_marketplace_status_transition_v01
after insert or update on marketplace_listings
for each row execute function log_marketplace_status_transition_v01();

drop view if exists marketplace_observed_exits_v01;
create view marketplace_observed_exits_v01 as
select
  e.id as status_event_id,
  e.marketplace_listing_id,
  ml.listing_number,
  ml.public_title,
  e.observed_at as first_observed_sold_at,
  e.prior_listing_price as last_asking_price_before_sold,
  e.prior_annual_listing_multiple as last_asking_annual_multiple_before_sold,
  e.prior_average_monthly_net_profit as monthly_profit_before_sold,
  e.prior_average_annual_net_profit as annual_profit_before_sold,
  ml.days_on_marketplace,
  ml.monetizations,
  ml.niches,
  ml.source_url
from marketplace_listing_status_events e
join marketplace_listings ml on ml.id=e.marketplace_listing_id
where e.from_status='For Sale'
  and e.to_status='Sold';

alter view marketplace_observed_exits_v01 set (security_invoker=true);

drop view if exists marketplace_exit_benchmarks_v01;
create view marketplace_exit_benchmarks_v01 as
with exploded as (
  select
    e.*,
    m.value as monetization
  from marketplace_observed_exits_v01 e
  cross join lateral jsonb_array_elements_text(e.monetizations) m(value)
)
select
  monetization,
  count(*) as observed_exit_count,
  count(last_asking_price_before_sold) as exits_with_prior_asking_price,
  round(percentile_cont(0.5) within group(order by last_asking_price_before_sold)::numeric,2)
    as median_last_asking_price_before_sold,
  round(percentile_cont(0.5) within group(order by last_asking_annual_multiple_before_sold)::numeric,2)
    as median_last_asking_annual_multiple_before_sold,
  round(percentile_cont(0.5) within group(order by days_on_marketplace)::numeric,1)
    as median_days_on_marketplace
from exploded
group by monetization
order by observed_exit_count desc,monetization;

alter view marketplace_exit_benchmarks_v01 set (security_invoker=true);

comment on view marketplace_observed_exits_v01 is
'Observed For Sale -> Sold transitions. Prior asking price/multiple are NOT transaction price/multiple.';
comment on view marketplace_exit_benchmarks_v01 is
'Aggregates observed exits using the last asking state before Sold; never label these values as actual sale prices.';
