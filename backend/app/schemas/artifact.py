from pydantic import BaseModel


class ArtifactResponse(BaseModel):
    id: str
    image_id: str
    parent_artifact_id: str | None
    artifact_type: str
    stored_path: str
    mime_type: str | None
    width: int | None
    height: int | None
    format: str | None
    sha256: str | None
    created_at: str
