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
For any reading in a critical range (systolic BP >= 180, diastolic BP >= 120, fasting glucose >= 400, \
or BMI >= 40), use urgent language and say: "Please speak to a doctor within 24 hours." \
Always end your response with this exact line on its own paragraph: \
"Clearline HMO Disclaimer: This report is a health screening summary, not a medical diagnosis. \
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
    client = _get_client()
    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=256,
        system=CLINICIAN_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_clinician_prompt(row)}],
    )
    return next(b.text for b in message.content if b.type == "text")
