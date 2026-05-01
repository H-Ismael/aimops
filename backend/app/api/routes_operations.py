from fastapi import APIRouter, HTTPException

from app.services.artifact_service import get_operation, list_operations_for_artifact

router = APIRouter(tags=["operations"])


@router.get("/artifacts/{artifact_id}/operations")
def operations_for_artifact(artifact_id: str):
    return list_operations_for_artifact(artifact_id)


@router.get("/operations/{operation_id}")
def operation_detail(operation_id: str):
    op = get_operation(operation_id)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    return op
