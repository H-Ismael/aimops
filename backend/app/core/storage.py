import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .config import (
    METADATA_DIR,
    MODELS_CACHE_DIR,
    OPERATIONS_DIR,
    PREVIEWS_DIR,
    PROCESSED_DIR,
    UPLOADS_ORIGINAL_DIR,
)


def ensure_dirs() -> None:
    for p in [
        UPLOADS_ORIGINAL_DIR,
        PROCESSED_DIR,
        PREVIEWS_DIR,
        METADATA_DIR,
        OPERATIONS_DIR,
        MODELS_CACHE_DIR,
    ]:
        p.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()
