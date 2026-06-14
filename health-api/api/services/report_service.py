from __future__ import annotations
import os
import uuid
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, Image as RLImage,
)
from reportlab.graphics.shapes import Drawing, Rect, Polygon, String as GStr, Line, Circle
from reportlab.graphics.renderPDF import draw

from api.models.health_data import EnrolleeRow
from api.models.responses import KlaireAnalysis, UrgencyLevel

# ── Clearline brand palette ─────────────────────────────────────────────────
_NAVY        = HexColor("#1B2B8C")   # wordmark navy
_NAVY_LIGHT  = HexColor("#EEF0FF")   # very light navy tint for info boxes
_TEAL        = HexColor("#00BCD4")   # icon mid-gradient teal
_TEAL_LIGHT  = HexColor("#E0F7FA")   # pale teal for example boxes
_GREEN       = HexColor("#00C87A")   # icon start green
_BLUE_ACCENT = HexColor("#4BA3FF")   # icon end blue
_WHITE       = colors.white
_BLACK       = HexColor("#1A1A2E")   # near-black body text
_GREY        = HexColor("#6B7280")   # secondary text
_BORDER      = HexColor("#DDE1F0")   # subtle border
_BG_PAGE     = HexColor("#FAFBFF")   # off-white page bg

# Urgency palette
_URGENCY_COLOR = {
    UrgencyLevel.routine:  HexColor("#00C87A"),
    UrgencyLevel.watch:    HexColor("#FFA726"),
    UrgencyLevel.urgent:   HexColor("#EF5350"),
    UrgencyLevel.critical: HexColor("#C62828"),
}
_URGENCY_LABEL = {
    UrgencyLevel.routine:  "ALL CLEAR",
    UrgencyLevel.watch:    "KEEP AN EYE ON IT",
    UrgencyLevel.urgent:   "NEEDS ATTENTION",
    UrgencyLevel.critical: "SEEK CARE NOW",
}
_URGENCY_ICON = {
    UrgencyLevel.routine:  "✓",
    UrgencyLevel.watch:    "!",
    UrgencyLevel.urgent:   "!!",
    UrgencyLevel.critical: "!!!",
}

# Logo path (relative to this file)
_LOGO_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..",
    "HEALTH SCREEN", "Clearline.png",
)
_LOGO_PATH = os.path.abspath(_LOGO_PATH)

_DISCLAIMER = (
    "Clearline HMO Disclaimer: This report is a health screening summary, not a medical "
    "diagnosis. Please consult a qualified healthcare professional for all medical advice, "
    "diagnosis, and treatment decisions."
)
_TELE_MSG = {
    UrgencyLevel.routine: (
        "Your Clearline doctors are available for consultations at any time "
        "through the Clearline mobile app."
    ),
    UrgencyLevel.watch: (
        "One or more of your readings deserves a conversation with a doctor. "
        "Reach out through the Clearline mobile app — it is free, fast, and confidential."
    ),
    UrgencyLevel.urgent: (
        "Please book a consultation with a doctor as soon as possible. "
        "Open the Clearline mobile app now to connect with a doctor today."
    ),
    UrgencyLevel.critical: (
        "A Clearline doctor will be reaching out to you very soon. "
        "Please do not ignore any calls or messages from Clearline HMO."
    ),
}

# ── Gauge segment definitions ───────────────────────────────────────────────
_G_BP_SYS = [
    ( 80, 120, HexColor("#00C87A"), "Normal\n<120"),
    (120, 130, HexColor("#A5D6A7"), "Elevated\n120-129"),
    (130, 140, HexColor("#FFA726"), "Stage 1\n130-139"),
    (140, 180, HexColor("#EF5350"), "Stage 2\n140-179"),
    (180, 220, HexColor("#B71C1C"), "Crisis\n≥180"),
]
_G_BP_DIA = [
    ( 50,  80, HexColor("#00C87A"), "Normal\n<80"),
    ( 80,  90, HexColor("#FFA726"), "Stage 1\n80-89"),
    ( 90, 120, HexColor("#EF5350"), "Stage 2\n≥90"),
    (120, 140, HexColor("#B71C1C"), "Crisis\n≥120"),
]
_G_GLUCOSE = [
    ( 40,  70, HexColor("#4BA3FF"), "Low\n<70"),
    ( 70, 100, HexColor("#00C87A"), "Normal\n70-99"),
    (100, 126, HexColor("#FFA726"), "Pre-diabetes\n100-125"),
    (126, 300, HexColor("#EF5350"), "High\n≥126"),
]
_G_BMI = [
    (12.0, 18.5, HexColor("#4BA3FF"), "Under-\nweight"),
    (18.5, 25.0, HexColor("#00C87A"), "Normal\n18.5-24.9"),
    (25.0, 30.0, HexColor("#FFA726"), "Over-\nweight"),
    (30.0, 45.0, HexColor("#EF5350"), "Obese\n≥30"),
]
_G_CHOLESTEROL = [
    (100, 200, HexColor("#00C87A"), "Desirable\n<200"),
    (200, 240, HexColor("#FFA726"), "Borderline\n200-239"),
    (240, 320, HexColor("#EF5350"), "High\n≥240"),
]

