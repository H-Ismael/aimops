from pydantic import BaseModel


class ImageResponse(BaseModel):
    id: str
    original_filename: str | None
    created_at: str


class UploadResponse(BaseModel):
    image_id: str
    artifact_id: str
    preview_url: str
