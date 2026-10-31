CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL,
    uri TEXT NOT NULL,
    schedule TEXT,
    credentials_ref TEXT,
    owner TEXT,
    sensitivity TEXT NOT NULL DEFAULT 'internal',
    status TEXT NOT NULL DEFAULT 'active',
    last_harvest_at TIMESTAMPTZ,
    last_cursor TEXT,
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    source_id UUID NOT NULL REFERENCES sources (id),
    external_id TEXT NOT NULL,
    props JSONB NOT NULL DEFAULT '{}'::jsonb,
    ontology_version TEXT NOT NULL,
    tombstoned_at TIMESTAMPTZ,
    UNIQUE (source_id, external_id)
);

CREATE INDEX idx_entities_source_id ON entities (source_id);
CREATE INDEX idx_entities_tombstoned_at ON entities (tombstoned_at);

CREATE TABLE edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    src_entity_id UUID NOT NULL REFERENCES entities (id),
    dst_entity_id UUID NOT NULL REFERENCES entities (id),
    relation TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    source_id UUID NOT NULL REFERENCES sources (id),
    ontology_version TEXT NOT NULL
);

CREATE INDEX idx_edges_source_id ON edges (source_id);
CREATE INDEX idx_edges_src_entity_id ON edges (src_entity_id);
CREATE INDEX idx_edges_dst_entity_id ON edges (dst_entity_id);

CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES entities (id),
    source_id UUID NOT NULL REFERENCES sources (id),
    text TEXT NOT NULL,
    embedding vector(1536),
    embedding_model TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    harvested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_chunks_source_id ON chunks (source_id);
CREATE INDEX idx_chunks_entity_id ON chunks (entity_id);

CREATE TABLE proposed_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kind TEXT NOT NULL,
    payload JSONB NOT NULL,
    confidence REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