# ── Educational content ─────────────────────────────────────────────────────
_EDU = {
    "bp": {
        "title": "BLOOD PRESSURE",
        "what": (
            "Blood pressure measures the force of blood pushing against the walls of your arteries — "
            "the vessels that carry blood from your heart to the rest of your body. It is expressed "
            "as two numbers: the <b>systolic</b> (top number) captures pressure when your heart "
            "beats and pumps blood out; the <b>diastolic</b> (bottom number) captures pressure when "
            "your heart is resting and refilling between beats. Both numbers are important."
        ),
        "why": (
            "High blood pressure — called <b>hypertension</b> — is often called the 'silent killer' "
            "because it rarely causes symptoms while quietly straining your heart, stiffening your "
            "arteries, and raising your risk of heart attack, stroke, and kidney disease. "
            "Detecting it early through a screening like this is your biggest advantage."
        ),
        "example": (
            "<b>Think of it this way:</b> Imagine your arteries as garden hoses and your blood as "
            "the water flowing through them. When the water pressure is just right, the hoses stay "
            "flexible and work perfectly. If someone cranks the pressure too high and leaves it "
            "there for years, the hoses bulge, develop weak spots, and eventually fail — sometimes "
            "without warning. Your blood vessels respond to sustained high pressure in exactly "
            "the same way."
        ),
        "normal": "Target: below 120/80 mmHg",
    },
    "glucose": {
        "title": "FASTING BLOOD GLUCOSE",
        "what": (
            "Fasting blood glucose measures how much sugar (glucose) is in your blood after at "
            "least 8 hours without eating. Glucose is your body's primary source of energy — it "
            "comes from carbohydrates you eat and is regulated by <b>insulin</b>, a hormone made "
            "by your pancreas. This fasting test shows how well your body manages blood sugar "
            "when it is not actively processing food."
        ),
        "why": (
            "Consistently high blood glucose slowly damages your blood vessels and nerves over "
            "years — this is the mechanism behind <b>type 2 diabetes</b>, which can harm your "
            "eyesight, kidneys, heart, and feet. Blood glucose that is <b>too low</b> (below "
            "70 mg/dL) is also a concern: it starves your brain and muscles, causing dizziness, "
            "shakiness, or confusion. Balance is everything."
        ),
        "example": (
            "<b>Think of it this way:</b> Glucose is the petrol in your body's engine, and insulin "
            "is the fuel pump that delivers exactly the right amount at the right time. When the "
            "system works well, everything runs smoothly. Too much fuel sitting in the tank too "
            "long corrodes the system from inside; too little and the engine stalls. Your body "
            "thrives when glucose stays in its optimal range every single day."
        ),
        "normal": "Normal fasting range: 70–99 mg/dL",
    },
    "bmi": {
        "title": "BODY MASS INDEX (BMI)",
        "what": (
            "BMI — Body Mass Index — is a number calculated from your height and weight. It is "
            "used as a quick screening indicator of whether your weight falls within a range "
            "generally considered healthy for your height. A BMI between <b>18.5 and 24.9</b> is "
            "the healthy range for most adults. BMI is not a perfect measure — it cannot "
            "distinguish muscle from fat — but it is a well-established and practical first check."
        ),
        "why": (
            "Excess body weight is closely linked to increased risk of type 2 diabetes, heart "
            "disease, high blood pressure, joint problems, sleep apnoea, and certain cancers. "
            "Being significantly underweight carries its own risks: weakened immunity, bone "
            "fragility, and nutritional deficiencies. Both ends of the scale matter, and this "
            "screening helps identify where you stand today."
        ),
        "example": (
            "<b>Think of it this way:</b> A bridge is engineered to carry loads within a specific "
            "range. Overload it and the structure faces strain it was not designed for — joints "
            "wear, cables stretch, and eventually something gives. Your body's joints, heart, "
            "and organs work optimally within their own 'load range'. BMI is the quick first "
            "check to see whether you are within that zone."
        ),
        "normal": "Healthy range: 18.5–24.9",
    },
    "cholesterol": {
        "title": "TOTAL CHOLESTEROL",
        "what": (
            "Cholesterol is a waxy, fat-like substance found in every cell of your body — "
            "essential for building cell membranes and producing hormones. Your liver makes most "
            "of it; some comes from your diet. It travels in your bloodstream as <b>LDL</b> "
            "('bad' cholesterol, which can build up in arteries) and <b>HDL</b> ('good' "
            "cholesterol, which helps remove LDL). Total cholesterol is the sum of all fractions."
        ),
        "why": (
            "When LDL cholesterol levels are too high for too long, it starts accumulating on "
            "artery walls as <b>plaque</b> — fatty deposits that narrow arteries over years and "
            "decades. This silently raises your risk of <b>heart attack, stroke</b>, and poor "
            "circulation. The process produces no symptoms until something goes wrong. Your "
            "cholesterol reading today is a window into what may be building inside your arteries."
        ),
        "example": (
            "<b>Think of it this way:</b> Picture the water pipes in an old building — never "
            "serviced, never flushed. Over years, mineral deposits and scale slowly coat the "
            "inside walls, narrowing the opening until flow is seriously reduced. When the "
            "blockage finally happens, it is sudden and severe. High cholesterol does exactly "
            "this to your arteries — a slow, invisible build-up with a potentially dramatic end."
        ),
        "normal": "Desirable: below 200 mg/dL",
    },
}


