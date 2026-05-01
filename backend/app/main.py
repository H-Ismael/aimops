from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_artifacts import router as artifacts_router
from app.api.routes_convert import router as convert_router
from app.api.routes_images import router as images_router
from app.api.routes_masks import router as masks_router
from app.api.routes_metadata import router as metadata_router
from app.api.routes_models import router as models_router
from app.api.routes_operations import router as operations_router
from app.core.database import init_db
from app.core.storage import ensure_dirs
from app.services.model_service import sync_models_from_registry

app = FastAPI(title="aimops", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    ensure_dirs()
    init_db()
    sync_models_from_registry()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(images_router)
app.include_router(artifacts_router)
app.include_router(metadata_router)
app.include_router(convert_router)
app.include_router(masks_router)
app.include_router(models_router)
app.include_router(operations_router)
