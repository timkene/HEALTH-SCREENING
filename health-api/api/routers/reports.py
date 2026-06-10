from fastapi import APIRouter, Depends
from api.core.security import require_api_key

router = APIRouter()


@router.get("/batch/{batch_id}")
async def get_batch(batch_id: str, _: str = Depends(require_api_key)):
    return {"batch_id": batch_id, "reports": []}