# ── Drawing helpers ─────────────────────────────────────────────────────────

def _make_gauge(value: float, segments: list, unit: str = "", width: float = 450.0) -> Drawing:
    H = 72
    bar_y, bar_h = 22, 24
    bar_top = bar_y + bar_h  # y=46

    d = Drawing(width, H)
    lo = segments[0][0]
    hi = segments[-1][1]
    span = hi - lo

    # Shadow behind bar
    d.add(Rect(0, bar_y - 2, width, bar_h + 4,
               fillColor=HexColor("#E8EAF6"), strokeColor=None))

    for seg_lo, seg_hi, seg_color, label in segments:
        x = (seg_lo - lo) / span * width
        w = max(1.0, (seg_hi - seg_lo) / span * width)
        d.add(Rect(x, bar_y, w, bar_h,
                   fillColor=seg_color,
                   strokeColor=_WHITE,
                   strokeWidth=1.2))
        cx = x + w / 2
        parts = label.split("\n")
        d.add(GStr(cx, 11, parts[0], fontSize=7, textAnchor="middle",
                   fillColor=HexColor("#4A4A6A"), fontName="Helvetica-Bold"))
        if len(parts) > 1:
            d.add(GStr(cx, 2, parts[1], fontSize=7, textAnchor="middle",
                       fillColor=HexColor("#4A4A6A")))

    # Clamped value marker
    clamped = max(lo + span * 0.001, min(hi - span * 0.001, value))
    xv = (clamped - lo) / span * width

    # White outline then navy filled triangle (pointing down at bar)
    d.add(Polygon([xv, bar_top - 1, xv - 8, bar_top + 15, xv + 8, bar_top + 15],
                  fillColor=_WHITE, strokeColor=None))
    d.add(Polygon([xv, bar_top + 1, xv - 6, bar_top + 13, xv + 6, bar_top + 13],
                  fillColor=_NAVY, strokeColor=None))

    # Value callout
    val_str = f"{value}" + (f" {unit}" if unit else "")
    label_x = max(30.0, min(width - 30.0, xv))
    d.add(Rect(label_x - 22, bar_top + 17, 44, 16,
               fillColor=_NAVY, strokeColor=None, rx=3, ry=3))
    d.add(GStr(label_x, bar_top + 22, val_str, fontSize=8,
               textAnchor="middle", fillColor=_WHITE, fontName="Helvetica-Bold"))

    return d


def _score_circle(score: int, color: HexColor, size: float = 80.0) -> Drawing:
    d = Drawing(size, size)
    cx, cy, r = size / 2, size / 2, size / 2 - 4
    # Outer ring
    d.add(Circle(cx, cy, r, fillColor=color, strokeColor=_WHITE, strokeWidth=3))
    # Score number
    d.add(GStr(cx, cy + 4, str(score), fontSize=24, textAnchor="middle",
               fillColor=_WHITE, fontName="Helvetica-Bold"))
    d.add(GStr(cx, cy - 14, "/100", fontSize=10, textAnchor="middle",
               fillColor=HexColor("#FFFFFF99")))
    return d


