import os
import pytest
from fastapi.testclient import TestClient

# Set test env vars before any app import
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
