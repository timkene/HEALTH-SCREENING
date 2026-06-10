# Health Screening API — Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI backend that replaces the existing Streamlit app — fixing all 6 critical bugs, powering Klaire via the Claude API, and exposing clean REST endpoints for the React staff portal (Plan B).

**Architecture:** Service-layer pattern: routers handle HTTP, services handle business logic, models define schemas. All credentials live in `.env` via Pydantic Settings. Async-first throughout — Celery handles bulk jobs, SSE streams Klaire's analysis.

**Tech Stack:** FastAPI · Pydantic v2 · anthropic SDK · ReportLab · duckdb + motherduck · boto3 + b2sdk · celery[redis] · httpx · pytest + pytest-asyncio

---

## Scope Note

This is Plan A — the full backend. Plan B covers the React staff portal. The backend produces working, independently testable software. Run the React portal against these endpoints once Plan A is complete.

---

## File Map

All new files live inside `health-api/` in the project root.

```
health-api/
├── api/
│   ├── routers/
│   │   ├── reports.py       — upload, generate, download endpoints
│   │   ├── klaire.py        — analyse, stream, doctor-brief endpoints
│   │   ├── email.py         — send individual + bulk endpoints
│   │   ├── storage.py       — Backblaze B2 upload + URL endpoints
│   │   └── jobs.py          — Celery job status endpoints
│   ├── services/
│   │   ├── analysis_service.py  — parse CSV/Excel, validate columns
│   │   ├── klaire_service.py    — Claude API calls (patient + clinician mode)
│   │   ├── report_service.py    — ReportLab PDF generation (individual + company)
│   │   ├── email_service.py     — Zoho OAuth + SMTP, thread-safe token cache
│   │   └── storage_service.py  — Backblaze B2 upload + signed URLs
│   ├── models/
│   │   ├── health_data.py   — input schemas (EnrolleeRow, BatchUpload)
│   │   └── responses.py     — output schemas (KlaireAnalysis, JobStatus, etc.)
│   └── core/
│       ├── config.py        — Pydantic Settings (all .env vars)
│       ├── database.py      — MotherDuck connection (singleton)
│       └── security.py      — X-API-Key dependency
├── workers/
│   └── tasks.py             — Celery task definitions
├── tests/
│   ├── conftest.py
│   ├── test_analysis_service.py
│   ├── test_klaire_service.py
│   ├── test_report_service.py
│   ├── test_email_service.py
│   ├── test_storage_service.py
│   └── test_routers.py
├── .env.example
├── pyproject.toml
└── main.py
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `health-api/pyproject.toml`
- Create: `health-api/.env.example`
- Create: `health-api/main.py`
- Create: `health-api/tests/conftest.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p health-api/api/routers health-api/api/services health-api/api/models health-api/api/core health-api/workers health-api/tests
touch health-api/api/__init__.py health-api/api/routers/__init__.py health-api/api/services/__init__.py health-api/api/models/__init__.py health-api/api/core/__init__.py health-api/workers/__init__.py
```

- [ ] **Step 2: Create `health-api/pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "health-api"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.29.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "anthropic>=0.28.0",
    "httpx>=0.27.0",
    "python-multipart>=0.0.9",
    "pandas>=2.0.3",
    "openpyxl>=3.1.2",
    "reportlab>=4.2.0",
    "duckdb>=1.3.2",
    "motherduck>=0.0.0",
    "boto3>=1.34.0",
    "b2sdk>=1.25.0",
    "celery[redis]>=5.3.1",
    "python-dotenv>=1.0.0",
    "qrcode[pil]>=7.4.2",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "httpx>=0.27.0",
    "black>=24.4.0",
    "ruff>=0.4.0",
]
```

- [ ] **Step 3: Create `health-api/.env.example`**

```ini
# API
API_KEY=change-me-in-production

# Anthropic (Klaire)
ANTHROPIC_API_KEY=sk-ant-...

# Zoho Mail OAuth
ZOHO_CLIENT_ID=
ZOHO_CLIENT_SECRET=
ZOHO_REFRESH_TOKEN=
ZOHO_ACCOUNT_ID=
ZOHO_FROM_EMAIL=hello@clearlinehmo.com

# SMTP fallback
SMTP_SERVER=smtp.zoho.com
SMTP_PORT=587
SMTP_USERNAME=hello@clearlinehmo.com
SMTP_PASSWORD=

# MotherDuck
MOTHERDUCK_TOKEN=

# Backblaze B2
BACKBLAZE_ACCESS_KEY_ID=
BACKBLAZE_SECRET_ACCESS_KEY=
BACKBLAZE_BUCKET_NAME=
BACKBLAZE_ENDPOINT_URL=https://s3.us-west-004.backblazeb2.com

# Telemedicine alerts
TELE_ALERT_EMAIL=telemedicine@clearlinehmo.com

# Celery
REDIS_URL=redis://localhost:6379/0

# Environment
ENVIRONMENT=development
```

- [ ] **Step 4: Copy `.env.example` to `.env` and fill in real values**

```bash
cp health-api/.env.example health-api/.env
# Now edit health-api/.env with actual credentials from the existing streamlit_health_app.py
# ZOHO_CLIENT_ID = value of CLIENT_ID in streamlit_health_app.py line 22
# ZOHO_CLIENT_SECRET = value of CLIENT_SECRET line 23
# ZOHO_REFRESH_TOKEN = value of REFRESH_TOKEN line 24
# ZOHO_ACCOUNT_ID = value of ACCOUNT_ID line 25
# MOTHERDUCK_TOKEN = value of MOTHERDUCK_TOKEN line 34
# (Backblaze values from backblaze_credentials.env)
```

- [ ] **Step 5: Create `health-api/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import reports, klaire, email, storage, jobs

