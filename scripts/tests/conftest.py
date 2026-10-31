import subprocess
import sys
import time
import uuid
from pathlib import Path

import psycopg
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def database_url():
    container_name = f"ctxplat-migtest-{uuid.uuid4().hex[:8]}"
    subprocess.run(
        [
            "docker", "run", "-d", "--rm",
            "--name", container_name,
            "-e", "POSTGRES_USER=context",
            "-e", "POSTGRES_PASSWORD=change-me",
            "-e", "POSTGRES_DB=context",
            "-P",
            "pgvector/pgvector:pg16",
        ],
        check=True,
        capture_output=True,
    )
    try:
        port = subprocess.run(
            ["docker", "port", container_name, "5432/tcp"],
            check=True, capture_output=True, text=True,
        ).stdout.strip().rsplit(":", 1)[-1]
        url = f"postgresql://context:change-me@localhost:{port}/context"
        _wait_for_postgres(url)
        yield url
    finally:
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)


def _wait_for_postgres(url: str, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            with psycopg.connect(url, connect_timeout=2) as conn:
                conn.execute("SELECT 1")
            return
        except psycopg.OperationalError as exc:
            last_error = exc
            time.sleep(0.5)
    raise RuntimeError(f"postgres did not become ready in time: {last_error}")
