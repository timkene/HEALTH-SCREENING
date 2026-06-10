import pytest
from unittest.mock import patch, MagicMock


def test_get_db_returns_connection(monkeypatch):
    monkeypatch.setenv("MOTHERDUCK_TOKEN", "fake-token")
    mock_conn = MagicMock()
    # Reset the module-level singleton and mock duckdb.connect
    import api.core.database as db_mod
    db_mod._connection = None  # reset singleton
    with patch("api.core.database.duckdb.connect", return_value=mock_conn):
        conn = db_mod.get_db()
        assert conn is mock_conn


def test_get_db_is_singleton(monkeypatch):
    monkeypatch.setenv("MOTHERDUCK_TOKEN", "fake-token")
    mock_conn = MagicMock()
    import api.core.database as db_mod
    db_mod._connection = None
    with patch("api.core.database.duckdb.connect", return_value=mock_conn):
        conn1 = db_mod.get_db()
        conn2 = db_mod.get_db()
    assert conn1 is conn2


def test_get_db_raises_if_token_empty():
    import api.core.database as db_mod
    mock_settings = MagicMock()
    mock_settings.motherduck_token = ""
    db_mod._connection = None
    with patch("api.core.database.get_settings", return_value=mock_settings):
        with pytest.raises(RuntimeError, match="MOTHERDUCK_TOKEN"):
            db_mod.get_db()
