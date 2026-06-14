import logging
import os
import duckdb
from api.core.config import get_settings

logger = logging.getLogger(__name__)

_connection: duckdb.DuckDBPyConnection | None = None
_LOCAL_DB = os.path.join(os.path.dirname(__file__), "..", "..", "health_screening.db")


def get_db() -> duckdb.DuckDBPyConnection:
    global _connection
    if _connection is not None:
        return _connection
    settings = get_settings()
    if settings.motherduck_token:
        try:
            _connection = duckdb.connect(
                f"md:health_screening?motherduck_token={settings.motherduck_token}"
            )
            logger.info("Connected to MotherDuck")
        except Exception as exc:
            logger.warning("MotherDuck unavailable (%s) — falling back to local DB", exc)
            _connection = duckdb.connect(os.path.abspath(_LOCAL_DB))
    else:
        _connection = duckdb.connect(os.path.abspath(_LOCAL_DB))
    _ensure_tables(_connection)
    return _connection


def _ensure_tables(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS enrollees (
            enrollee_id VARCHAR PRIMARY KEY,
            batch_id    VARCHAR,
            name        VARCHAR,
            age         INTEGER,
            gender      VARCHAR,
            systolic    DOUBLE,
            diastolic   DOUBLE,
            blood_glucose DOUBLE,
            bmi         DOUBLE,
            cholesterol DOUBLE,
            email       VARCHAR,
            phone       VARCHAR,
            company_name VARCHAR,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS klaire_analyses (
            enrollee_id  VARCHAR PRIMARY KEY,
            batch_id     VARCHAR,
            health_score INTEGER,
            urgency      VARCHAR,
            klaire_flags VARCHAR,
            next_steps   VARCHAR,
            analysed_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS report_meta (
            enrollee_id VARCHAR PRIMARY KEY,
            batch_id    VARCHAR,
            pdf_path    VARCHAR,
            b2_url      VARCHAR,
            email_sent  BOOLEAN DEFAULT FALSE,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
