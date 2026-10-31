"""Deterministic SQL lineage extraction (KAN-25 spike).

Parses SQL text with `sqlglot` and turns it into Ontology v0 `Table` entities and
`READS_FROM` / `WRITES_TO` edges, without calling an LLM.

This module is intentionally harvester-independent: no `harvesters/` framework
exists yet in this repo (Epic 3), so `extract_sql_lineage()` is a plain function a
future Git or SQL-database harvester's `normalize()` step can call once it has a
real `source_id` and a way to resolve table external ids to `entities.id` UUIDs.

Scope (see spec/changes/kan-25-sql-lineage-extraction-sqlglot/proposal.md):
- Table-level lineage only (no column lineage).
- SELECT/JOIN, INSERT ... SELECT, UPDATE ... FROM, CREATE TABLE ... AS SELECT,
  MERGE INTO ... USING, and CTEs (resolved to their base tables).
- Statements sqlglot cannot parse are reported in `LineageResult.unparsed`,
  never silently dropped.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp

ONTOLOGY_VERSION_DEFAULT = "v0"
DETERMINISTIC_CONFIDENCE = 0.9


@dataclass
class Entity:
    """Shaped to the `entities` table contract in CLAUDE.md (Ontology v0)."""

    type: str
    name: str
    source_id: str
    external_id: str
    ontology_version: str = ONTOLOGY_VERSION_DEFAULT
    props: dict = field(default_factory=dict)


@dataclass
class Edge:
    """Shaped to the `edges` table contract in CLAUDE.md (Ontology v0).

    `src_entity_id` / `dst_entity_id` hold `external_id` values here, not real
    `entities.id` UUIDs: this spike has no entity store to resolve against. A
    harvester's normalize step must resolve these to real entity ids before
    upserting into `edges` (see proposal.md "Risks and open questions").
    """

    src_entity_id: str
    dst_entity_id: str
    relation: str
    source_id: str
    ontology_version: str = ONTOLOGY_VERSION_DEFAULT
    confidence: float = DETERMINISTIC_CONFIDENCE


@dataclass
class UnparsedStatement:
    statement: str
    error: str


@dataclass
class LineageResult:
    entities: list[Entity] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    unparsed: list[UnparsedStatement] = field(default_factory=list)


def _table_external_id(table: exp.Table) -> str:
    """Render a sqlglot Table node as `schema.table` (or just `table`)."""
    parts = [p for p in (table.db, table.name) if p]
    return ".".join(parts) if parts else table.name


def _is_cte_name(table: exp.Table, cte_names: set[str]) -> bool:
    return table.db == "" and table.name in cte_names


def _collect_source_tables(statement: exp.Expression, cte_names: set[str]) -> dict[str, exp.Table]:
    """All tables read anywhere in the statement, excluding CTE references and the write target."""
    tables: dict[str, exp.Table] = {}
    for table in statement.find_all(exp.Table):
        if _is_cte_name(table, cte_names):
            continue
        tables[_table_external_id(table)] = table
    return tables


def _write_target(statement: exp.Expression) -> exp.Table | None:
    if isinstance(statement, exp.Insert):
        target = statement.this
        if isinstance(target, exp.Table):
            return target
        return target.find(exp.Table) if target else None
    if isinstance(statement, exp.Update):
        return statement.this if isinstance(statement.this, exp.Table) else None
    if isinstance(statement, exp.Create) and statement.kind and statement.kind.upper() == "TABLE":
        target = statement.this
        return target.find(exp.Table) if target is not None else None
    if isinstance(statement, exp.Merge):
        return statement.this if isinstance(statement.this, exp.Table) else None
    return None


def _extract_one(
    statement: exp.Expression, source_id: str, ontology_version: str
) -> tuple[list[Entity], list[Edge]]:
    entities: dict[str, Entity] = {}
    edges: list[Edge] = []

    cte_names = {cte.alias for cte in statement.find_all(exp.CTE)}

    write_table = _write_target(statement)
    write_external_id = _table_external_id(write_table) if write_table is not None else None

    source_tables = _collect_source_tables(statement, cte_names)
    source_tables.pop(write_external_id, None) if write_external_id else None

    def entity_for(table: exp.Table, external_id: str) -> Entity:
        if external_id not in entities:
            entities[external_id] = Entity(
                type="Table",
                name=table.name,
                source_id=source_id,
                external_id=external_id,
                ontology_version=ontology_version,
                props={"schema": table.db} if table.db else {},
            )
        return entities[external_id]

    if write_table is not None and write_external_id:
        entity_for(write_table, write_external_id)
        edges.append(
            Edge(
                src_entity_id=write_external_id,
                dst_entity_id=write_external_id,
                relation="WRITES_TO",
                source_id=source_id,
                ontology_version=ontology_version,
            )
        )
        for external_id, table in source_tables.items():
            entity_for(table, external_id)
            edges.append(
                Edge(
                    src_entity_id=write_external_id,
                    dst_entity_id=external_id,
                    relation="READS_FROM",
                    source_id=source_id,
                    ontology_version=ontology_version,
                )
            )
    elif isinstance(statement, exp.Select) or statement.find(exp.Select):
        # Pure read (plain SELECT): no write target, only READS_FROM.
        query_id = "query"
        for external_id, table in source_tables.items():
            entity_for(table, external_id)
            edges.append(
                Edge(
                    src_entity_id=query_id,
                    dst_entity_id=external_id,
                    relation="READS_FROM",
                    source_id=source_id,
                    ontology_version=ontology_version,
                )
            )

    # De-duplicate the accidental double WRITES_TO append above into a single edge.
    deduped: list[Edge] = []
    seen: set[tuple[str, str, str]] = set()
    for edge in edges:
        key = (edge.src_entity_id, edge.dst_entity_id, edge.relation)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(edge)

    return list(entities.values()), deduped


def extract_sql_lineage(
    sql: str,
    source_id: str,
    ontology_version: str = ONTOLOGY_VERSION_DEFAULT,
) -> LineageResult:
    """Extract table-level READS_FROM/WRITES_TO lineage from SQL text.

    `sql` may contain one statement or a `;`-separated script. Statements that
    fail to parse are collected in `LineageResult.unparsed` and do not stop
    extraction of the remaining statements.
    """
    result = LineageResult()

    # sqlglot.parse() raises on the first bad statement in a script and drops the
    # rest, which conflicts with "report, don't drop" (docs/HARVESTERS.md rule 11,
    # "everything is manifested"). Split into statements ourselves (naive `;`
    # split -- a known limitation for strings/procedures containing `;`, see
    # design.md) and parse each independently so one bad statement cannot hide
    # the others.
    raw_chunks = [s.strip() for s in sql.split(";") if s.strip()]
    if not raw_chunks:
        return result

    for raw in raw_chunks:
        try:
            statement = sqlglot.parse_one(raw)
        except Exception as exc:
            result.unparsed.append(UnparsedStatement(statement=raw, error=str(exc)))
            continue
        try:
            entities, edges = _extract_one(statement, source_id, ontology_version)
        except Exception as exc:
            result.unparsed.append(UnparsedStatement(statement=raw, error=str(exc)))
            continue
        for entity in entities:
            if entity.external_id not in {e.external_id for e in result.entities}:
                result.entities.append(entity)
        result.edges.extend(edges)

    return result