# ── Style factory ───────────────────────────────────────────────────────────

def _make_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        # Cover
        "report_type": ParagraphStyle(
            "RepType", fontSize=9, fontName="Helvetica-Bold",
            textColor=_TEAL, spaceAfter=2, tracking=2,
        ),
        "patient_name": ParagraphStyle(
            "PatName", fontSize=28, fontName="Helvetica-Bold",
            textColor=_NAVY, spaceAfter=4, leading=32,
        ),
        "patient_meta": ParagraphStyle(
            "PatMeta", fontSize=10, textColor=_GREY, spaceAfter=16, leading=15,
        ),
        "score_val": ParagraphStyle(
            "ScV", fontSize=18, fontName="Helvetica-Bold",
            textColor=_WHITE, leading=22,
        ),
        "score_label": ParagraphStyle(
            "ScL", fontSize=10, textColor=HexColor("#FFFFFFCC"), leading=14,
        ),
        "urgency_badge": ParagraphStyle(
            "Urg", fontSize=13, fontName="Helvetica-Bold",
            textColor=_WHITE, leading=16,
        ),
        # Section
        "sec_title": ParagraphStyle(
            "SecT", fontSize=12, fontName="Helvetica-Bold",
            textColor=_WHITE, leading=15,
        ),
        # Info boxes
        "box_head": ParagraphStyle(
            "BxH", fontSize=10, fontName="Helvetica-Bold",
            textColor=_NAVY, spaceAfter=4, leading=13,
        ),
        "box_body": ParagraphStyle(
            "BxB", fontSize=10.5, textColor=_BLACK, leading=16, spaceAfter=0,
        ),
        # Example
        "ex_label": ParagraphStyle(
            "ExL", fontSize=9, fontName="Helvetica-Bold",
            textColor=_TEAL, spaceAfter=2, tracking=1,
        ),
        "ex_body": ParagraphStyle(
            "ExB", fontSize=10.5, textColor=HexColor("#004D5A"), leading=16,
        ),
        # Result
        "res_value": ParagraphStyle(
            "RV", fontSize=22, fontName="Helvetica-Bold",
            textColor=_WHITE, leading=26, spaceAfter=2,
        ),
        "res_status": ParagraphStyle(
            "RS", fontSize=11, fontName="Helvetica-Bold",
            textColor=_WHITE, leading=15,
        ),
        # Narrative
        "narr_head": ParagraphStyle(
            "NaH", fontSize=11, fontName="Helvetica-Bold",
            textColor=_NAVY, spaceBefore=10, spaceAfter=4, leading=14,
        ),
        "narr_body": ParagraphStyle(
            "NaB", fontSize=10.5, textColor=_BLACK, leading=17, spaceAfter=5,
        ),
        "step": ParagraphStyle(
            "Stp", fontSize=10.5, textColor=_BLACK, leading=17,
            leftIndent=16, spaceAfter=5,
        ),
        "normal_tag": ParagraphStyle(
            "NTag", fontSize=9, textColor=_GREY, leading=12, spaceAfter=6,
        ),
        # Summary
        "next_head": ParagraphStyle(
            "NxH", fontSize=12, fontName="Helvetica-Bold",
            textColor=_WHITE, leading=15,
        ),
        "next_step": ParagraphStyle(
            "NxS", fontSize=11, textColor=_BLACK, leading=17,
            leftIndent=10, spaceAfter=6,
        ),
        # Footer
        "disclaimer": ParagraphStyle(
            "Disc", fontSize=8, textColor=_GREY, leading=11,
        ),
        "greeting": ParagraphStyle(
            "Gr", fontSize=11, textColor=_BLACK, leading=18, spaceAfter=6,
        ),
        "klaire_note": ParagraphStyle(
            "KN", fontSize=9, fontName="Helvetica-Bold",
            textColor=_TEAL, spaceAfter=4, tracking=1,
        ),
    }


# ── Status helpers ──────────────────────────────────────────────────────────

def _bp_status(s: float, d: float) -> tuple[str, HexColor]:
    if s >= 180 or d >= 120:
        return "HYPERTENSIVE CRISIS", HexColor("#B71C1C")
    if s >= 140 or d >= 90:
        return "STAGE 2 HYPERTENSION", HexColor("#EF5350")
    if s >= 130 or d >= 80:
        return "STAGE 1 HYPERTENSION", HexColor("#FFA726")
    if s >= 120:
        return "ELEVATED BLOOD PRESSURE", HexColor("#FFA726")
    return "NORMAL BLOOD PRESSURE", HexColor("#00C87A")


