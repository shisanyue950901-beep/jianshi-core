create or replace view marketplace_listing_history as
select distinct on (
  marketplace_listing_id,
  coalesce(snapshot->>'source_updated_at', snapshot_hash)
)
  id,
  marketplace_listing_id,
  source_id,
  observed_at,
  snapshot_hash,
  snapshot,
  created_at
from marketplace_listing_snapshots
order by
  marketplace_listing_id,
  coalesce(snapshot->>'source_updated_at', snapshot_hash),
  observed_at asc,
  id asc;

comment on view marketplace_listing_history is
'Canonical marketplace history view. Collapses bootstrap/collector duplicate snapshots that represent the same upstream source_updated_at version.';
