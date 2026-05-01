from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "db" / "app.sqlite"
MODELS_CACHE_DIR = BASE_DIR / "models" / "hf_cache"

UPLOADS_ORIGINAL_DIR = DATA_DIR / "uploads" / "original"
PROCESSED_DIR = DATA_DIR / "processed"
PREVIEWS_DIR = DATA_DIR / "previews"
METADATA_DIR = DATA_DIR / "metadata"
OPERATIONS_DIR = DATA_DIR / "operations"

ALLOWED_FORMATS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/tiff": "tiff",
}

SUPPORTED_OUTPUT_FORMATS = {"jpeg", "jpg", "png", "webp", "tiff"}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
