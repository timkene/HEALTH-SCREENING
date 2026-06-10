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