def _glucose_status(v: float) -> tuple[str, HexColor]:
    if v < 70:
        return "LOW — HYPOGLYCAEMIA RISK", HexColor("#4BA3FF")
    if v < 100:
        return "NORMAL", HexColor("#00C87A")
    if v < 126:
        return "PRE-DIABETES RANGE", HexColor("#FFA726")
    return "DIABETIC RANGE", HexColor("#EF5350")


def _bmi_status(v: float) -> tuple[str, HexColor]:
    if v < 18.5:
        return "UNDERWEIGHT", HexColor("#4BA3FF")
    if v < 25:
        return "HEALTHY WEIGHT", HexColor("#00C87A")
    if v < 30:
        return "OVERWEIGHT", HexColor("#FFA726")
    return "OBESE", HexColor("#EF5350")


def _cholesterol_status(v: float) -> tuple[str, HexColor]:
    if v < 200:
        return "DESIRABLE", HexColor("#00C87A")
    if v < 240:
        return "BORDERLINE HIGH", HexColor("#FFA726")
    return "HIGH", HexColor("#EF5350")


# ── Block builders ──────────────────────────────────────────────────────────

def _section_header(title: str, st: dict) -> Table:
    """Navy header bar with teal left accent stripe."""
    stripe = Table([[""]], colWidths=[0.08 * inch])
    stripe.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _TEAL),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    content = Table(
        [[Paragraph(f"  {title}", st["sec_title"])]],
        colWidths=[6.42 * inch],
    )
    content.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    outer = Table([[stripe, content]], colWidths=[0.08 * inch, 6.42 * inch])
    outer.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return outer


def _info_box(heading: str, body: str, st: dict) -> Table:
    rows = [
        [Paragraph(heading, st["box_head"])],
        [Paragraph(body, st["box_body"])],
    ]
    t = Table(rows, colWidths=[6.3 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _NAVY_LIGHT),
        ("TOPPADDING", (0, 0), (0, 0), 8),
        ("TOPPADDING", (1, 0), (1, 0), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("LINEAFTER", (0, 0), (0, -1), 0, _NAVY_LIGHT),  # prevent right border
    ]))
    return t


def _example_box(body: str, st: dict) -> Table:
    rows = [
        [Paragraph("REAL-WORLD EXAMPLE", st["ex_label"])],
        [Paragraph(body, st["ex_body"])],
    ]
    t = Table(rows, colWidths=[6.3 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _TEAL_LIGHT),
        ("TOPPADDING", (0, 0), (0, 0), 8),
        ("TOPPADDING", (1, 0), (1, 0), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("LINEBEFORE", (0, 0), (0, -1), 4, _TEAL),
    ]))
    return t


def _result_box(value_str: str, status_str: str, color: HexColor, st: dict) -> Table:
    data = [[
        Paragraph(value_str, st["res_value"]),
        Paragraph(status_str, st["res_status"]),
    ]]
    t = Table(data, colWidths=[2.8 * inch, 3.7 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _gauge_label(label: str, normal_text: str, st: dict) -> Table:
    data = [[Paragraph(f"<b>{label}</b>", st["narr_head"]),
             Paragraph(normal_text, st["normal_tag"])]]
    t = Table(data, colWidths=[3.5 * inch, 3.0 * inch])
    t.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
    ]))
    return t


# ── Metric section builders ─────────────────────────────────────────────────

def _metric_section(
    edu_key: str,
    value_str: str,
    status_str: str,
    status_color: HexColor,
    gauges: list,           # list of (gauge_label, Drawing)
    narratives: dict,
    narr_key: str,
    st: dict,
) -> list:
    edu = _EDU[edu_key]
    narr = narratives.get(narr_key, {})
    meaning = narr.get("meaning", "")
    steps = narr.get("steps", [])

    items: list = [
        Spacer(1, 14),
        _section_header(edu["title"], st),
        Spacer(1, 10),
        KeepTogether([
            _info_box("What is this test?", edu["what"], st),
            Spacer(1, 6),
            _info_box("Why does it matter?", edu["why"], st),
            Spacer(1, 6),
            _example_box(edu["example"], st),
        ]),
        Spacer(1, 14),
    ]

    for g_label, gauge_drawing in gauges:
        items.append(_gauge_label(g_label, edu["normal"], st))
        items.append(gauge_drawing)
        items.append(Spacer(1, 10))

    items += [
        _result_box(value_str, status_str, status_color, st),
        Spacer(1, 12),
    ]

    if meaning:
        items += [
            Paragraph("What this means for you — from Klaire", st["narr_head"]),
            Paragraph(meaning, st["narr_body"]),
            Spacer(1, 4),
        ]
    if steps:
        items.append(Paragraph("What you can do", st["narr_head"]))
        for i, s in enumerate(steps, 1):
            items.append(Paragraph(f"<b>{i}.</b>  {s}", st["step"]))

    items += [Spacer(1, 12), HRFlowable(width="100%", color=_BORDER, thickness=0.8)]
    return items


