from fastapi import APIRouter, HTTPException

from app.schemas.convert import ConvertRequest
from app.services.convert_service import convert_artifact

router = APIRouter(prefix="/artifacts/{artifact_id}", tags=["convert"])


@router.post("/convert")
def convert_endpoint(artifact_id: str, req: ConvertRequest):
    try:
        return convert_artifact(artifact_id, req.output_format, req.quality, req.preserve_metadata)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
