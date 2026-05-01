from fastapi import APIRouter, HTTPException

from app.schemas.mask import MaskRequest
from app.services.mask_service import apply_mask

router = APIRouter(prefix="/artifacts/{artifact_id}", tags=["mask"])


@router.post("/mask")
def mask_endpoint(artifact_id: str, req: MaskRequest):
    try:
        return apply_mask(artifact_id, req.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