def _urine_section(row: EnrolleeRow, st: dict) -> list:
    gluc = (row.urine_glucose or "NEGATIVE").strip().upper()
    prot = (row.urine_protein or "NEGATIVE").strip().upper()
    g_ok = gluc == "NEGATIVE"
    p_ok = prot == "NEGATIVE"
    gc = HexColor("#00C87A") if g_ok else HexColor("#EF5350")
    pc = HexColor("#00C87A") if p_ok else HexColor("#EF5350")

    items = [
        Spacer(1, 14),
        _section_header("URINE SCREENING TESTS", st),
        Spacer(1, 10),
        KeepTogether([
            _info_box(
                "What are these tests checking for?",
                "Two substances are screened in your urine: <b>glucose</b> (sugar) and "
                "<b>protein</b>. Urine glucose is normally absent — if detected, it may "
                "indicate blood sugar has been very high, beyond the kidney's reabsorption "
                "threshold. Urine protein is also normally absent — its presence can suggest "
                "early kidney stress or reduced kidney filtering capacity. Both are early "
                "warning signals worth acting on.",
                st,
            ),
        ]),
        Spacer(1, 12),
    ]

    data = [
        [Paragraph("<b>Test</b>", st["box_head"]),
         Paragraph("<b>Your Result</b>", st["box_head"]),
         Paragraph("<b>What it means</b>", st["box_head"])],
        [
            Paragraph("Urine Glucose", st["box_body"]),
            Paragraph(gluc, ParagraphStyle("GR", fontSize=10, fontName="Helvetica-Bold",
                                           textColor=_WHITE)),
            Paragraph("Normal — no sugar detected." if g_ok else
                      "Sugar detected. Discuss with a doctor promptly.",
                      st["box_body"]),
        ],
        [
            Paragraph("Urine Protein", st["box_body"]),
            Paragraph(prot, ParagraphStyle("PR", fontSize=10, fontName="Helvetica-Bold",
                                           textColor=_WHITE)),
            Paragraph("Normal — no protein detected." if p_ok else
                      "Protein detected. A kidney function check is recommended.",
                      st["box_body"]),
        ],
    ]
    t = Table(data, colWidths=[2.0 * inch, 1.5 * inch, 3.0 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), _WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_NAVY_LIGHT, _WHITE]),
        ("BACKGROUND", (1, 1), (1, 1), gc),
        ("BACKGROUND", (1, 2), (1, 2), pc),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    items.append(t)
    items += [Spacer(1, 12), HRFlowable(width="100%", color=_BORDER, thickness=0.8)]
    return items


# ── Cover page ──────────────────────────────────────────────────────────────

