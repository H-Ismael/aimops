import json
from pathlib import Path

from PIL import Image

from app.core.config import (
    ALLOWED_FORMATS,
    PREVIEWS_DIR,
    PROCESSED_DIR,
    SUPPORTED_OUTPUT_FORMATS,
    UPLOADS_ORIGINAL_DIR,
)
from app.core.database import get_conn
from app.core.storage import new_id, now_iso, sha256_file


def _row_to_dict(row):
    return dict(row) if row else None


def get_artifact(artifact_id: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
    return _row_to_dict(row)


def list_images():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM images ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def get_image(image_id: str):
    with get_conn() as conn:
        img = conn.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
        artifacts = conn.execute(
            "SELECT * FROM artifacts WHERE image_id = ? ORDER BY created_at DESC", (image_id,)
        ).fetchall()
    return _row_to_dict(img), [dict(a) for a in artifacts]


def save_upload(file_name: str, content_type: str, data: bytes):
    if content_type not in ALLOWED_FORMATS:
        raise ValueError("Unsupported mime type")

    image_id = new_id("img")
    artifact_id = new_id("art")
    ext = ALLOWED_FORMATS[content_type]
    stored = UPLOADS_ORIGINAL_DIR / f"{image_id}.{ext}"
    stored.write_bytes(data)

    with Image.open(stored) as img:
        width, height = img.size
        fmt = (img.format or ext).lower()
        preview = PREVIEWS_DIR / f"{artifact_id}.webp"
        p = img.convert("RGB")
        p.thumbnail((768, 768))
        p.save(preview, format="WEBP", quality=85)

    sha = sha256_file(stored)
    ts = now_iso()
    rel = str(stored)

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO images (id, original_filename, created_at) VALUES (?, ?, ?)",
            (image_id, file_name, ts),
        )
        conn.execute(
            """INSERT INTO artifacts
            (id, image_id, parent_artifact_id, artifact_type, stored_path, mime_type, width, height, format, sha256, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (artifact_id, image_id, None, "original", rel, content_type, width, height, fmt, sha, ts),
        )
    return image_id, artifact_id


def create_derived_artifact(source_artifact_id: str, artifact_type: str, out_path: Path, mime_type: str):
    source = get_artifact(source_artifact_id)
    if not source:
        raise ValueError("Source artifact not found")

    with Image.open(out_path) as img:
        width, height = img.size
        fmt = (img.format or out_path.suffix.lstrip(".")).lower()

    artifact_id = new_id("art")
    ts = now_iso()
    sha = sha256_file(out_path)
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO artifacts
            (id, image_id, parent_artifact_id, artifact_type, stored_path, mime_type, width, height, format, sha256, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                artifact_id,
                source["image_id"],
                source_artifact_id,
                artifact_type,
                str(out_path),
                mime_type,
                width,
                height,
                fmt,
                sha,
                ts,
            ),
        )
    return artifact_id


def validate_output_format(fmt: str) -> str:
    norm = fmt.lower().strip(".")
    if norm == "jpg":
        norm = "jpeg"
    if norm not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError("Unsupported output format")
    return norm


def ensure_processed_dir(image_id: str) -> Path:
    path = PROCESSED_DIR / image_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def operation_insert(source_artifact_id: str, output_artifact_id: str | None, operation_type: str, params: dict, metrics: dict | None, status: str = "done"):
    op_id = new_id("op")
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO operations (id, source_artifact_id, output_artifact_id, operation_type, params_json, metrics_json, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                op_id,
                source_artifact_id,
                output_artifact_id,
                operation_type,
                json.dumps(params),
                json.dumps(metrics or {}),
                status,
                now_iso(),
            ),
        )
    return op_id


def list_operations_for_artifact(artifact_id: str):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM operations WHERE source_artifact_id = ? OR output_artifact_id = ? ORDER BY created_at DESC",
            (artifact_id, artifact_id),
        ).fetchall()
    return [dict(r) for r in rows]


def get_operation(operation_id: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM operations WHERE id = ?", (operation_id,)).fetchone()
    return _row_to_dict(row)