app = FastAPI(title="Clearline HMO Health Screening API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(klaire.router, prefix="/api", tags=["klaire"])
app.include_router(email.router, prefix="/api/email", tags=["email"])
app.include_router(storage.router, prefix="/api/storage", tags=["storage"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}
```

- [ ] **Step 6: Create `health-api/tests/conftest.py`**

```python
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
```

- [ ] **Step 7: Install dependencies**

```bash
cd health-api
pip install -e ".[dev]"
```

- [ ] **Step 8: Verify the server starts**

```bash
cd health-api
uvicorn main:app --reload
# Expected: "Application startup complete." — visit http://localhost:8000/health → {"status":"ok"}
```

- [ ] **Step 9: Commit**

```bash
git add health-api/
git commit -m "feat: scaffold health-api FastAPI project"
```

---

## Task 2: Pydantic Settings — Secrets Management

**Files:**
- Create: `health-api/api/core/config.py`
- Create: `health-api/tests/test_config.py`

- [ ] **Step 1: Write failing test**

```python
# health-api/tests/test_config.py
import pytest
from pydantic import ValidationError


def test_settings_loads_all_required_vars(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("ZOHO_CLIENT_ID", "zid")
    monkeypatch.setenv("ZOHO_CLIENT_SECRET", "zsec")
    monkeypatch.setenv("ZOHO_REFRESH_TOKEN", "zrt")
    monkeypatch.setenv("ZOHO_ACCOUNT_ID", "zacc")
    monkeypatch.setenv("ZOHO_FROM_EMAIL", "hello@clearlinehmo.com")
    monkeypatch.setenv("SMTP_SERVER", "smtp.zoho.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "hello@clearlinehmo.com")
    monkeypatch.setenv("SMTP_PASSWORD", "pass")
    monkeypatch.setenv("MOTHERDUCK_TOKEN", "token")
    monkeypatch.setenv("BACKBLAZE_ACCESS_KEY_ID", "bid")
    monkeypatch.setenv("BACKBLAZE_SECRET_ACCESS_KEY", "bsec")
    monkeypatch.setenv("BACKBLAZE_BUCKET_NAME", "bucket")
    monkeypatch.setenv("BACKBLAZE_ENDPOINT_URL", "https://s3.us-west-004.backblazeb2.com")
    monkeypatch.setenv("TELE_ALERT_EMAIL", "tele@clearlinehmo.com")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

    # Import fresh instance inside the test after env is set
    import importlib
    import api.core.config as cfg_module
    importlib.reload(cfg_module)
    settings = cfg_module.get_settings()

    assert settings.api_key == "test-key"
    assert settings.anthropic_api_key == "sk-ant-test"
    assert settings.motherduck_token == "token"


def test_settings_raises_if_api_key_missing(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    import importlib
    import api.core.config as cfg_module
    with pytest.raises((ValidationError, Exception)):
        importlib.reload(cfg_module)
        cfg_module.get_settings()
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd health-api
pytest tests/test_config.py -v
# Expected: FAIL — "ModuleNotFoundError: No module named 'api.core.config'"
```

- [ ] **Step 3: Create `health-api/api/core/config.py`**

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    api_key: str
    anthropic_api_key: str

    zoho_client_id: str
    zoho_client_secret: str
    zoho_refresh_token: str
    zoho_account_id: str
    zoho_from_email: str

    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str

    motherduck_token: str

    backblaze_access_key_id: str
    backblaze_secret_access_key: str
    backblaze_bucket_name: str
    backblaze_endpoint_url: str

    tele_alert_email: str
    redis_url: str = "redis://localhost:6379/0"
    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Run test — expect PASS**

```bash
pytest tests/test_config.py -v
# Expected: PASS
```

- [ ] **Step 5: Commit**

```bash
git add health-api/api/core/config.py health-api/tests/test_config.py
git commit -m "feat: add Pydantic Settings — all secrets in .env"
```

---

## Task 3: API Key Authentication

**Files:**
- Create: `health-api/api/core/security.py`
- Modify: `health-api/tests/conftest.py`

- [ ] **Step 1: Write failing test**

```python
# Add to health-api/tests/test_routers.py (create file)
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check_no_auth_required():
    response = client.get("/health")
    assert response.status_code == 200


def test_protected_endpoint_rejects_missing_key():
    response = client.get("/api/reports/batch/test-batch")
    assert response.status_code == 403


def test_protected_endpoint_rejects_wrong_key():
    response = client.get(
        "/api/reports/batch/test-batch",
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 403
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
pytest tests/test_routers.py::test_protected_endpoint_rejects_missing_key -v
# Expected: FAIL — route doesn't exist yet, but confirms auth logic is needed
```

- [ ] **Step 3: Create `health-api/api/core/security.py`**

```python
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from api.core.config import get_settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str | None = Security(_api_key_header)) -> str:
    settings = get_settings()
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )
    return api_key
```

- [ ] **Step 4: Add a stub reports router so the auth test has a route to hit**

```python
# health-api/api/routers/reports.py  (stub — full implementation in Task 9)
from fastapi import APIRouter, Depends
from api.core.security import require_api_key

router = APIRouter()


@router.get("/batch/{batch_id}")
async def get_batch(_: str = Depends(require_api_key), batch_id: str = ""):
    return {"batch_id": batch_id, "reports": []}
```

Create stub files for the other routers so `main.py` can import them:

```python
# health-api/api/routers/klaire.py
from fastapi import APIRouter
router = APIRouter()

# health-api/api/routers/email.py
from fastapi import APIRouter
router = APIRouter()

# health-api/api/routers/storage.py
from fastapi import APIRouter
router = APIRouter()

# health-api/api/routers/jobs.py
from fastapi import APIRouter
router = APIRouter()
```

- [ ] **Step 5: Run test — expect PASS**

```bash
pytest tests/test_routers.py -v
# Expected: PASS (all 3 auth tests)
```

- [ ] **Step 6: Commit**

```bash
git add health-api/api/core/security.py health-api/api/routers/ health-api/tests/test_routers.py
git commit -m "feat: add X-API-Key authentication"
```

---

## Task 4: Data Models

**Files:**
- Create: `health-api/api/models/health_data.py`
- Create: `health-api/api/models/responses.py`
- Create: `health-api/tests/test_models.py`

- [ ] **Step 1: Write failing tests**

```python
# health-api/tests/test_models.py
import pytest
from pydantic import ValidationError
from api.models.health_data import EnrolleeRow, BatchUpload


def test_enrollee_row_requires_core_fields():
    row = EnrolleeRow(
        enrollee_id="CL_ARIK_003",
        name="Chukwuemeka Obi",
        age=44,
        gender="M",
        systolic=142,
        diastolic=88,
    )
    assert row.enrollee_id == "CL_ARIK_003"
    assert row.bmi is None  # optional fields default to None


def test_enrollee_row_rejects_negative_age():
    with pytest.raises(ValidationError):
        EnrolleeRow(
            enrollee_id="X",
            name="Test",
            age=-1,
            gender="M",
            systolic=120,
            diastolic=80,
        )


def test_batch_upload_holds_multiple_rows():
    rows = [
        EnrolleeRow(enrollee_id=f"ID_{i}", name=f"Person {i}", age=30, gender="F",
                    systolic=120, diastolic=80)
        for i in range(3)
    ]
    batch = BatchUpload(batch_id="batch-001", company_name="Arik Air", rows=rows)
    assert len(batch.rows) == 3
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
pytest tests/test_models.py -v
# Expected: FAIL — module not found
```

- [ ] **Step 3: Create `health-api/api/models/health_data.py`**

```python
from __future__ import annotations
from pydantic import BaseModel, Field


class EnrolleeRow(BaseModel):
    enrollee_id: str
    name: str
    age: int = Field(..., ge=0, le=120)
    gender: str  # "M" or "F"
    systolic: float | None = None
    diastolic: float | None = None
    blood_glucose: float | None = None
    bmi: float | None = None
    cholesterol: float | None = None
    urine_glucose: str | None = None
    urine_protein: str | None = None
    email: str | None = None
    phone: str | None = None
    company_name: str | None = None


class BatchUpload(BaseModel):
    batch_id: str
    company_name: str
    rows: list[EnrolleeRow]
```

- [ ] **Step 4: Create `health-api/api/models/responses.py`**

```python
from __future__ import annotations
from pydantic import BaseModel
from enum import Enum


class UrgencyLevel(str, Enum):
    routine = "routine"
    watch = "watch"
    urgent = "urgent"
    critical = "critical"


class MetricScore(BaseModel):
    metric: str
    score: int  # 0-100
    flag: str | None = None


class KlaireAnalysis(BaseModel):
    enrollee_id: str
    health_score: int  # 0-100
    urgency: UrgencyLevel
    metric_scores: list[MetricScore]
    dominant_risk: str | None = None
    next_steps: list[str]  # exactly 3
    klaire_flags: str  # clinical summary for doctor brief


class DoctorBrief(BaseModel):
    enrollee_id: str
    name: str
    age: int
    gender: str
    screening_date: str
    urgency: UrgencyLevel
    health_score: int
    vitals: dict
    klaire_flags: str
    recommended_focus: list[str]


class JobStatus(BaseModel):
    job_id: str
    status: str  # pending | running | done | failed
    total: int = 0
    completed: int = 0
    failed_ids: list[str] = []


class ReportMeta(BaseModel):
    enrollee_id: str
    batch_id: str
    pdf_path: str | None = None
    b2_url: str | None = None
    urgency: UrgencyLevel | None = None
    email_sent: bool = False
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
pytest tests/test_models.py -v
# Expected: PASS
```

- [ ] **Step 6: Commit**

```bash
git add health-api/api/models/ health-api/tests/test_models.py
git commit -m "feat: add Pydantic data models for health data and responses"
```

---

## Task 5: MotherDuck Database Connection

**Files:**
- Create: `health-api/api/core/database.py`
- Create: `health-api/tests/test_database.py`

- [ ] **Step 1: Write failing test**

```python
# health-api/tests/test_database.py
import pytest
from unittest.mock import patch, MagicMock


def test_get_db_returns_connection(monkeypatch):
    monkeypatch.setenv("MOTHERDUCK_TOKEN", "fake-token")
    mock_conn = MagicMock()
    with patch("duckdb.connect", return_value=mock_conn):
        from api.core.database import get_db
        conn = get_db()
        assert conn is mock_conn


def test_get_db_raises_if_token_missing(monkeypatch):
    monkeypatch.delenv("MOTHERDUCK_TOKEN", raising=False)
    import importlib, api.core.database as db_mod
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(Exception, match="MOTHERDUCK_TOKEN"):
            importlib.reload(db_mod)
            db_mod.get_db()
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
pytest tests/test_database.py -v
# Expected: FAIL
```

- [ ] **Step 3: Create `health-api/api/core/database.py`**

```python
import duckdb
from api.core.config import get_settings

_connection: duckdb.DuckDBPyConnection | None = None


def get_db() -> duckdb.DuckDBPyConnection:
    global _connection
    if _connection is not None:
        return _connection
    settings = get_settings()
    if not settings.motherduck_token:
        raise RuntimeError("MOTHERDUCK_TOKEN is required")
    _connection = duckdb.connect(
        f"md:health_screening?motherduck_token={settings.motherduck_token}"
    )
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
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_database.py -v
# Expected: PASS
```

- [ ] **Step 5: Commit**

```bash
git add health-api/api/core/database.py health-api/tests/test_database.py
git commit -m "feat: add MotherDuck database connection with table bootstrap"
```

---

## Task 6: Analysis Service — Parse & Validate CSV/Excel

**Files:**
- Create: `health-api/api/services/analysis_service.py`
- Create: `health-api/tests/test_analysis_service.py`

- [ ] **Step 1: Write failing tests**

```python
# health-api/tests/test_analysis_service.py
import io
import pandas as pd
import pytest
from api.services.analysis_service import parse_upload, REQUIRED_COLUMNS, ParseError


def _make_csv(rows: list[dict]) -> bytes:
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode()


VALID_ROW = {
    "ENROLLEE ID": "CL_001",
    "NAME": "Ada Obi",
    "AGE": 35,
    "GENDER": "F",
    "SYSTOLIC": 118,
    "DIASTOLIC": 76,
    "BLOOD GLUCOSE": 90,
    "BMI": 22.1,
}


def test_parse_valid_csv_returns_batch():
    csv_bytes = _make_csv([VALID_ROW])
    batch = parse_upload(csv_bytes, "test.csv", "Arik Air")
    assert len(batch.rows) == 1
    assert batch.rows[0].enrollee_id == "CL_001"
    assert batch.rows[0].name == "Ada Obi"


def test_parse_missing_required_column_raises():
    bad = {k: v for k, v in VALID_ROW.items() if k != "ENROLLEE ID"}
    csv_bytes = _make_csv([bad])
    with pytest.raises(ParseError, match="ENROLLEE ID"):
        parse_upload(csv_bytes, "test.csv", "Arik Air")


def test_parse_xlsx_is_supported():
    df = pd.DataFrame([VALID_ROW])
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    batch = parse_upload(buf.getvalue(), "test.xlsx", "Arik Air")
    assert len(batch.rows) == 1


def test_numeric_columns_coerced():
    row = {**VALID_ROW, "SYSTOLIC": "140", "DIASTOLIC": "90"}
    csv_bytes = _make_csv([row])
    batch = parse_upload(csv_bytes, "test.csv", "Arik Air")
    assert batch.rows[0].systolic == 140.0
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_analysis_service.py -v
# Expected: FAIL
```

- [ ] **Step 3: Create `health-api/api/services/analysis_service.py`**

```python
from __future__ import annotations
import io
import uuid
import pandas as pd
from api.models.health_data import EnrolleeRow, BatchUpload

REQUIRED_COLUMNS = {"ENROLLEE ID", "NAME", "AGE", "GENDER", "SYSTOLIC", "DIASTOLIC"}
NUMERIC_COLUMNS = ["AGE", "SYSTOLIC", "DIASTOLIC", "BLOOD GLUCOSE", "BMI", "CHOLESTEROL"]

COLUMN_MAP = {
    "ENROLLEE ID": "enrollee_id",
    "NAME": "name",
    "AGE": "age",
    "GENDER": "gender",
    "SYSTOLIC": "systolic",
    "DIASTOLIC": "diastolic",
    "BLOOD GLUCOSE": "blood_glucose",
    "BMI": "bmi",
    "CHOLESTEROL": "cholesterol",
    "GLUCOSE": "urine_glucose",
    "PROTEIN": "urine_protein",
    "EMAIL": "email",
    "PHONE": "phone",
}


class ParseError(ValueError):
    pass


def parse_upload(file_bytes: bytes, filename: str, company_name: str) -> BatchUpload:
    df = _read_file(file_bytes, filename)
    df.columns = df.columns.str.strip().str.upper()

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ParseError(f"Missing required columns: {', '.join(sorted(missing))}")

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    rows = [_row_to_model(r, company_name) for _, r in df.iterrows()]
    return BatchUpload(
        batch_id=str(uuid.uuid4()),
        company_name=company_name,
        rows=rows,
    )


def _read_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    buf = io.BytesIO(file_bytes)
    if filename.endswith(".xlsx") or filename.endswith(".xls"):
        return pd.read_excel(buf)
    return pd.read_csv(buf)


def _row_to_model(row: pd.Series, company_name: str) -> EnrolleeRow:
    kwargs: dict = {"company_name": company_name}
    for csv_col, field in COLUMN_MAP.items():
        val = row.get(csv_col)
        if pd.notna(val):
            kwargs[field] = val
    return EnrolleeRow(**kwargs)
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_analysis_service.py -v
# Expected: PASS
```

- [ ] **Step 5: Commit**

```bash
git add health-api/api/services/analysis_service.py health-api/tests/test_analysis_service.py
git commit -m "feat: add analysis_service — parse and validate CSV/Excel uploads"
```

---

## Task 7: Klaire AI Service

**Files:**
- Create: `health-api/api/services/klaire_service.py`
- Create: `health-api/tests/test_klaire_service.py`

- [ ] **Step 1: Write failing tests**

```python
# health-api/tests/test_klaire_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from api.models.health_data import EnrolleeRow
from api.models.responses import UrgencyLevel
from api.services.klaire_service import build_patient_prompt, build_clinician_prompt, parse_analysis_json


def test_patient_prompt_includes_name_and_vitals():
    row = EnrolleeRow(
        enrollee_id="CL_001", name="Ada Obi", age=35, gender="F",
        systolic=118, diastolic=76, blood_glucose=90, bmi=22.1
    )
    prompt = build_patient_prompt(row)
    assert "Ada Obi" in prompt
    assert "35" in prompt
    assert "118" in prompt


def test_clinician_prompt_is_concise_instruction():
    row = EnrolleeRow(
        enrollee_id="CL_001", name="Ada Obi", age=35, gender="F",
        systolic=118, diastolic=76
    )
    prompt = build_clinician_prompt(row)
    assert "clinical" in prompt.lower() or "brief" in prompt.lower()


def test_parse_analysis_json_extracts_score():
    raw = """
    {
      "health_score": 78,
      "urgency": "routine",
      "metric_scores": [{"metric": "bp", "score": 80, "flag": null}],
      "dominant_risk": null,
      "next_steps": ["Walk 30 min daily", "Reduce salt", "Check BP monthly"],
      "klaire_flags": "BP normal for age. No concerns."
    }
    """
    analysis = parse_analysis_json("CL_001", raw)
    assert analysis.health_score == 78
    assert analysis.urgency == UrgencyLevel.routine
    assert len(analysis.next_steps) == 3


def test_parse_analysis_json_handles_embedded_json():
    raw = """Here is the analysis:
    ```json
    {"health_score": 65, "urgency": "watch", "metric_scores": [],
     "dominant_risk": "BP", "next_steps": ["a", "b", "c"],
     "klaire_flags": "BP elevated."}
    ```
    """
    analysis = parse_analysis_json("CL_001", raw)
    assert analysis.urgency == UrgencyLevel.watch
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_klaire_service.py -v
```

- [ ] **Step 3: Create `health-api/api/services/klaire_service.py`**

```python
from __future__ import annotations
import json
import re
from typing import AsyncIterator
import anthropic
from api.core.config import get_settings
from api.models.health_data import EnrolleeRow
from api.models.responses import KlaireAnalysis, MetricScore, UrgencyLevel

_LAYER_1_IDENTITY = """You are Klaire, the AI health companion for Clearline HMO. \
You are warm, direct, and genuinely care about the people you talk to. \
You explain health results the way a knowledgeable doctor-friend would — honest and human, never cold. \
You always end with hope and clear next steps. Your name is Klaire, and the people reading your \
reports know and trust you."""

_LAYER_2_TONE = """Use short paragraphs (2-3 sentences each). \
Explain any medical term in plain language immediately after using it. \
Celebrate small wins and healthy readings. \
Always provide exactly 3 actionable next steps at the end under the heading "Your 3 next steps:". \
Never catastrophise. Use the person's first name once at the very start. \
Use a maximum of 2 emojis in the entire response."""

_LAYER_3_GUARDRAILS = """You are a health screening interpretation tool, not a diagnostic system. \
You do not diagnose diseases. \
For any reading in a critical range (systolic BP ≥ 180, diastolic BP ≥ 120, fasting glucose ≥ 400, \
or BMI ≥ 40), use urgent language and say: "Please speak to a doctor within 24 hours." \
Always end your response with this exact line on its own paragraph: \
"⚕️ Clearline HMO Disclaimer: This report is a health screening summary, not a medical diagnosis. \
Please consult a qualified healthcare professional for medical advice, diagnosis, or treatment." """

PATIENT_SYSTEM_PROMPT = "\n\n".join([_LAYER_1_IDENTITY, _LAYER_2_TONE, _LAYER_3_GUARDRAILS])

CLINICIAN_SYSTEM_PROMPT = """You are a clinical summary assistant for Clearline HMO doctors. \
Given a patient's health screening data, produce a concise clinical brief in 100 words or fewer. \
Structure: [Patient profile] | [Key findings] | [Flags] | [Recommended focus]. \
Use clinical language. No emojis. No disclaimers. No patient-facing language."""

ANALYSIS_SYSTEM_PROMPT = (
    _LAYER_1_IDENTITY + "\n\n" + _LAYER_3_GUARDRAILS + """

Return a JSON object — and only JSON — with this exact shape:
{
  "health_score": <integer 0-100>,
  "urgency": <"routine"|"watch"|"urgent"|"critical">,
  "metric_scores": [{"metric": "<name>", "score": <int>, "flag": <str|null>}],
  "dominant_risk": <str|null>,
  "next_steps": [<str>, <str>, <str>],
  "klaire_flags": "<one paragraph clinical summary>"
}
"""
)


def build_patient_prompt(row: EnrolleeRow) -> str:
    first_name = row.name.split()[0]
    parts = [
        f"Patient: {row.name} (first name: {first_name})",
        f"Age: {row.age}, Gender: {row.gender}",
    ]
    if row.systolic and row.diastolic:
        parts.append(f"Blood Pressure: {row.systolic}/{row.diastolic} mmHg")
    if row.blood_glucose:
        parts.append(f"Fasting Blood Glucose: {row.blood_glucose} mg/dL")
    if row.bmi:
        parts.append(f"BMI: {row.bmi}")
    if row.cholesterol:
        parts.append(f"Total Cholesterol: {row.cholesterol} mg/dL")
    if row.urine_glucose:
        parts.append(f"Urine Glucose: {row.urine_glucose}")
    if row.urine_protein:
        parts.append(f"Urine Protein: {row.urine_protein}")
    parts.append(
        "\nWrite a warm, personal health report for this person based on the above readings."
    )
    return "\n".join(parts)


def build_clinician_prompt(row: EnrolleeRow) -> str:
    parts = [
        f"Patient: {row.name}, {row.age}{row.gender}.",
        f"BP: {row.systolic}/{row.diastolic} mmHg." if row.systolic else "",
        f"Glucose: {row.blood_glucose} mg/dL." if row.blood_glucose else "",
        f"BMI: {row.bmi}." if row.bmi else "",
        f"Cholesterol: {row.cholesterol} mg/dL." if row.cholesterol else "",
        "Produce a clinical brief for the attending doctor.",
    ]
    return " ".join(p for p in parts if p)


def parse_analysis_json(enrollee_id: str, raw: str) -> KlaireAnalysis:
    match = re.search(r"```json\s*(\{.*?\})\s*```", raw, re.DOTALL)
    json_str = match.group(1) if match else raw.strip()
    data = json.loads(json_str)
    return KlaireAnalysis(
        enrollee_id=enrollee_id,
        health_score=data["health_score"],
        urgency=UrgencyLevel(data["urgency"]),
        metric_scores=[MetricScore(**m) for m in data.get("metric_scores", [])],
        dominant_risk=data.get("dominant_risk"),
        next_steps=data["next_steps"],
        klaire_flags=data["klaire_flags"],
    )


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=get_settings().anthropic_api_key)


def analyse_enrollee(row: EnrolleeRow) -> KlaireAnalysis:
    """Non-streaming call — returns structured analysis for PDF embedding."""
    client = _get_client()
    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        thinking={"type": "adaptive"},
        system=ANALYSIS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_patient_prompt(row)}],
    )
    raw = next(b.text for b in message.content if b.type == "text")
    return parse_analysis_json(row.enrollee_id, raw)


