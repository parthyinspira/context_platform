-- Provisional run-tracking table for the dispatcher's POST /sources/{id}/run
-- endpoint (KAN-106). This is intentionally minimal (no CONNECTING/PUBLISHED/
-- QUARANTINED lifecycle states) because the full `harvest_runs` lifecycle table
-- described in harvester-framework.md is scoped to the later harvest-core epic
-- (KAN-75+). Expect this table to be superseded or merged into `harvest_runs`
-- once that epic lands.
CREATE TABLE dispatcher_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources (id),
    status TEXT NOT NULL DEFAULT 'queued',
    requested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_dispatcher_runs_source_id ON dispatcher_runs (source_id);
