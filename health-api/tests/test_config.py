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

    import importlib
    import api.core.config as cfg_module
    cfg_module.get_settings.cache_clear()
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
