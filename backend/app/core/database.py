import sqlite3
from contextlib import contextmanager

from .config import DB_PATH

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS images (
    id TEXT PRIMARY KEY,
    original_filename TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    image_id TEXT NOT NULL,
    parent_artifact_id TEXT,
    artifact_type TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    mime_type TEXT,
    width INTEGER,
    height INTEGER,
    format TEXT,
    sha256 TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(image_id) REFERENCES images(id),
    FOREIGN KEY(parent_artifact_id) REFERENCES artifacts(id)
);

CREATE TABLE IF NOT EXISTS classifications (
    id TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    top_k INTEGER,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(artifact_id) REFERENCES artifacts(id)
);

CREATE TABLE IF NOT EXISTS metadata_records (
    id TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(artifact_id) REFERENCES artifacts(id)
);

CREATE TABLE IF NOT EXISTS operations (
    id TEXT PRIMARY KEY,
    source_artifact_id TEXT NOT NULL,
    output_artifact_id TEXT,
    operation_type TEXT NOT NULL,
    params_json TEXT,
    metrics_json TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(source_artifact_id) REFERENCES artifacts(id),
    FOREIGN KEY(output_artifact_id) REFERENCES artifacts(id)
);

CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    task TEXT NOT NULL,
    local_path TEXT,
    enabled INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    last_loaded_at TEXT
);
"""


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
