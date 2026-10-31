"""An in-memory fake of the tiny subset of psycopg's DB-API used by PostgresChunkWriter.

Used because no live Postgres is available in this environment; the real adapter issues
plain SQL against the `chunks` table from migration 0001 and is otherwise untested
against a live Postgres server (noted in verification.md).
"""
import json
from dataclasses import dataclass, field


@dataclass
class _ChunkRow:
    id: str
    entity_id: str
    source_id: str
    text: str
    embedding: list
    embedding_model: str
    metadata: dict


@dataclass
class FakeChunksConnection:
    rows: list[_ChunkRow] = field(default_factory=list)
    committed: int = 0

    def cursor(self) -> "FakeChunksCursor":
        return FakeChunksCursor(self)

    def commit(self) -> None:
        self.committed += 1


class FakeChunksCursor:
    def __init__(self, conn: FakeChunksConnection):
        self._conn = conn

    def execute(self, sql: str, params: tuple = ()) -> None:
        sql_norm = " ".join(sql.split())
        if sql_norm.startswith("INSERT INTO chunks"):
            chunk_id, entity_id, source_id, text, embedding, embedding_model, metadata_json = params
            self._conn.rows.append(
                _ChunkRow(
                    id=chunk_id,
                    entity_id=entity_id,
                    source_id=source_id,
                    text=text,
                    embedding=embedding,
                    embedding_model=embedding_model,
                    metadata=json.loads(metadata_json),
                )
            )
        else:
            raise AssertionError(f"unexpected SQL in fake: {sql_norm}")
