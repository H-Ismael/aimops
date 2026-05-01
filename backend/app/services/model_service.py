import json
from pathlib import Path

import yaml
from PIL import Image

from app.core.config import MODELS_CACHE_DIR
from app.core.database import get_conn
from app.core.storage import new_id, now_iso
from app.services.artifact_service import get_artifact, operation_insert

REGISTRY_PATH = Path(__file__).resolve().parents[1] / "registry" / "models.yaml"

_PIPELINES = {}


def sync_models_from_registry():
    content = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    models = content.get("models", [])
    now = now_iso()
    with get_conn() as conn:
        for m in models:
            conn.execute(
                """INSERT INTO models (id, provider, model_name, task, local_path, enabled, created_at, last_loaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET provider=excluded.provider, model_name=excluded.model_name,
                task=excluded.task, enabled=excluded.enabled""",
                (
                    m["id"],
                    m["provider"],
                    m["model_name"],
                    m["task"],
                    str(MODELS_CACHE_DIR / m["id"]),
                    1 if m.get("enabled", True) else 0,
                    now,
                    None,
                ),
            )


def list_models():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM models WHERE enabled = 1 ORDER BY id ASC").fetchall()
    return [dict(r) for r in rows]


def _load_pipeline(model_id: str, model_name: str):
    if model_id in _PIPELINES:
        return _PIPELINES[model_id]
    from transformers import pipeline

    MODELS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    clf = pipeline("image-classification", model=model_name, cache_dir=str(MODELS_CACHE_DIR))
    _PIPELINES[model_id] = clf
    with get_conn() as conn:
        conn.execute("UPDATE models SET last_loaded_at = ? WHERE id = ?", (now_iso(), model_id))
    return clf


def classify_artifact(artifact_id: str, model_ids: list[str], top_k: int):
    artifact = get_artifact(artifact_id)
    if not artifact:
        raise ValueError("Artifact not found")

    image = Image.open(artifact["stored_path"]).convert("RGB")

    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM models WHERE id IN ({','.join(['?']*len(model_ids))}) AND enabled = 1",
            tuple(model_ids),
        ).fetchall()

    if not rows:
        raise ValueError("No enabled models found")

    all_results = []
    with get_conn() as conn:
        for row in rows:
            model = dict(row)
            clf = _load_pipeline(model["id"], model["model_name"])
            preds = clf(image, top_k=top_k)
            normalized = [{"label": p["label"], "score": float(p["score"])} for p in preds]
            cls_id = new_id("cls")
            payload = {
                "artifact_id": artifact_id,
                "model_id": model["id"],
                "predictions": normalized,
            }
            conn.execute(
                "INSERT INTO classifications (id, artifact_id, model_id, top_k, result_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (cls_id, artifact_id, model["id"], top_k, json.dumps(payload), now_iso()),
            )
            operation_insert(artifact_id, None, "classification", {"model_id": model["id"], "top_k": top_k}, None)
            all_results.append({"classification_id": cls_id, **payload})

    return all_results


def list_classifications_for_artifact(artifact_id: str):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM classifications WHERE artifact_id = ? ORDER BY created_at DESC",
            (artifact_id,),
        ).fetchall()
    return [dict(r) for r in rows]
