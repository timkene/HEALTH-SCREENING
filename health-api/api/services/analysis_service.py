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