async def stream_patient_narrative(row: EnrolleeRow) -> AsyncIterator[str]:
    """SSE streaming — yields text chunks for the staff preview panel."""
    client = anthropic.AsyncAnthropic(api_key=get_settings().anthropic_api_key)
    async with client.messages.stream(
        model="claude-opus-4-8",
        max_tokens=2048,
        thinking={"type": "adaptive"},
        system=PATIENT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_patient_prompt(row)}],
    ) as stream:
        async for text in stream.text_stream:
            yield text


def generate_doctor_brief(row: EnrolleeRow, analysis: KlaireAnalysis) -> str:
    """Returns a short clinical summary string."""
    client = _get_client()
    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=256,
        system=CLINICIAN_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_clinician_prompt(row)}],
    )
    return next(b.text for b in message.content if b.type == "text")
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_klaire_service.py -v
# Expected: PASS (all 4 tests — no API calls made, only pure functions tested)
```

- [ ] **Step 5: Commit**

```bash
git add health-api/api/services/klaire_service.py health-api/tests/test_klaire_service.py
git commit -m "feat: add Klaire AI service — patient mode, clinician mode, SSE streaming"
```

---

## Task 8: Klaire Router

**Files:**
- Modify: `health-api/api/routers/klaire.py`
- Modify: `health-api/tests/test_routers.py`

- [ ] **Step 1: Write failing tests**

Add to `health-api/tests/test_routers.py`:

```python
from unittest.mock import patch, MagicMock
from api.models.responses import KlaireAnalysis, UrgencyLevel, MetricScore


