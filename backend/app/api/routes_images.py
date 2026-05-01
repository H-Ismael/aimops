from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import MAX_UPLOAD_BYTES
from app.services.artifact_service import get_image, list_images, save_upload

router = APIRouter(prefix="/images", tags=["images"])


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large")
    try:
        image_id, artifact_id = save_upload(file.filename, file.content_type or "", data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "image_id": image_id,
        "artifact_id": artifact_id,
        "preview_url": f"/artifacts/{artifact_id}/preview",
    }


@router.get("")
def get_images():
    return list_images()


@router.get("/{image_id}")
def get_single_image(image_id: str):
    image, artifacts = get_image(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"image": image, "artifacts": artifacts}
