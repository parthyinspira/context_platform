-- Full harvest run lifecycle table (KAN-75), per spec/capabilities/harvester-framework.md
-- "Lifecycle" requirement and docs/HARVESTERS.md section 1. Distinct from the provisional
-- `dispatcher_runs` table added in KAN-106 (see its migration comment); reconciling the two
-- is left to a later story.
CREATE TABLE harvest_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources (id),
    state TEXT NOT NULL DEFAULT 'CONNECTING' CHECK (
        state IN (
            'CONNECTING', 'DISCOVERING', 'PROFILING', 'PLANNED', 'APPROVED',
            'HARVESTING', 'VALIDATING', 'PUBLISHED', 'QUARANTINED', 'FAILED', 'PARTIAL'
        )
    ),
    plan JSONB NOT NULL DEFAULT '{}'::jsonb,
    manifest JSONB NOT NULL DEFAULT '{}'::jsonb,
    error TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_harvest_runs_source_id ON harvest_runs (source_id);
CREATE INDEX idx_harvest_runs_state ON harvest_runs (state);