def test_analyse_endpoint_returns_job_id(client):
    mock_analysis = KlaireAnalysis(
        enrollee_id="CL_001",
        health_score=74,
        urgency=UrgencyLevel.watch,
        metric_scores=[],
        next_steps=["a", "b", "c"],
        klaire_flags="BP elevated.",
    )
    with patch("api.routers.klaire.analyse_enrollee", return_value=mock_analysis), \
         patch("api.routers.klaire._get_enrollee_row", return_value=MagicMock()):
        resp = client.post(
            "/api/klaire/analyse/CL_001",
            headers={"X-API-Key": "test-key"},
        )
    assert resp.status_code == 200
    assert "health_score" in resp.json()
```

Update `health-api/tests/conftest.py` to expose an `API_KEY=test-key` env:

```python
import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.environ.setdefault("ZOHO_CLIENT_ID", "z")
os.environ.setdefault("ZOHO_CLIENT_SECRET", "z")
os.environ.setdefault("ZOHO_REFRESH_TOKEN", "z")
os.environ.setdefault("ZOHO_ACCOUNT_ID", "z")
os.environ.setdefault("ZOHO_FROM_EMAIL", "hello@test.com")
os.environ.setdefault("SMTP_SERVER", "smtp.test.com")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("SMTP_USERNAME", "u")
os.environ.setdefault("SMTP_PASSWORD", "p")
os.environ.setdefault("MOTHERDUCK_TOKEN", "fake")
os.environ.setdefault("BACKBLAZE_ACCESS_KEY_ID", "b")
os.environ.setdefault("BACKBLAZE_SECRET_ACCESS_KEY", "b")
os.environ.setdefault("BACKBLAZE_BUCKET_NAME", "bucket")
os.environ.setdefault("BACKBLAZE_ENDPOINT_URL", "https://s3.test.com")
os.environ.setdefault("TELE_ALERT_EMAIL", "tele@test.com")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


@pytest.fixture
def client() -> TestClient:
    from main import app
    return TestClient(app)
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
pytest tests/test_routers.py::test_analyse_endpoint_returns_job_id -v
```

- [ ] **Step 3: Implement `health-api/api/routers/klaire.py`**

```python
from __future__ import annotations
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from api.core.security import require_api_key
from api.core.database import get_db
from api.models.health_data import EnrolleeRow
from api.models.responses import KlaireAnalysis, DoctorBrief, UrgencyLevel
from api.services.klaire_service import (
    analyse_enrollee,
    stream_patient_narrative,
    generate_doctor_brief,
)

router = APIRouter()


def _get_enrollee_row(enrollee_id: str) -> EnrolleeRow:
    conn = get_db()
    result = conn.execute(
        "SELECT * FROM enrollees WHERE enrollee_id = ?", [enrollee_id]
    ).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail=f"Enrollee {enrollee_id} not found")
    cols = [d[0] for d in conn.description]
    data = dict(zip(cols, result))
    return EnrolleeRow(**data)


