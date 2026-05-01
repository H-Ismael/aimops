import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.schemas.metadata import MetadataExportRequest, MetadataImportRequest, MetadataStripRequest
from app.services.metadata_service import extract_metadata, get_metadata_by_source, import_metadata, strip_metadata

router = APIRouter(prefix="/artifacts/{artifact_id}/metadata", tags=["metadata"])


@router.get("")
def metadata_get_latest(artifact_id: str):
    row = get_metadata_by_source(artifact_id, "extracted")
    if not row:
        raise HTTPException(status_code=404, detail="No extracted metadata found")
    return {"metadata_id": row["id"], "metadata": json.loads(row["metadata_json"])}


@router.post("/extract")
def metadata_extract(artifact_id: str):
    try:
        return extract_metadata(artifact_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/import")
def metadata_import(artifact_id: str, req: MetadataImportRequest):
    try:
        return import_metadata(artifact_id, req.content, req.source_format)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/export")
def metadata_export(artifact_id: str, req: MetadataExportRequest):
    row = get_metadata_by_source(artifact_id, req.source)
    if not row:
        raise HTTPException(status_code=404, detail="No metadata record for source")
    payload = json.loads(row["metadata_json"])
    path = Path(__file__).resolve().parents[4] / "data" / "metadata" / payload.get("artifact_id", "unknown") / f"export_{row['id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"metadata_id": row["id"], "path": str(path)}


@router.post("/strip")
def metadata_strip(artifact_id: str, req: MetadataStripRequest):
    try:
        return strip_metadata(artifact_id, req.mode, req.output_format, req.export_removed_metadata)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
