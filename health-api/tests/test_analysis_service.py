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