@router.post("/klaire/analyse/{enrollee_id}", response_model=KlaireAnalysis)
async def analyse(enrollee_id: str, _: str = Depends(require_api_key)) -> KlaireAnalysis:
    row = _get_enrollee_row(enrollee_id)
    analysis = analyse_enrollee(row)
    conn = get_db()
    conn.execute("""
        INSERT OR REPLACE INTO klaire_analyses
          (enrollee_id, health_score, urgency, klaire_flags, next_steps)
        VALUES (?, ?, ?, ?, ?)
    """, [
        analysis.enrollee_id,
        analysis.health_score,
        analysis.urgency.value,
        analysis.klaire_flags,
        json.dumps(analysis.next_steps),
    ])
    return analysis


@router.get("/klaire/stream/{enrollee_id}")
async def stream(enrollee_id: str, _: str = Depends(require_api_key)) -> StreamingResponse:
    row = _get_enrollee_row(enrollee_id)

    async def event_generator():
        async for chunk in stream_patient_narrative(row):
            yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/enrollees/{enrollee_id}/doctor-brief", response_model=DoctorBrief)
async def doctor_brief(enrollee_id: str, _: str = Depends(require_api_key)) -> DoctorBrief:
    row = _get_enrollee_row(enrollee_id)
    conn = get_db()
    result = conn.execute(
        "SELECT health_score, urgency, klaire_flags FROM klaire_analyses WHERE enrollee_id = ?",
        [enrollee_id],
    ).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="No analysis found. Run /klaire/analyse first.")
    health_score, urgency_str, klaire_flags = result
    analysis_stub = type("A", (), {
        "health_score": health_score,
        "urgency": UrgencyLevel(urgency_str),
        "klaire_flags": klaire_flags,
    })()
    brief_text = generate_doctor_brief(row, analysis_stub)
    return DoctorBrief(
        enrollee_id=enrollee_id,
        name=row.name,
        age=row.age,
        gender=row.gender,
        screening_date="",
        urgency=UrgencyLevel(urgency_str),
        health_score=health_score,
        vitals={
            "bp_systolic": row.systolic,
            "bp_diastolic": row.diastolic,
            "bmi": row.bmi,
            "glucose": row.blood_glucose,
        },
        klaire_flags=brief_text,
        recommended_focus=[],
    )
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_routers.py -v
```

- [ ] **Step 5: Commit**

```bash
git add health-api/api/routers/klaire.py health-api/tests/
git commit -m "feat: add Klaire router — analyse, stream, doctor-brief endpoints"
```

---

## Task 9: Report Service — Individual PDF

**Files:**
- Create: `health-api/api/services/report_service.py`
- Create: `health-api/tests/test_report_service.py`

- [ ] **Step 1: Write failing tests**

```python
# health-api/tests/test_report_service.py
import os
import pytest
from api.models.health_data import EnrolleeRow
from api.models.responses import KlaireAnalysis, UrgencyLevel
from api.services.report_service import generate_individual_pdf, generate_company_pdf


SAMPLE_ROW = EnrolleeRow(
    enrollee_id="CL_001", name="Ada Obi", age=35, gender="F",
    systolic=118, diastolic=76, blood_glucose=90, bmi=22.1,
    email="ada@test.com", company_name="Arik Air",
)

SAMPLE_ANALYSIS = KlaireAnalysis(
    enrollee_id="CL_001",
    health_score=82,
    urgency=UrgencyLevel.routine,
    metric_scores=[],
    next_steps=["Walk daily", "Drink water", "Sleep 8hrs"],
    klaire_flags="All readings normal for age and gender.",
)


def test_generate_individual_pdf_creates_file(tmp_path):
    out_path = generate_individual_pdf(SAMPLE_ROW, SAMPLE_ANALYSIS, str(tmp_path))
    assert os.path.exists(out_path)
    assert out_path.endswith(".pdf")
    assert os.path.getsize(out_path) > 1000


def test_generate_individual_pdf_uses_unique_path(tmp_path):
    path1 = generate_individual_pdf(SAMPLE_ROW, SAMPLE_ANALYSIS, str(tmp_path))
    path2 = generate_individual_pdf(SAMPLE_ROW, SAMPLE_ANALYSIS, str(tmp_path))
    assert path1 != path2  # UUID-keyed — no collision


def test_generate_company_pdf_creates_file(tmp_path):
    rows = [SAMPLE_ROW]
    analyses = [SAMPLE_ANALYSIS]
    out_path = generate_company_pdf("Arik Air", rows, analyses, str(tmp_path))
    assert os.path.exists(out_path)
    assert out_path.endswith(".pdf")
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_report_service.py -v
```

- [ ] **Step 3: Create `health-api/api/services/report_service.py`**

```python
from __future__ import annotations
import os
import uuid
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.colors import HexColor
from api.models.health_data import EnrolleeRow
from api.models.responses import KlaireAnalysis, UrgencyLevel

_URGENCY_COLOURS = {
    UrgencyLevel.routine: HexColor("#00b894"),
    UrgencyLevel.watch: HexColor("#fdcb6e"),
    UrgencyLevel.urgent: HexColor("#e17055"),
    UrgencyLevel.critical: HexColor("#d63031"),
}

_DISCLAIMER = (
    "⚕️ Clearline HMO Disclaimer: This report is a health screening summary, "
    "not a medical diagnosis. Please consult a qualified healthcare professional "
    "for medical advice, diagnosis, or treatment."
)

_TELE_ROUTINE = (
    "Your Clearline doctors are available for consultations on the Clearline mobile app."
)
_TELE_WATCH = (
    "Your reading is worth a conversation with a doctor. "
    "Reach out through the Clearline mobile app — it's free."
)
_TELE_CRITICAL = "A Clearline doctor will be in touch with you soon."


