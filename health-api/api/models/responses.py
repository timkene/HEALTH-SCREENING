from __future__ import annotations
from enum import Enum
from pydantic import BaseModel


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
