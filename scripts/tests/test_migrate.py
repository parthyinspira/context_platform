import psycopg

from migrate import apply_migrations, rollback_migrations

CORE_TABLES = {"sources", "entities", "edges", "chunks", "proposed_changes"}

EXPECTED_COLUMNS = {
    "sources": {
        "id", "type", "uri", "schedule", "credentials_ref", "owner",
        "sensitivity", "status", "last_harvest_at", "last_cursor", "config_json",
    },
    "entities": {
        "id", "type", "name", "source_id", "external_id", "props",
        "ontology_version", "tombstoned_at",
    },
    "edges": {
        "id", "src_entity_id", "dst_entity_id", "relation", "confidence",
        "source_id", "ontology_version",
    },
    "chunks": {
        "id", "entity_id", "source_id", "text", "embedding", "embedding_model",
        "metadata", "harvested_at",
    },
    "proposed_changes": {"id", "kind", "payload", "confidence", "status", "created_at"},
}

HARVEST_RUN_STATES = {
    "CONNECTING", "DISCOVERING", "PROFILING", "PLANNED", "APPROVED",
    "HARVESTING", "VALIDATING", "PUBLISHED", "QUARANTINED", "FAILED", "PARTIAL",
}


def _existing_tables(conn) -> set[str]:
    rows = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    ).fetchall()
    return {row[0] for row in rows}


def _columns(conn, table: str) -> set[str]:
    rows = conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
        (table,),
    ).fetchall()
    return {row[0] for row in rows}


def test_fresh_database_creates_all_core_tables_with_contract_columns(database_url):
    apply_migrations(database_url)

    with psycopg.connect(database_url) as conn:
        tables = _existing_tables(conn)
        assert CORE_TABLES <= tables

        for table, expected_columns in EXPECTED_COLUMNS.items():
            assert expected_columns <= _columns(conn, table), f"{table} missing columns"


def test_reapplying_migrations_is_a_no_op(database_url):
    apply_migrations(database_url)
    applied_first = _applied_versions(database_url)

    apply_migrations(database_url)
    applied_second = _applied_versions(database_url)

    assert applied_first == applied_second

    with psycopg.connect(database_url) as conn:
        tables = _existing_tables(conn)
        assert CORE_TABLES <= tables


def test_rollback_drops_core_tables(database_url):
    apply_migrations(database_url)

    rollback_migrations(database_url)

    with psycopg.connect(database_url) as conn:
        tables = _existing_tables(conn)
        assert not (CORE_TABLES & tables)

    assert _applied_versions(database_url) == set()


def _applied_versions(database_url: str) -> set[str]:
    with psycopg.connect(database_url) as conn:
        rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
        return {row[0] for row in rows}


def _insert_source(conn) -> str:
    row = conn.execute(
        "INSERT INTO sources (type, uri) VALUES ('git', 'https://example.test/repo') "
        "RETURNING id"
    ).fetchone()
    return row[0]


def test_harvest_runs_table_has_contract_columns(database_url):
    apply_migrations(database_url)

    with psycopg.connect(database_url) as conn:
        assert "harvest_runs" in _existing_tables(conn)
        expected = {
            "id", "source_id", "state", "plan", "manifest", "error",
            "started_at", "updated_at",
        }
        assert expected <= _columns(conn, "harvest_runs")


def test_harvest_runs_accepts_every_lifecycle_state(database_url):
    apply_migrations(database_url)

    with psycopg.connect(database_url, autocommit=True) as conn:
        source_id = _insert_source(conn)
        for state in HARVEST_RUN_STATES:
            conn.execute(
                "INSERT INTO harvest_runs (source_id, state) VALUES (%s, %s)",
                (source_id, state),
            )
        count = conn.execute(
            "SELECT count(*) FROM harvest_runs WHERE source_id = %s", (source_id,)
        ).fetchone()[0]
        assert count == len(HARVEST_RUN_STATES)


def test_harvest_runs_rejects_unknown_state(database_url):
    apply_migrations(database_url)

    with psycopg.connect(database_url, autocommit=True) as conn:
        source_id = _insert_source(conn)
        try:
            conn.execute(
                "INSERT INTO harvest_runs (source_id, state) VALUES (%s, 'BOGUS')",
                (source_id,),
            )
            assert False, "expected a CHECK constraint violation"
        except psycopg.errors.CheckViolation:
            pass


def test_harvest_runs_dropped_on_rollback(database_url):
    apply_migrations(database_url)

    rollback_migrations(database_url)

    with psycopg.connect(database_url) as conn:
        assert "harvest_runs" not in _existing_tables(conn)