def generate_individual_pdf(
    row: EnrolleeRow,
    analysis: KlaireAnalysis,
    output_dir: str,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{row.enrollee_id}_{uuid.uuid4().hex[:8]}.pdf"
    out_path = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(out_path, pagesize=letter,
                            leftMargin=inch, rightMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(row.name, ParagraphStyle(
        "Title", parent=styles["Title"], fontSize=26, spaceAfter=6)))
    story.append(Paragraph(
        f"Enrollee ID: {row.enrollee_id} · {row.company_name or ''} · "
        f"Generated: {datetime.now().strftime('%B %d, %Y')}",
        ParagraphStyle("Sub", parent=styles["Normal"], fontSize=11, spaceAfter=20)))

    # Health score banner
    urgency_hex = _URGENCY_COLOURS.get(analysis.urgency, HexColor("#00b894"))
    score_data = [[
        Paragraph(f"<b>Health Score: {analysis.health_score}/100</b>",
                  ParagraphStyle("Score", parent=styles["Normal"], fontSize=16, textColor=colors.white)),
        Paragraph(f"<b>{analysis.urgency.value.upper()}</b>",
                  ParagraphStyle("Urg", parent=styles["Normal"], fontSize=14, textColor=colors.white)),
    ]]
    score_table = Table(score_data, colWidths=[4.5*inch, 2*inch])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), urgency_hex),
        ("PADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 16))

    # Vitals table
    vitals = [["Metric", "Value"]]
    if row.systolic and row.diastolic:
        vitals.append(["Blood Pressure", f"{row.systolic}/{row.diastolic} mmHg"])
    if row.blood_glucose:
        vitals.append(["Fasting Blood Glucose", f"{row.blood_glucose} mg/dL"])
    if row.bmi:
        vitals.append(["BMI", str(row.bmi)])
    if row.cholesterol:
        vitals.append(["Total Cholesterol", f"{row.cholesterol} mg/dL"])

    if len(vitals) > 1:
        t = Table(vitals, colWidths=[3*inch, 3.5*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2d3436")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f5f5f5"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 16))

    # Klaire's analysis (next_steps)
    story.append(Paragraph("Klaire's Analysis", styles["Heading2"]))
    for step in analysis.next_steps:
        story.append(Paragraph(f"• {step}", styles["Normal"]))
    story.append(Spacer(1, 16))

    # Telemedicine section
    story.append(Paragraph("Talk to a Clearline Doctor", styles["Heading2"]))
    if analysis.urgency == UrgencyLevel.critical:
        tele_text = _TELE_CRITICAL
    elif analysis.urgency in (UrgencyLevel.watch, UrgencyLevel.urgent):
        tele_text = _TELE_WATCH
    else:
        tele_text = _TELE_ROUTINE
    story.append(Paragraph(tele_text, styles["Normal"]))
    story.append(Spacer(1, 20))

    # Disclaimer
    story.append(Paragraph(_DISCLAIMER,
                            ParagraphStyle("Disc", parent=styles["Normal"],
                                           fontSize=9, textColor=colors.grey)))

    doc.build(story)
    return out_path


def generate_company_pdf(
    company_name: str,
    rows: list[EnrolleeRow],
    analyses: list[KlaireAnalysis],
    output_dir: str,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"company_{company_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.pdf"
    out_path = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(out_path, pagesize=letter,
                            leftMargin=inch, rightMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"{company_name} — Health Screening Report",
                            ParagraphStyle("T", parent=styles["Title"], fontSize=22)))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y')} · {len(rows)} enrollees screened",
        styles["Normal"]))
    story.append(Spacer(1, 16))

    if analyses:
        avg_score = int(sum(a.health_score for a in analyses) / len(analyses))
        counts = {u: sum(1 for a in analyses if a.urgency == u) for u in UrgencyLevel}
        summary = [
            ["Metric", "Value"],
            ["Average Health Score", f"{avg_score}/100"],
            ["Routine", str(counts[UrgencyLevel.routine])],
            ["Watch", str(counts[UrgencyLevel.watch])],
            ["Urgent", str(counts[UrgencyLevel.urgent])],
            ["Critical", str(counts[UrgencyLevel.critical])],
        ]
        t = Table(summary, colWidths=[3*inch, 3.5*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2d3436")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f5f5f5"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(t)

    doc.build(story)
    return out_path
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_report_service.py -v
# Expected: PASS — actual PDF files created in tmp_path
```

- [ ] **Step 5: Commit**

```bash
git add health-api/api/services/report_service.py health-api/tests/test_report_service.py
git commit -m "feat: add report_service — individual and company PDF generation with UUID isolation"
```

---

## Task 10: Reports Router

**Files:**
- Modify: `health-api/api/routers/reports.py`

- [ ] **Step 1: Implement full reports router**

```python
# health-api/api/routers/reports.py
from __future__ import annotations
import os
import uuid
import tempfile
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from api.core.security import require_api_key
from api.core.database import get_db
from api.models.health_data import BatchUpload
from api.models.responses import ReportMeta
from api.services.analysis_service import parse_upload, ParseError

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    company_name: str = Form(...),
    _: str = Depends(require_api_key),
) -> dict:
    contents = await file.read()
    try:
        batch = parse_upload(contents, file.filename or "upload.csv", company_name)
    except ParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    conn = get_db()
    for row in batch.rows:
        conn.execute("""
            INSERT OR REPLACE INTO enrollees
              (enrollee_id, batch_id, name, age, gender, systolic, diastolic,
               blood_glucose, bmi, cholesterol, email, phone, company_name)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, [
            row.enrollee_id, batch.batch_id, row.name, row.age, row.gender,
            row.systolic, row.diastolic, row.blood_glucose, row.bmi,
            row.cholesterol, row.email, row.phone, row.company_name,
        ])

    return {
        "batch_id": batch.batch_id,
        "company_name": batch.company_name,
        "count": len(batch.rows),
        "preview": [r.model_dump() for r in batch.rows[:5]],
    }


@router.post("/generate/{batch_id}")
async def generate_batch(
    batch_id: str,
    _: str = Depends(require_api_key),
) -> dict:
    from workers.tasks import generate_batch_task
    task = generate_batch_task.delay(batch_id)
    return {"job_id": task.id, "status": "queued"}


@router.get("/batch/{batch_id}")
async def get_batch(batch_id: str, _: str = Depends(require_api_key)) -> dict:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM report_meta WHERE batch_id = ?", [batch_id]
    ).fetchall()
    cols = [d[0] for d in conn.description]
    return {"batch_id": batch_id, "reports": [dict(zip(cols, r)) for r in rows]}


@router.get("/{enrollee_id}/pdf")
async def download_pdf(enrollee_id: str, _: str = Depends(require_api_key)) -> FileResponse:
    conn = get_db()
    result = conn.execute(
        "SELECT pdf_path FROM report_meta WHERE enrollee_id = ?", [enrollee_id]
    ).fetchone()
    if not result or not result[0] or not os.path.exists(result[0]):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(result[0], media_type="application/pdf",
                        filename=f"{enrollee_id}_report.pdf")


@router.get("/company/{batch_id}/pdf")
async def download_company_pdf(batch_id: str, _: str = Depends(require_api_key)) -> FileResponse:
    conn = get_db()
    result = conn.execute(
        "SELECT pdf_path FROM report_meta WHERE batch_id = ? AND enrollee_id = 'COMPANY'",
        [batch_id],
    ).fetchone()
    if not result or not result[0] or not os.path.exists(result[0]):
        raise HTTPException(status_code=404, detail="Company PDF not found")
    return FileResponse(result[0], media_type="application/pdf",
                        filename=f"company_report_{batch_id}.pdf")
```

- [ ] **Step 2: Verify upload endpoint works end-to-end**

```bash
cd health-api
uvicorn main:app --reload &
curl -X POST http://localhost:8000/api/reports/upload \
  -H "X-API-Key: $(grep API_KEY .env | cut -d= -f2)" \
  -F "file=@../TEST.xlsx" \
  -F "company_name=Test Company"
# Expected: {"batch_id": "...", "company_name": "Test Company", "count": N, "preview": [...]}
```

- [ ] **Step 3: Commit**

```bash
git add health-api/api/routers/reports.py
git commit -m "feat: add reports router — upload, generate, download endpoints"
```

---

## Task 11: Storage Service — Backblaze B2

**Files:**
- Create: `health-api/api/services/storage_service.py`
- Create: `health-api/api/routers/storage.py`
- Create: `health-api/tests/test_storage_service.py`

- [ ] **Step 1: Write failing tests**

```python
# health-api/tests/test_storage_service.py
import pytest
from unittest.mock import patch, MagicMock
from api.services.storage_service import upload_pdf, get_signed_url


def test_upload_pdf_returns_key(tmp_path):
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 test")

    mock_s3 = MagicMock()
    with patch("api.services.storage_service._get_s3_client", return_value=mock_s3):
        key = upload_pdf(str(pdf_file), "CL_001", "Arik Air")
    assert "CL_001" in key
    mock_s3.upload_file.assert_called_once()


def test_get_signed_url_returns_url():
    mock_s3 = MagicMock()
    mock_s3.generate_presigned_url.return_value = "https://b2.example.com/signed"
    with patch("api.services.storage_service._get_s3_client", return_value=mock_s3):
        url = get_signed_url("reports/CL_001.pdf")
    assert url.startswith("https://")
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_storage_service.py -v
```

- [ ] **Step 3: Create `health-api/api/services/storage_service.py`**

```python
from __future__ import annotations
import os
import boto3
from botocore.config import Config
from api.core.config import get_settings


def _get_s3_client():
    s = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=s.backblaze_endpoint_url,
        aws_access_key_id=s.backblaze_access_key_id,
        aws_secret_access_key=s.backblaze_secret_access_key,
        config=Config(signature_version="s3v4"),
    )


def upload_pdf(local_path: str, enrollee_id: str, company_name: str) -> str:
    s3 = _get_s3_client()
    settings = get_settings()
    safe_company = company_name.replace(" ", "_")
    key = f"reports/{safe_company}/{enrollee_id}/{os.path.basename(local_path)}"
    s3.upload_file(local_path, settings.backblaze_bucket_name, key,
                   ExtraArgs={"ContentType": "application/pdf"})
    return key


def get_signed_url(key: str, expiry_seconds: int = 604800) -> str:
    """Returns a 7-day (604800s) presigned download URL."""
    s3 = _get_s3_client()
    settings = get_settings()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.backblaze_bucket_name, "Key": key},
        ExpiresIn=expiry_seconds,
    )
```

- [ ] **Step 4: Create `health-api/api/routers/storage.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from api.core.security import require_api_key
from api.core.database import get_db
from api.services.storage_service import upload_pdf, get_signed_url

router = APIRouter()


@router.post("/upload/{enrollee_id}")
async def upload(enrollee_id: str, _: str = Depends(require_api_key)) -> dict:
    conn = get_db()
    result = conn.execute(
        "SELECT pdf_path, company_name FROM report_meta rm "
        "JOIN enrollees e USING (enrollee_id) WHERE rm.enrollee_id = ?",
        [enrollee_id],
    ).fetchone()
    if not result or not result[0]:
        raise HTTPException(status_code=404, detail="PDF not found. Generate it first.")
    pdf_path, company_name = result
    key = upload_pdf(pdf_path, enrollee_id, company_name or "Unknown")
    url = get_signed_url(key)
    conn.execute(
        "UPDATE report_meta SET b2_url = ? WHERE enrollee_id = ?", [url, enrollee_id]
    )
    return {"enrollee_id": enrollee_id, "key": key, "url": url}


@router.get("/url/{enrollee_id}")
async def get_url(enrollee_id: str, _: str = Depends(require_api_key)) -> dict:
    conn = get_db()
    result = conn.execute(
        "SELECT b2_url FROM report_meta WHERE enrollee_id = ?", [enrollee_id]
    ).fetchone()
    if not result or not result[0]:
        raise HTTPException(status_code=404, detail="No B2 URL found.")
    return {"enrollee_id": enrollee_id, "url": result[0]}
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
pytest tests/test_storage_service.py -v
```

- [ ] **Step 6: Commit**

```bash
git add health-api/api/services/storage_service.py health-api/api/routers/storage.py health-api/tests/test_storage_service.py
git commit -m "feat: add Backblaze B2 storage service and router"
```

---

## Task 12: Email Service — Thread-Safe Zoho OAuth + SMTP

**Files:**
- Create: `health-api/api/services/email_service.py`
- Create: `health-api/api/routers/email.py`
- Create: `health-api/tests/test_email_service.py`

- [ ] **Step 1: Write failing tests**

```python
# health-api/tests/test_email_service.py
import time
import pytest
from unittest.mock import patch, MagicMock
from api.services.email_service import ZohoTokenCache, send_via_zoho


def test_token_cache_returns_cached_token():
    cache = ZohoTokenCache()
    cache._token = "cached-token"
    cache._expires_at = time.time() + 3600
    assert cache.get() == "cached-token"


def test_token_cache_refreshes_expired_token():
    cache = ZohoTokenCache()
    cache._token = "old-token"
    cache._expires_at = time.time() - 1  # expired

    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": "new-token", "expires_in": 3600}

    with patch("httpx.post", return_value=mock_response):
        token = cache.get()
    assert token == "new-token"


def test_send_via_zoho_calls_api(tmp_path):
    pdf = tmp_path / "report.pdf"
    pdf.write_bytes(b"%PDF test")

    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("api.services.email_service._token_cache") as mock_cache, \
         patch("httpx.post", return_value=mock_response):
        mock_cache.get.return_value = "token"
        result = send_via_zoho("test@example.com", "Ada Obi", str(pdf))
    assert result is True
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_email_service.py -v
```

- [ ] **Step 3: Create `health-api/api/services/email_service.py`**

```python
from __future__ import annotations
import base64
import smtplib
import threading
import time
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
import httpx
from api.core.config import get_settings

_EMAIL_SUBJECT = "Your Clearline HMO Health Screening Report"
_EMAIL_BODY = """\
Dear {name},

Please find attached your personalised health screening report prepared by Klaire, \
your Clearline HMO health companion.

If you have any questions about your results, you can speak to one of our doctors \
through the Clearline mobile app.

Warm regards,
Clearline HMO
"""


class ZohoTokenCache:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._token: str | None = None
        self._expires_at: float = 0.0

    def get(self, force_refresh: bool = False) -> str:
        with self._lock:
            now = time.time()
            if not force_refresh and self._token and now < self._expires_at:
                return self._token
            return self._refresh()

    def _refresh(self) -> str:
        s = get_settings()
        resp = httpx.post(
            "https://accounts.zoho.com/oauth/v2/token",
            data={
                "refresh_token": s.zoho_refresh_token,
                "client_id": s.zoho_client_id,
                "client_secret": s.zoho_client_secret,
                "grant_type": "refresh_token",
            },
        )
        data = resp.json()
        if "access_token" not in data:
            raise RuntimeError(f"Zoho token refresh failed: {data}")
        expires_in = int(data.get("expires_in", 3600))
        self._token = data["access_token"]
        self._expires_at = time.time() + max(60, expires_in - 300)
        return self._token


_token_cache = ZohoTokenCache()


def send_via_zoho(to_email: str, name: str, pdf_path: str) -> bool:
    s = get_settings()
    token = _token_cache.get()
    with open(pdf_path, "rb") as f:
        pdf_b64 = base64.b64encode(f.read()).decode()
    payload = {
        "fromAddress": s.zoho_from_email,
        "toAddress": to_email,
        "subject": _EMAIL_SUBJECT,
        "content": _EMAIL_BODY.format(name=name),
        "attachments": [{"name": "health_report.pdf", "content": pdf_b64}],
    }
    resp = httpx.post(
        f"https://mail.zoho.com/api/accounts/{s.zoho_account_id}/messages",
        json=payload,
        headers={"Authorization": f"Zoho-oauthtoken {token}"},
        timeout=30,
    )
    return resp.status_code == 200


def send_via_smtp(to_email: str, name: str, pdf_path: str) -> bool:
    s = get_settings()
    msg = MIMEMultipart()
    msg["From"] = s.smtp_username
    msg["To"] = to_email
    msg["Subject"] = _EMAIL_SUBJECT
    msg.attach(MIMEText(_EMAIL_BODY.format(name=name), "plain"))

    with open(pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment; filename=health_report.pdf")
    msg.attach(part)

    with smtplib.SMTP(s.smtp_server, s.smtp_port) as server:
        server.starttls()
        server.login(s.smtp_username, s.smtp_password)
        server.sendmail(s.smtp_username, to_email, msg.as_string())
    return True


def send_alert_to_tele_team(enrollee_name: str, enrollee_id: str, urgency: str) -> bool:
    """Notify telemedicine team when a critical reading is found."""
    s = get_settings()
    subject = f"[CRITICAL] Health screening alert — {enrollee_name}"
    body = (
        f"Enrollee {enrollee_name} (ID: {enrollee_id}) has a CRITICAL health screening result.\n\n"
        f"Urgency level: {urgency}\n\n"
        "Please contact this enrollee within 24 hours via the telemedicine system."
    )
    try:
        with smtplib.SMTP(s.smtp_server, s.smtp_port) as server:
            server.starttls()
            server.login(s.smtp_username, s.smtp_password)
            msg = MIMEText(body)
            msg["From"] = s.smtp_username
            msg["To"] = s.tele_alert_email
            msg["Subject"] = subject
            server.sendmail(s.smtp_username, s.tele_alert_email, msg.as_string())
        return True
    except Exception:
        return False
```

- [ ] **Step 4: Create `health-api/api/routers/email.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from api.core.security import require_api_key
from api.core.database import get_db
from api.services.email_service import send_via_zoho, send_via_smtp

router = APIRouter()


@router.post("/send/{enrollee_id}")
async def send_email(
    enrollee_id: str,
    method: str = "zoho",
    _: str = Depends(require_api_key),
) -> dict:
    conn = get_db()
    result = conn.execute(
        "SELECT e.name, e.email, rm.pdf_path FROM enrollees e "
        "JOIN report_meta rm USING (enrollee_id) WHERE e.enrollee_id = ?",
        [enrollee_id],
    ).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Enrollee or PDF not found")
    name, email, pdf_path = result
    if not email:
        raise HTTPException(status_code=422, detail="No email address on record")
    if not pdf_path:
        raise HTTPException(status_code=422, detail="PDF not generated yet")

    ok = send_via_zoho(email, name, pdf_path) if method == "zoho" else send_via_smtp(email, name, pdf_path)
    if ok:
        conn.execute("UPDATE report_meta SET email_sent = TRUE WHERE enrollee_id = ?", [enrollee_id])
    return {"enrollee_id": enrollee_id, "sent": ok, "method": method}


@router.post("/bulk/{batch_id}")
async def bulk_send(
    batch_id: str,
    method: str = "zoho",
    _: str = Depends(require_api_key),
) -> dict:
    from workers.tasks import bulk_email_task
    task = bulk_email_task.delay(batch_id, method)
    return {"job_id": task.id, "status": "queued"}


@router.get("/methods")
async def list_methods(_: str = Depends(require_api_key)) -> dict:
    return {"methods": ["zoho", "smtp"]}
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
pytest tests/test_email_service.py -v
```

- [ ] **Step 6: Commit**

```bash
git add health-api/api/services/email_service.py health-api/api/routers/email.py health-api/tests/test_email_service.py
git commit -m "feat: add email service — thread-safe Zoho OAuth token cache, SMTP fallback, tele-alert"
```

---

## Task 13: Celery Async Jobs

**Files:**
- Create: `health-api/workers/tasks.py`
- Modify: `health-api/api/routers/jobs.py`

- [ ] **Step 1: Create `health-api/workers/tasks.py`**

```python
from __future__ import annotations
import os
import tempfile
import json
from celery import Celery
from api.core.config import get_settings

_settings = get_settings()
celery_app = Celery("health_api", broker=_settings.redis_url, backend=_settings.redis_url)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"


@celery_app.task(bind=True)
def generate_batch_task(self, batch_id: str) -> dict:
    from api.core.database import get_db
    from api.services.klaire_service import analyse_enrollee
    from api.services.report_service import generate_individual_pdf, generate_company_pdf
    from api.models.health_data import EnrolleeRow
    from api.services.email_service import send_alert_to_tele_team

    conn = get_db()
    rows_data = conn.execute(
        "SELECT * FROM enrollees WHERE batch_id = ?", [batch_id]
    ).fetchall()
    cols = [d[0] for d in conn.description]

    tmp_dir = tempfile.mkdtemp(prefix=f"batch_{batch_id}_")
    analyses = []
    rows = []
    failed = []

    for i, rd in enumerate(rows_data):
        row = EnrolleeRow(**dict(zip(cols, rd)))
        try:
            analysis = analyse_enrollee(row)
            pdf_path = generate_individual_pdf(row, analysis, tmp_dir)
            conn.execute("""
                INSERT OR REPLACE INTO report_meta (enrollee_id, batch_id, pdf_path)
                VALUES (?, ?, ?)
            """, [row.enrollee_id, batch_id, pdf_path])
            conn.execute("""
                INSERT OR REPLACE INTO klaire_analyses
                  (enrollee_id, batch_id, health_score, urgency, klaire_flags, next_steps)
                VALUES (?,?,?,?,?,?)
            """, [
                row.enrollee_id, batch_id, analysis.health_score,
                analysis.urgency.value, analysis.klaire_flags,
                json.dumps(analysis.next_steps),
            ])
            if analysis.urgency.value == "critical":
                send_alert_to_tele_team(row.name, row.enrollee_id, analysis.urgency.value)
            analyses.append(analysis)
            rows.append(row)
        except Exception as exc:
            failed.append({"enrollee_id": row.enrollee_id, "error": str(exc)})
        self.update_state(state="PROGRESS",
                         meta={"total": len(rows_data), "completed": i + 1})

    if rows:
        company_name = rows[0].company_name or "Company"
        company_pdf = generate_company_pdf(company_name, rows, analyses, tmp_dir)
        conn.execute("""
            INSERT OR REPLACE INTO report_meta (enrollee_id, batch_id, pdf_path)
            VALUES ('COMPANY', ?, ?)
        """, [batch_id, company_pdf])

    return {"completed": len(rows), "failed": len(failed), "failed_ids": [f["enrollee_id"] for f in failed]}


@celery_app.task(bind=True)
def bulk_email_task(self, batch_id: str, method: str = "zoho") -> dict:
    from api.core.database import get_db
    from api.services.email_service import send_via_zoho, send_via_smtp

    conn = get_db()
    rows = conn.execute(
        "SELECT e.enrollee_id, e.name, e.email, rm.pdf_path FROM enrollees e "
        "JOIN report_meta rm USING (enrollee_id) WHERE e.batch_id = ? AND e.email IS NOT NULL",
        [batch_id],
    ).fetchall()

    completed = 0
    failed = []
    for enrollee_id, name, email, pdf_path in rows:
        try:
            ok = send_via_zoho(email, name, pdf_path) if method == "zoho" else send_via_smtp(email, name, pdf_path)
            if ok:
                conn.execute("UPDATE report_meta SET email_sent = TRUE WHERE enrollee_id = ?", [enrollee_id])
                completed += 1
            else:
                failed.append(enrollee_id)
        except Exception:
            failed.append(enrollee_id)
        self.update_state(state="PROGRESS",
                         meta={"total": len(rows), "completed": completed})
    return {"completed": completed, "failed": len(failed), "failed_ids": failed}
```

- [ ] **Step 2: Implement `health-api/api/routers/jobs.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from api.core.security import require_api_key
from api.models.responses import JobStatus

router = APIRouter()


@router.get("/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str, _: str = Depends(require_api_key)) -> JobStatus:
    from workers.tasks import celery_app
    result = celery_app.AsyncResult(job_id)
    meta = result.info or {}
    return JobStatus(
        job_id=job_id,
        status=result.state.lower() if result.state else "unknown",
        total=meta.get("total", 0) if isinstance(meta, dict) else 0,
        completed=meta.get("completed", 0) if isinstance(meta, dict) else 0,
        failed_ids=meta.get("failed_ids", []) if isinstance(meta, dict) else [],
    )


@router.get("/{job_id}/progress")
async def get_progress(job_id: str, _: str = Depends(require_api_key)) -> dict:
    from workers.tasks import celery_app
    result = celery_app.AsyncResult(job_id)
    meta = result.info if isinstance(result.info, dict) else {}
    return {
        "job_id": job_id,
        "state": result.state,
        "total": meta.get("total", 0),
        "completed": meta.get("completed", 0),
    }
```

- [ ] **Step 3: Verify Celery starts (requires Redis running)**

```bash
# In one terminal — start Redis
docker run -p 6379:6379 redis:7-alpine
# In another terminal
cd health-api
celery -A workers.tasks worker --loglevel=info
# Expected: "celery@host ready."
```

- [ ] **Step 4: Commit**

```bash
git add health-api/workers/tasks.py health-api/api/routers/jobs.py
git commit -m "feat: add Celery tasks for async batch PDF generation and bulk email"
```

---

## Task 14: Full Integration Test

**Files:**
- Create: `health-api/tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# health-api/tests/test_integration.py
import io
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)
HEADERS = {"X-API-Key": "test-key"}


def _csv_bytes() -> bytes:
    df = pd.DataFrame([{
        "ENROLLEE ID": "INT_001",
        "NAME": "Test Person",
        "AGE": 40,
        "GENDER": "M",
        "SYSTOLIC": 130,
        "DIASTOLIC": 85,
        "BLOOD GLUCOSE": 100,
        "BMI": 24.0,
        "EMAIL": "test@example.com",
    }])
    return df.to_csv(index=False).encode()


def test_upload_parses_and_stores(monkeypatch):
    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_conn
    mock_conn.fetchone.return_value = None
    mock_conn.description = []

    with patch("api.routers.reports.get_db", return_value=mock_conn):
        resp = client.post(
            "/api/reports/upload",
            headers=HEADERS,
            files={"file": ("test.csv", _csv_bytes(), "text/csv")},
            data={"company_name": "Test Corp"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["preview"][0]["enrollee_id"] == "INT_001"


def test_health_check_is_public():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
```

- [ ] **Step 2: Run full test suite**

```bash
cd health-api
pytest tests/ -v --cov=api --cov-report=term-missing
# Expected: all tests PASS, coverage ≥ 80%
```

- [ ] **Step 3: Final commit**

```bash
git add health-api/tests/test_integration.py
git commit -m "test: add integration tests — full test suite passing"
```

---

## Running the Full Stack

```bash
# Terminal 1: Redis
docker run -p 6379:6379 redis:7-alpine

# Terminal 2: Celery worker
cd health-api && celery -A workers.tasks worker --loglevel=info

# Terminal 3: FastAPI
cd health-api && uvicorn main:app --reload --port 8000

# Test
curl http://localhost:8000/health
# {"status": "ok"}

curl -X POST http://localhost:8000/api/reports/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@../ARIK UPDATED.xlsx" \
  -F "company_name=Arik Air"
```

---

## What comes next — Plan B

Plan B covers the React + Vite staff portal. Implement Plan A fully and confirm the API is working before starting Plan B. The frontend depends on these endpoints:

- `POST /api/reports/upload` — upload page
- `GET /api/klaire/stream/{id}` — SSE preview panel
- `POST /api/email/bulk/{batch_id}` + `GET /api/jobs/{job_id}/progress` — bulk send
- `GET /api/reports/batch/{batch_id}` — individual reports list
