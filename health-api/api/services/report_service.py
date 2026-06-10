from __future__ import annotations
import os
import uuid
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.colors import HexColor
from api.models.health_data import EnrolleeRow
from api.models.responses import KlaireAnalysis, UrgencyLevel

_URGENCY_COLOURS = {
    UrgencyLevel.routine: HexColor("#00b894"),
    UrgencyLevel.watch: HexColor("#fdcb6e"),
    UrgencyLevel.urgent: HexColor("#e17055"),
    UrgencyLevel.critical: HexColor("#d63031"),
}

_DISCLAIMER = (
    "Clearline HMO Disclaimer: This report is a health screening summary, "
    "not a medical diagnosis. Please consult a qualified healthcare professional "
    "for medical advice, diagnosis, or treatment."
)

_TELE_ROUTINE = (
    "Your Clearline doctors are available for consultations on the Clearline mobile app."
)
_TELE_WATCH = (
    "Your reading is worth a conversation with a doctor. "
    "Reach out through the Clearline mobile app — it's free."
)
_TELE_CRITICAL = "A Clearline doctor will be in touch with you soon."


def generate_individual_pdf(
    row: EnrolleeRow,
    analysis: KlaireAnalysis,
    output_dir: str,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{row.enrollee_id}_{uuid.uuid4().hex[:8]}.pdf"
    out_path = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(out_path, pagesize=letter,
                            leftMargin=inch, rightMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(row.name, ParagraphStyle(
        "Title", parent=styles["Title"], fontSize=26, spaceAfter=6)))
    story.append(Paragraph(
        f"Enrollee ID: {row.enrollee_id} | {row.company_name or ''} | "
        f"Generated: {datetime.now().strftime('%B %d, %Y')}",
        ParagraphStyle("Sub", parent=styles["Normal"], fontSize=11, spaceAfter=20)))

    urgency_hex = _URGENCY_COLOURS.get(analysis.urgency, HexColor("#00b894"))
    score_data = [[
        Paragraph(f"<b>Health Score: {analysis.health_score}/100</b>",
                  ParagraphStyle("Score", parent=styles["Normal"], fontSize=16, textColor=colors.white)),
        Paragraph(f"<b>{analysis.urgency.value.upper()}</b>",
                  ParagraphStyle("Urg", parent=styles["Normal"], fontSize=14, textColor=colors.white)),
    ]]
    score_table = Table(score_data, colWidths=[4.5 * inch, 2 * inch])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), urgency_hex),
        ("PADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 16))

    vitals = [["Metric", "Value"]]
    if row.systolic and row.diastolic:
        vitals.append(["Blood Pressure", f"{row.systolic}/{row.diastolic} mmHg"])
    if row.blood_glucose:
        vitals.append(["Fasting Blood Glucose", f"{row.blood_glucose} mg/dL"])
    if row.bmi:
        vitals.append(["BMI", str(row.bmi)])
    if row.cholesterol:
        vitals.append(["Total Cholesterol", f"{row.cholesterol} mg/dL"])

    if len(vitals) > 1:
        t = Table(vitals, colWidths=[3 * inch, 3.5 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2d3436")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f5f5f5"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 16))

    story.append(Paragraph("Klaire's Analysis", styles["Heading2"]))
    for step in analysis.next_steps:
        story.append(Paragraph(f"- {step}", styles["Normal"]))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Talk to a Clearline Doctor", styles["Heading2"]))
    if analysis.urgency == UrgencyLevel.critical:
        tele_text = _TELE_CRITICAL
    elif analysis.urgency in (UrgencyLevel.watch, UrgencyLevel.urgent):
        tele_text = _TELE_WATCH
    else:
        tele_text = _TELE_ROUTINE
    story.append(Paragraph(tele_text, styles["Normal"]))
    story.append(Spacer(1, 20))

    story.append(Paragraph(_DISCLAIMER,
                            ParagraphStyle("Disc", parent=styles["Normal"],
                                           fontSize=9, textColor=colors.grey)))

    doc.build(story)
    return out_path


def generate_company_pdf(
    company_name: str,
    rows: list[EnrolleeRow],
    analyses: list[KlaireAnalysis],
    output_dir: str,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"company_{company_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.pdf"
    out_path = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(out_path, pagesize=letter,
                            leftMargin=inch, rightMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"{company_name} — Health Screening Report",
                            ParagraphStyle("T", parent=styles["Title"], fontSize=22)))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y')} | {len(rows)} enrollees screened",
        styles["Normal"]))
    story.append(Spacer(1, 16))

    if analyses:
        avg_score = int(sum(a.health_score for a in analyses) / len(analyses))
        counts = {u: sum(1 for a in analyses if a.urgency == u) for u in UrgencyLevel}
        summary = [
            ["Metric", "Value"],
            ["Average Health Score", f"{avg_score}/100"],
            ["Routine", str(counts[UrgencyLevel.routine])],
            ["Watch", str(counts[UrgencyLevel.watch])],
            ["Urgent", str(counts[UrgencyLevel.urgent])],
            ["Critical", str(counts[UrgencyLevel.critical])],
        ]
        t = Table(summary, colWidths=[3 * inch, 3.5 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2d3436")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f5f5f5"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(t)

    doc.build(story)
    return out_path
