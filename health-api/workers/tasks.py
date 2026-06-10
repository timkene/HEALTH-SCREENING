from __future__ import annotations
import json
import tempfile
from celery import Celery
from api.core.config import get_settings

_settings = get_settings()
celery_app = Celery("health_api", broker=_settings.redis_url, backend=_settings.redis_url)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"


@celery_app.task(bind=True)
def generate_batch_task(self, batch_id: str) -> dict:
    from api.core.database import get_db
    from api.services.klaire_service import analyse_enrollee
    from api.services.report_service import generate_individual_pdf, generate_company_pdf
    from api.models.health_data import EnrolleeRow
    from api.services.email_service import send_alert_to_tele_team

    conn = get_db()
    rows_data = conn.execute(
        "SELECT * FROM enrollees WHERE batch_id = ?", [batch_id]
    ).fetchall()
    cols = [d[0] for d in conn.description]

    tmp_dir = tempfile.mkdtemp(prefix=f"batch_{batch_id}_")
    analyses = []
    rows = []
    failed = []

    for i, rd in enumerate(rows_data):
        row = EnrolleeRow(**dict(zip(cols, rd)))
        try:
            analysis = analyse_enrollee(row)
            pdf_path = generate_individual_pdf(row, analysis, tmp_dir)
            conn.execute("""
                INSERT OR REPLACE INTO report_meta (enrollee_id, batch_id, pdf_path)
                VALUES (?, ?, ?)
            """, [row.enrollee_id, batch_id, pdf_path])
            conn.execute("""
                INSERT OR REPLACE INTO klaire_analyses
                  (enrollee_id, batch_id, health_score, urgency, klaire_flags, next_steps)
                VALUES (?,?,?,?,?,?)
            """, [
                row.enrollee_id, batch_id, analysis.health_score,
                analysis.urgency.value, analysis.klaire_flags,
                json.dumps(analysis.next_steps),
            ])
            if analysis.urgency.value == "critical":
                send_alert_to_tele_team(row.name, row.enrollee_id, analysis.urgency.value)
            analyses.append(analysis)
            rows.append(row)
        except Exception as exc:
            failed.append({"enrollee_id": row.enrollee_id, "error": str(exc)})
        self.update_state(state="PROGRESS",
                         meta={"total": len(rows_data), "completed": i + 1})

    if rows:
        company_name = rows[0].company_name or "Company"
        company_pdf = generate_company_pdf(company_name, rows, analyses, tmp_dir)
        conn.execute("""
            INSERT OR REPLACE INTO report_meta (enrollee_id, batch_id, pdf_path)
            VALUES ('COMPANY', ?, ?)
        """, [batch_id, company_pdf])

    return {"completed": len(rows), "failed": len(failed), "failed_ids": [f["enrollee_id"] for f in failed]}


@celery_app.task(bind=True)
def bulk_email_task(self, batch_id: str, method: str = "zoho") -> dict:
    from api.core.database import get_db
    from api.services.email_service import send_via_zoho, send_via_smtp

    conn = get_db()
    rows = conn.execute(
        "SELECT e.enrollee_id, e.name, e.email, rm.pdf_path FROM enrollees e "
        "JOIN report_meta rm USING (enrollee_id) WHERE e.batch_id = ? AND e.email IS NOT NULL",
        [batch_id],
    ).fetchall()

    completed = 0
    failed = []
    for enrollee_id, name, email, pdf_path in rows:
        try:
            ok = send_via_zoho(email, name, pdf_path) if method == "zoho" else send_via_smtp(email, name, pdf_path)
            if ok:
                conn.execute("UPDATE report_meta SET email_sent = TRUE WHERE enrollee_id = ?", [enrollee_id])
                completed += 1
            else:
                failed.append(enrollee_id)
        except Exception:
            failed.append(enrollee_id)
        self.update_state(state="PROGRESS",
                         meta={"total": len(rows), "completed": completed})
    return {"completed": completed, "failed": len(failed), "failed_ids": failed}
