insert into data_sources
(code,name,homepage_url,source_status,access_method,auto_collect,redisplay_allowed,raw_storage_policy,refresh_interval_minutes,rate_limit_note)
values
('empire_flippers','Empire Flippers','https://empireflippers.com','GREEN','OFFICIAL_API',true,true,'LIMIT_TO_API_RESPONSE_NEEDED_FOR_AUDIT',360,'<= 1 request/second'),
('acquire','Acquire.com','https://acquire.com','RED','MANUAL_RESEARCH_ONLY',false,false,'NO_LISTING_MIRROR',null,null),
('flippa','Flippa','https://flippa.com','RED','MANUAL_RESEARCH_OR_WRITTEN_LICENSE',false,false,'NO_SUBSTANTIAL_DATABASE_COPY',null,null),
('microns','Microns','https://www.microns.io','RED','MANUAL_RESEARCH_ONLY',false,false,'NO_PAGE_MIRROR',null,null),
('sideprojectors','SideProjectors','https://www.sideprojectors.com','YELLOW','REVIEW_REQUIRED',false,false,'PENDING_REVIEW',null,null)
on conflict (code) do update set
  name=excluded.name,
  homepage_url=excluded.homepage_url,
  source_status=excluded.source_status,
  access_method=excluded.access_method,
  auto_collect=excluded.auto_collect,
  redisplay_allowed=excluded.redisplay_allowed,
  raw_storage_policy=excluded.raw_storage_policy,
  refresh_interval_minutes=excluded.refresh_interval_minutes,
  rate_limit_note=excluded.rate_limit_note,
  updated_at=now();

insert into source_policies
(source_id,policy_url,reviewed_at,commercial_use_allowed,automated_collection_allowed,redisplay_allowed,fulltext_storage_allowed,notes)
select id,'https://empireflippers.com/marketplace-api/','2026-10-06',true,true,true,false,
       '官方 Marketplace API；生产 collector 限制 <=1 req/s。'
from data_sources where code='empire_flippers'
and not exists (
  select 1 from source_policies p
  where p.source_id=data_sources.id and p.reviewed_at='2026-10-06'
);

insert into source_policies
(source_id,policy_url,reviewed_at,commercial_use_allowed,automated_collection_allowed,redisplay_allowed,fulltext_storage_allowed,notes)
select id,'https://acquire.com/buyerseller/','2026-10-06',false,false,false,false,
       '未书面授权前仅人工研究，不做自动抓取或跨域重展示。'
from data_sources where code='acquire'
and not exists (
  select 1 from source_policies p
  where p.source_id=data_sources.id and p.reviewed_at='2026-10-06'
);

insert into source_policies
(source_id,policy_url,reviewed_at,commercial_use_allowed,automated_collection_allowed,redisplay_allowed,fulltext_storage_allowed,notes)
select id,'https://flippa.com/terms-of-service/','2026-10-06',false,false,false,false,
       '未书面授权前不做批量抽取或 substantial database 复制。'
from data_sources where code='flippa'
and not exists (
  select 1 from source_policies p
  where p.source_id=data_sources.id and p.reviewed_at='2026-10-06'
);

insert into source_policies
(source_id,policy_url,reviewed_at,commercial_use_allowed,automated_collection_allowed,redisplay_allowed,fulltext_storage_allowed,notes)
select id,'https://www.microns.io/terms','2026-10-06',false,false,false,false,
       'Terms 禁止未经明确许可 crawl/scrape/spider。'
from data_sources where code='microns'
and not exists (
  select 1 from source_policies p
  where p.source_id=data_sources.id and p.reviewed_at='2026-10-06'
);
