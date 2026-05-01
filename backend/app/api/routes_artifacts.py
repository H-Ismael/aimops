from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services.artifact_service import get_artifact

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/{artifact_id}")
def get_artifact_detail(artifact_id: str):
    artifact = get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.get("/{artifact_id}/preview")
def artifact_preview(artifact_id: str):
    p = Path(__file__).resolve().parents[4] / "data" / "previews" / f"{artifact_id}.webp"
    if not p.exists():
        raise HTTPException(status_code=404, detail="Preview not found")
    return FileResponse(p, media_type="image/webp")


@router.get("/{artifact_id}/download")
def artifact_download(artifact_id: str):
    artifact = get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    p = Path(artifact["stored_path"])
    if not p.exists():
        raise HTTPException(status_code=404, detail="File missing on disk")
    return FileResponse(p, media_type=artifact.get("mime_type") or "application/octet-stream", filename=p.name)
