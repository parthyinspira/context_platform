-- Adds a structured validation report column to harvest_runs (KAN-58/KAN-65).
-- `error` already carries a joined one-line summary (see 0004); `report` holds the
-- fuller `{status, checks:[{name,status,message,counts,samples}]}` shape so the
-- validation report screen can show per-check counts and samples. Nullable: no
-- harvester populates this yet (see spec/changes/kan-58-.../plan.md "Risks").
ALTER TABLE harvest_runs ADD COLUMN report JSONB;
