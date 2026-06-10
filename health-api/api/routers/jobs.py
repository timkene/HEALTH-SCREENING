from fastapi import APIRouter, Depends, HTTPException
from api.core.security import require_api_key
from api.models.responses import JobStatus

router = APIRouter()


@router.get("/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str, _: str = Depends(require_api_key)) -> JobStatus:
    from workers.tasks import celery_app
    result = celery_app.AsyncResult(job_id)
    meta = result.info or {}
    return JobStatus(
        job_id=job_id,
        status=result.state.lower() if result.state else "unknown",
        total=meta.get("total", 0) if isinstance(meta, dict) else 0,
        completed=meta.get("completed", 0) if isinstance(meta, dict) else 0,
        failed_ids=meta.get("failed_ids", []) if isinstance(meta, dict) else [],
    )


@router.get("/{job_id}/progress")
async def get_progress(job_id: str, _: str = Depends(require_api_key)) -> dict:
    from workers.tasks import celery_app
    result = celery_app.AsyncResult(job_id)
    meta = result.info if isinstance(result.info, dict) else {}
    return {
        "job_id": job_id,
        "state": result.state,
        "total": meta.get("total", 0),
        "completed": meta.get("completed", 0),
    }
