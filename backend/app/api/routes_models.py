from fastapi import APIRouter, HTTPException

from app.schemas.classification import ClassifyRequest
from app.services.model_service import classify_artifact, list_classifications_for_artifact, list_models, sync_models_from_registry

router = APIRouter(tags=["models"])


@router.get("/models")
def models_list():
    return list_models()


@router.post("/models/reload")
def models_reload():
    sync_models_from_registry()
    return {"message": "models reloaded"}


@router.post("/artifacts/{artifact_id}/classify")
def classify_endpoint(artifact_id: str, req: ClassifyRequest):
    try:
        return classify_artifact(artifact_id, req.model_ids, req.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/artifacts/{artifact_id}/classifications")
def list_classification(artifact_id: str):
    return list_classifications_for_artifact(artifact_id)
