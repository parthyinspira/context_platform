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
