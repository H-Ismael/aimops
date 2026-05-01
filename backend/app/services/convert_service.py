from pathlib import Path

from PIL import Image

from app.core.storage import new_id
from app.services.artifact_service import create_derived_artifact, ensure_processed_dir, get_artifact, operation_insert, validate_output_format


def convert_artifact(artifact_id: str, output_format: str, quality: int, preserve_metadata: bool):
    artifact = get_artifact(artifact_id)
    if not artifact:
        raise ValueError("Artifact not found")

    fmt = validate_output_format(output_format)
    src = Path(artifact["stored_path"])
    out_dir = ensure_processed_dir(artifact["image_id"])
    out_path = out_dir / f"{new_id('conv')}.{fmt}"

    with Image.open(src) as img:
        kwargs = {}
        if fmt in {"jpeg", "webp"}:
            kwargs["quality"] = max(1, min(100, quality))
        if preserve_metadata and "exif" in img.info:
            kwargs["exif"] = img.info["exif"]
        img.convert("RGB").save(out_path, format=fmt.upper(), **kwargs)

    out_art = create_derived_artifact(artifact_id, "converted", out_path, f"image/{fmt}")
    op_id = operation_insert(
        artifact_id,
        out_art,
        "convert_format",
        {"output_format": fmt, "quality": quality, "preserve_metadata": preserve_metadata},
        None,
    )
    return {"operation_id": op_id, "output_artifact_id": out_art, "output_format": fmt}
