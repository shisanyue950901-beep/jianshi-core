-- P4.1.1 external signal FK index hardening.
-- Covers the evidence_type foreign key introduced by 0047.
-- No scoring, publication, source-policy, Auth, or Newsletter behavior changes.

create index if not exists idx_external_signal_queries_evidence_type
  on external_signal_queries(evidence_type);
