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
