"""Tests for the KAN-25 SQL lineage extraction spike (ontology/sql_lineage.py).

Scenarios map to spec/changes/kan-25-sql-lineage-extraction-sqlglot/specs/sql-lineage-extraction.md.
"""
from pathlib import Path

from ontology.sql_lineage import extract_sql_lineage

SOURCE_ID = "11111111-1111-1111-1111-111111111111"
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def _fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text()


def _relations(result, relation):
    return {(e.src_entity_id, e.dst_entity_id) for e in result.edges if e.relation == relation}


def _entity_external_ids(result):
    return {e.external_id for e in result.entities}


# scenario: reads-from-select
def test_select_with_join_yields_reads_from_edges():
    sql = """
        SELECT a.id, b.name
        FROM schema.orders a
        JOIN schema.customers b ON a.customer_id = b.id
    """
    result = extract_sql_lineage(sql, source_id=SOURCE_ID)

    assert "schema.orders" in _entity_external_ids(result)
    assert "schema.customers" in _entity_external_ids(result)
    reads = _relations(result, "READS_FROM")
    assert any(dst == "schema.orders" for _src, dst in reads)
    assert any(dst == "schema.customers" for _src, dst in reads)
    assert result.unparsed == []
    for entity in result.entities:
        assert entity.type == "Table"
        assert entity.source_id == SOURCE_ID
        assert entity.ontology_version == "v0"
    for edge in result.edges:
        assert edge.source_id == SOURCE_ID
        assert edge.ontology_version == "v0"
        assert 0.0 < edge.confidence <= 1.0


# scenario: writes-to-insert-select
def test_insert_select_yields_reads_from_and_writes_to():
    sql = (
        "INSERT INTO schema.summary SELECT customer_id, sum(total) "
        "FROM schema.orders GROUP BY customer_id"
    )
    result = extract_sql_lineage(sql, source_id=SOURCE_ID)

    writes = _relations(result, "WRITES_TO")
    reads = _relations(result, "READS_FROM")
    assert any(dst == "schema.summary" for _src, dst in writes)
    assert any(dst == "schema.orders" for _src, dst in reads)
    assert result.unparsed == []


def test_update_from_yields_reads_from_and_writes_to():
    sql = (
        "UPDATE schema.summary SET total = o.total FROM schema.orders o "
        "WHERE o.id = schema.summary.id"
    )
    result = extract_sql_lineage(sql, source_id=SOURCE_ID)

    writes = _relations(result, "WRITES_TO")
    reads = _relations(result, "READS_FROM")
    assert any(dst == "schema.summary" for _src, dst in writes)
    assert any(dst == "schema.orders" for _src, dst in reads)


# scenario: writes-to-ctas
def test_ctas_yields_reads_from_and_writes_to():
    sql = (
        "CREATE TABLE schema.report AS SELECT customer_id, count(*) "
        "FROM schema.orders GROUP BY customer_id"
    )
    result = extract_sql_lineage(sql, source_id=SOURCE_ID)

    writes = _relations(result, "WRITES_TO")
    reads = _relations(result, "READS_FROM")
    assert any(dst == "schema.report" for _src, dst in writes)
    assert any(dst == "schema.orders" for _src, dst in reads)


def test_merge_into_yields_reads_from_and_writes_to():
    sql = (
        "MERGE INTO schema.summary AS t "
        "USING schema.orders AS s ON t.id = s.id "
        "WHEN MATCHED THEN UPDATE SET t.total = s.total "
        "WHEN NOT MATCHED THEN INSERT (id, total) VALUES (s.id, s.total)"
    )
    result = extract_sql_lineage(sql, source_id=SOURCE_ID)

    writes = _relations(result, "WRITES_TO")
    reads = _relations(result, "READS_FROM")
    assert any(dst == "schema.summary" for _src, dst in writes)
    assert any(dst == "schema.orders" for _src, dst in reads)


def test_cte_resolves_to_base_table_not_emitted_as_entity():
    sql = """
        WITH recent AS (SELECT * FROM schema.orders WHERE created_at > '2026-01-01')
        INSERT INTO schema.summary SELECT * FROM recent
    """
    result = extract_sql_lineage(sql, source_id=SOURCE_ID)

    external_ids = _entity_external_ids(result)
    assert "schema.orders" in external_ids
    assert "recent" not in external_ids
    reads = _relations(result, "READS_FROM")
    assert any(dst == "schema.orders" for _src, dst in reads)


# scenario: multi-statement-script
def test_multi_statement_script_reports_unparsed_without_dropping_valid_statements():
    script = """
        INSERT INTO schema.summary SELECT * FROM schema.orders;
        SELEKT * FORM not sql at all;
        CREATE TABLE schema.report AS SELECT * FROM schema.customers;
    """
    result = extract_sql_lineage(script, source_id=SOURCE_ID)

    writes = _relations(result, "WRITES_TO")
    assert any(dst == "schema.summary" for _src, dst in writes)
    assert any(dst == "schema.report" for _src, dst in writes)
    assert len(result.unparsed) == 1
    assert "SELEKT" in result.unparsed[0].statement


def test_unparseable_single_statement_is_reported_not_raised():
    result = extract_sql_lineage("THIS IS NOT SQL AT ALL", source_id=SOURCE_ID)

    assert result.entities == []
    assert result.edges == []
    assert len(result.unparsed) == 1
    assert result.unparsed[0].error


# fixture-file variants of the scenarios above, exercising on-disk SQL files
# (closer to how a future harvester would read .sql files from a repo)

def test_fixture_reads_from_select():
    result = extract_sql_lineage(_fixture("reads_from_select.sql"), source_id=SOURCE_ID)
    assert any(dst == "schema.orders" for _src, dst in _relations(result, "READS_FROM"))
    assert result.unparsed == []


def test_fixture_writes_to_insert_select():
    result = extract_sql_lineage(_fixture("writes_to_insert_select.sql"), source_id=SOURCE_ID)
    assert any(dst == "schema.summary" for _src, dst in _relations(result, "WRITES_TO"))
    assert result.unparsed == []


def test_fixture_writes_to_ctas():
    result = extract_sql_lineage(_fixture("writes_to_ctas.sql"), source_id=SOURCE_ID)
    assert any(dst == "schema.report" for _src, dst in _relations(result, "WRITES_TO"))
    assert result.unparsed == []


def test_fixture_multi_statement_script():
    result = extract_sql_lineage(_fixture("multi_statement_script.sql"), source_id=SOURCE_ID)
    assert len(result.unparsed) == 1
    assert any(dst == "schema.summary" for _src, dst in _relations(result, "WRITES_TO"))
    assert any(dst == "schema.report" for _src, dst in _relations(result, "WRITES_TO"))
