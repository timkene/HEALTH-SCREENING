import pytest
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