def _cover_section(row: EnrolleeRow, analysis: KlaireAnalysis, st: dict) -> list:
    items: list = []
    urgency_color = _URGENCY_COLOR[analysis.urgency]
    urgency_label = _URGENCY_LABEL[analysis.urgency]

    # ── Logo + tagline header ─────────────────────────────────────────────
    logo_cell: list = []
    if os.path.exists(_LOGO_PATH):
        logo_img = RLImage(_LOGO_PATH, width=2.0 * inch, kind="proportional")
        logo_cell = [logo_img]
    else:
        logo_cell = [Paragraph(
            "<b>CLEARLINE</b>",
            ParagraphStyle("CLfb", fontSize=18, fontName="Helvetica-Bold", textColor=_NAVY),
        )]

    tagline = Paragraph(
        "Personal Health Screening Report",
        ParagraphStyle("TL", fontSize=10, textColor=_GREY, leading=13),
    )
    sub = Paragraph(
        "Powered by Klaire — Clearline HMO's AI Health Companion",
        ParagraphStyle("Sub", fontSize=8, textColor=_TEAL, leading=12),
    )

    logo_table = Table(
        [[logo_cell[0], [tagline, Spacer(1, 2), sub]]],
        colWidths=[2.4 * inch, 4.1 * inch],
    )
    logo_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("LEFTPADDING", (1, 0), (1, 0), 12),
    ]))
    items.append(logo_table)
    items.append(HRFlowable(width="100%", color=_TEAL, thickness=2))
    items.append(Spacer(1, 18))

    # ── Patient identity ──────────────────────────────────────────────────
    items.append(Paragraph(row.name.title(), st["patient_name"]))
    items.append(Paragraph(
        f"{row.company_name or 'Clearline HMO'}  &nbsp;·&nbsp;  "
        f"ID: {row.enrollee_id}  &nbsp;·&nbsp;  "
        f"Screened: {datetime.now().strftime('%B %d, %Y')}",
        st["patient_meta"],
    ))

    # ── Health score + urgency banner ─────────────────────────────────────
    _wht   = lambda s, fs, bold=False: ParagraphStyle(
        s, fontSize=fs, textColor=_WHITE, leading=fs * 1.4,
        fontName="Helvetica-Bold" if bold else "Helvetica",
    )
    _wht99 = lambda s, fs: ParagraphStyle(
        s, fontSize=fs, textColor=HexColor("#FFFFFFBB"), leading=fs * 1.4,
    )

    badge_data = [[
        # ── Column 1: score block ─────────────────────────────────────
        [
            Paragraph("HEALTH SCORE", _wht99("ScLbl", 8)),
            Spacer(1, 3),
            Paragraph(
                f"<b>{analysis.health_score}</b>",
                ParagraphStyle("ScNum", fontSize=38, fontName="Helvetica-Bold",
                               textColor=_WHITE, leading=40),
            ),
            Paragraph("out of 100", _wht99("ScSub", 9)),
        ],
        # ── Column 2: urgency block ───────────────────────────────────
        [
            Paragraph("STATUS", _wht99("UrgLbl", 8)),
            Spacer(1, 4),
            Paragraph(
                f"{_URGENCY_ICON[analysis.urgency]}  {urgency_label}",
                _wht("UrgVal", 14, bold=True),
            ),
            Spacer(1, 6),
            Paragraph(
                f"Dominant risk: {analysis.dominant_risk or 'None identified'}",
                _wht99("UrgRisk", 9),
            ),
        ],
    ]]
    badge = Table(badge_data, colWidths=[2.3 * inch, 4.2 * inch])
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), urgency_color),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING", (0, 0), (0, 0), 18),
        ("LEFTPADDING", (1, 0), (1, 0), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBEFORE", (1, 0), (1, 0), 1, HexColor("#FFFFFF55")),
    ]))
    items.append(badge)
    items.append(Spacer(1, 18))

    # ── Klaire's opening letter ────────────────────────────────────────────
    letter_rows = [
        [Paragraph("A MESSAGE FROM KLAIRE", st["klaire_note"])],
        [Paragraph(analysis.klaire_flags, st["greeting"])],
    ]
    letter_t = Table(letter_rows, colWidths=[6.3 * inch])
    letter_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _TEAL_LIGHT),
        ("TOPPADDING", (0, 0), (0, 0), 10),
        ("TOPPADDING", (1, 0), (1, 0), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("LINEBEFORE", (0, 0), (0, -1), 4, _TEAL),
    ]))
    items.append(letter_t)
    items.append(Spacer(1, 16))
    items.append(HRFlowable(width="100%", color=_BORDER, thickness=0.8))

    return items


# ── Main generators ─────────────────────────────────────────────────────────

