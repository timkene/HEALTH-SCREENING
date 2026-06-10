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
