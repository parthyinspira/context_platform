import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_conn():
    conn = MagicMock()
    conn.cursor.return_value = MagicMock()
    return conn


@pytest.fixture
def app_with_mock_conn(mock_conn):
    from app import main as app_module
    from fastapi.testclient import TestClient

    original = app_module.connection_factory_dependency

    def override():
        return lambda: mock_conn

    app_module.app.dependency_overrides[original] = override
    client = TestClient(app_module.app)
    yield client, mock_conn
    app_module.app.dependency_overrides.clear()