def generate_individual_pdf(
    row: EnrolleeRow,
    analysis: KlaireAnalysis,
    output_dir: str,
    narratives: dict | None = None,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{row.enrollee_id}_{uuid.uuid4().hex[:8]}.pdf"
    out_path = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        out_path, pagesize=letter,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
        topMargin=0.65 * inch, bottomMargin=0.65 * inch,
    )
    st = _make_styles()
    nav = narratives or {}
    story: list = []

    # Cover
    story.extend(_cover_section(row, analysis, st))

    # Blood Pressure
    if row.systolic and row.diastolic:
        status_str, status_color = _bp_status(row.systolic, row.diastolic)
        story.extend(_metric_section(
            "bp",
            f"{row.systolic}/{row.diastolic} mmHg",
            status_str, status_color,
            [
                (f"Systolic (top number) — {row.systolic} mmHg",
                 _make_gauge(row.systolic, _G_BP_SYS, "mmHg")),
                (f"Diastolic (bottom number) — {row.diastolic} mmHg",
                 _make_gauge(row.diastolic, _G_BP_DIA, "mmHg")),
            ],
            nav, "blood_pressure", st,
        ))

    # Glucose
    if row.blood_glucose:
        status_str, status_color = _glucose_status(row.blood_glucose)
        story.extend(_metric_section(
            "glucose",
            f"{row.blood_glucose} mg/dL",
            status_str, status_color,
            [(f"Fasting Blood Glucose — {row.blood_glucose} mg/dL",
              _make_gauge(row.blood_glucose, _G_GLUCOSE, "mg/dL"))],
            nav, "glucose", st,
        ))

    # BMI
    if row.bmi:
        status_str, status_color = _bmi_status(row.bmi)
        story.extend(_metric_section(
            "bmi",
            f"BMI  {row.bmi}",
            status_str, status_color,
            [(f"Body Mass Index — {row.bmi}",
              _make_gauge(row.bmi, _G_BMI))],
            nav, "bmi", st,
        ))

    # Cholesterol
    if row.cholesterol:
        status_str, status_color = _cholesterol_status(row.cholesterol)
        story.extend(_metric_section(
            "cholesterol",
            f"{row.cholesterol} mg/dL",
            status_str, status_color,
            [(f"Total Cholesterol — {row.cholesterol} mg/dL",
              _make_gauge(row.cholesterol, _G_CHOLESTEROL, "mg/dL"))],
            nav, "cholesterol", st,
        ))

    # Urine
    if row.urine_glucose or row.urine_protein:
        story.extend(_urine_section(row, st))

    # ── Summary / next steps ──────────────────────────────────────────────
    story.append(Spacer(1, 14))
    story.append(_section_header("YOUR 3 NEXT STEPS FROM KLAIRE", st))
    story.append(Spacer(1, 10))
    for i, step in enumerate(analysis.next_steps, 1):
        story.append(Paragraph(
            f"<b>{i}.</b>  {step}",
            ParagraphStyle("NS", fontSize=11, textColor=_BLACK,
                           leading=17, leftIndent=10, spaceAfter=7),
        ))

    # ── Telemedicine CTA ──────────────────────────────────────────────────
    urgency_color = _URGENCY_COLOR[analysis.urgency]
    story.append(Spacer(1, 16))
    cta_data = [[
        Paragraph("TALK TO A CLEARLINE DOCTOR",
                  ParagraphStyle("CH", fontSize=10, fontName="Helvetica-Bold",
                                 textColor=_WHITE, leading=13, spaceAfter=4)),
        Paragraph(_TELE_MSG[analysis.urgency],
                  ParagraphStyle("CB", fontSize=10, textColor=_WHITE, leading=15)),
    ]]
    cta = Table(cta_data, colWidths=[2.0 * inch, 4.5 * inch])
    cta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), urgency_color),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBEFORE", (1, 0), (1, 0), 1, HexColor("#FFFFFF55")),
    ]))
    story.append(cta)

    # ── Disclaimer ────────────────────────────────────────────────────────
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", color=_BORDER, thickness=0.8))
    story.append(Spacer(1, 6))
    story.append(Paragraph(_DISCLAIMER, st["disclaimer"]))

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
    base = getSampleStyleSheet()
    story: list = []

    if os.path.exists(_LOGO_PATH):
        story.append(RLImage(_LOGO_PATH, width=1.8 * inch, kind="proportional"))
        story.append(Spacer(1, 8))

    story.append(Paragraph(
        f"{company_name} — Workforce Health Screening Summary",
        ParagraphStyle("T", parent=base["Title"], fontSize=20, textColor=_NAVY),
    ))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y')}  ·  {len(rows)} enrollees screened",
        ParagraphStyle("Sub", parent=base["Normal"], fontSize=11, textColor=_GREY),
    ))
    story.append(HRFlowable(width="100%", color=_TEAL, thickness=2))
    story.append(Spacer(1, 16))

    if analyses:
        avg_score = int(sum(a.health_score for a in analyses) / len(analyses))
        counts = {u: sum(1 for a in analyses if a.urgency == u) for u in UrgencyLevel}
        summary = [
            ["Metric", "Count / Score"],
            ["Average Health Score", f"{avg_score} / 100"],
            ["All Clear (Routine)", str(counts[UrgencyLevel.routine])],
            ["Keep an Eye On It (Watch)", str(counts[UrgencyLevel.watch])],
            ["Needs Attention (Urgent)", str(counts[UrgencyLevel.urgent])],
            ["Seek Care Now (Critical)", str(counts[UrgencyLevel.critical])],
        ]
        t = Table(summary, colWidths=[3.2 * inch, 3.3 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), _WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_NAVY_LIGHT, _WHITE]),
            ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
            ("PADDING", (0, 0), (-1, -1), 9),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
        ]))
        story.append(t)

    doc.build(story)
    return out_path
