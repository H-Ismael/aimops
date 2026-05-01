import json
import subprocess
from pathlib import Path

from PIL import Image, ExifTags

from app.core.config import METADATA_DIR
from app.core.database import get_conn
from app.core.storage import new_id, now_iso
from app.services.artifact_service import create_derived_artifact, ensure_processed_dir, get_artifact, operation_insert, validate_output_format


def _artifact_path(artifact: dict) -> Path:
    return Path(artifact["stored_path"])


GPS_TAGS = ExifTags.GPSTAGS


def _safe_value(value):
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_safe_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _safe_value(v) for k, v in value.items()}
    return str(value)


def _extract_from_pillow(img: Image.Image) -> dict:
    exif_data = {}
    gps_data = {}

    exif_raw = img.getexif()
    if not exif_raw and hasattr(img, "_getexif"):
        exif_legacy = img._getexif()  # pylint: disable=protected-access
        if exif_legacy:
            exif_raw = exif_legacy

    for k, v in dict(exif_raw).items():
        name = ExifTags.TAGS.get(k, str(k))
        if name == "GPSInfo" and isinstance(v, dict):
            for gps_k, gps_v in v.items():
                gps_name = GPS_TAGS.get(gps_k, str(gps_k))
                gps_data[gps_name] = _safe_value(gps_v)
        else:
            exif_data[name] = _safe_value(v)

    info = img.info or {}
    xmp = info.get("xmp") or info.get("XML:com.adobe.xmp")
    if isinstance(xmp, bytes):
        xmp = xmp.decode("utf-8", errors="replace")

    icc_profile = info.get("icc_profile")
    icc = {
        "present": icc_profile is not None,
        "byte_size": len(icc_profile) if isinstance(icc_profile, (bytes, bytearray)) else 0,
    }

    text_fields = {}
    for key, value in info.items():
        if key.lower() in {"xmp", "xml:com.adobe.xmp", "icc_profile", "exif"}:
            continue
        if isinstance(value, (str, int, float, bool)):
            text_fields[key] = value

    return {
        "exif": exif_data,
        "gps": gps_data,
        "icc": icc,
        "xmp": xmp,
        "text": text_fields,
    }


def _extract_from_exiftool(path: Path) -> dict | None:
    try:
        proc = subprocess.run(
            ["exiftool", "-j", "-G", "-n", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    try:
        parsed = json.loads(proc.stdout)
        if not parsed or not isinstance(parsed, list):
            return None
        record = parsed[0]
    except json.JSONDecodeError:
        return None

    exif_data = {}
    gps_data = {}
    icc_data = {}
    xmp_data = {}
    other = {}

    for key, value in record.items():
        if key == "SourceFile":
            continue
        normalized = _safe_value(value)
        lower = key.lower()
        if "gps" in lower:
            gps_data[key] = normalized
        elif "icc" in lower or lower.startswith("[icc_profile]"):
            icc_data[key] = normalized
        elif "xmp" in lower or lower.startswith("[xmp]"):
            xmp_data[key] = normalized
        elif "exif" in lower or lower.startswith("[exif]"):
            exif_data[key] = normalized
        else:
            other[key] = normalized

    return {
        "exif": exif_data,
        "gps": gps_data,
        "icc": {
            "present": len(icc_data) > 0,
            "byte_size": 0,
            "tags": icc_data,
        },
        "xmp": xmp_data if xmp_data else None,
        "text": other,
    }


def extract_metadata(artifact_id: str):
    artifact = get_artifact(artifact_id)
    if not artifact:
        raise ValueError("Artifact not found")

    path = _artifact_path(artifact)
    data = {
        "artifact_id": artifact_id,
        "format": artifact.get("format"),
        "width": artifact.get("width"),
        "height": artifact.get("height"),
        "extractor": "pillow",
        "exif": {},
        "gps": {},
        "icc": {"present": False, "byte_size": 0, "tags": {}},
        "xmp": None,
        "text": {},
    }

    parsed_exiftool = _extract_from_exiftool(path)
    if parsed_exiftool:
        data["extractor"] = "exiftool"
        data["exif"] = parsed_exiftool["exif"]
        data["gps"] = parsed_exiftool["gps"]
        data["icc"] = parsed_exiftool["icc"]
        data["xmp"] = parsed_exiftool["xmp"]
        data["text"] = parsed_exiftool["text"]
    else:
        with Image.open(path) as img:
            parsed = _extract_from_pillow(img)
            data["exif"] = parsed["exif"]
            data["gps"] = parsed["gps"]
            data["icc"] = parsed["icc"]
            data["xmp"] = parsed["xmp"]
            data["text"] = parsed["text"]

    md_id = new_id("md")
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO metadata_records (id, artifact_id, metadata_json, source, created_at) VALUES (?, ?, ?, ?, ?)",
            (md_id, artifact_id, json.dumps(data), "extracted", now_iso()),
        )

    image_id = artifact["image_id"]
    out_dir = METADATA_DIR / image_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"extracted_{md_id}.json"
    out_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    operation_insert(artifact_id, None, "metadata_extract", {"artifact_id": artifact_id}, None)
    return {"metadata_id": md_id, "metadata": data, "path": str(out_file)}


def import_metadata(artifact_id: str, content: dict, source_format: str):
    artifact = get_artifact(artifact_id)
    if not artifact:
        raise ValueError("Artifact not found")

    md_id = new_id("md")
    payload = {
        "artifact_id": artifact_id,
        "source_format": source_format,
        "content": content,
    }
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO metadata_records (id, artifact_id, metadata_json, source, created_at) VALUES (?, ?, ?, ?, ?)",
            (md_id, artifact_id, json.dumps(payload), "imported", now_iso()),
        )

    out_dir = METADATA_DIR / artifact["image_id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"imported_{md_id}.json"
    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    operation_insert(artifact_id, None, "metadata_import", {"source_format": source_format}, None)
    return {"metadata_id": md_id, "path": str(out_file)}


def get_metadata_by_source(artifact_id: str, source: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM metadata_records WHERE artifact_id = ? AND source = ? ORDER BY created_at DESC LIMIT 1",
            (artifact_id, source),
        ).fetchone()
    return dict(row) if row else None


def strip_metadata(artifact_id: str, mode: str, output_format: str, export_removed_metadata: bool):
    artifact = get_artifact(artifact_id)
    if not artifact:
        raise ValueError("Artifact not found")

    norm = validate_output_format(output_format)
    source_path = _artifact_path(artifact)
    out_dir = ensure_processed_dir(artifact["image_id"])
    out_path = out_dir / f"{new_id('stripped')}.{norm}"

    with Image.open(source_path) as img:
        clean = Image.new(img.mode, img.size)
        clean.putdata(list(img.getdata()))
        save_kwargs = {}
        if norm in {"jpeg", "jpg", "webp"}:
            save_kwargs["quality"] = 95
        clean.save(out_path, format=norm.upper(), **save_kwargs)

    out_art_id = create_derived_artifact(artifact_id, "metadata_stripped", out_path, f"image/{norm}")

    export_path = None
    if export_removed_metadata:
        extracted = extract_metadata(artifact_id)
        export_path = extracted["path"]

    op_id = operation_insert(
        artifact_id,
        out_art_id,
        "metadata_strip",
        {
            "mode": mode,
            "output_format": norm,
            "export_removed_metadata": export_removed_metadata,
        },
        None,
    )

    return {
        "operation_id": op_id,
        "source_artifact_id": artifact_id,
        "processed_artifact_id": out_art_id,
        "metadata_removed": True,
        "metadata_export_path": export_path,
        "output_format": norm,
    }
