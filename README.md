# aimops

Artifact-centric image operations lab.

Supports upload, metadata handling, format conversion, parametric transformations, and classification through a decoupled API-first workflow.

Model/AI-based fake detection features are still in active development.

## How we work

Every uploaded image is treated as an immutable original artifact.

Each capability runs independently:
- Extract, import, export, and strip metadata.
- Convert artifacts across supported image formats.
- Apply subtle parametric pixel-level transformations.
- Run classification on original or derived artifacts.

Operations and derived artifacts are recorded to trace lineage and support reproducibility.

## Quick start

1. Create and use `aimosvenv` for local Python tooling:

```bash
python3 -m venv aimosvenv
source aimosvenv/bin/activate
pip install -e backend
```

2. Start with Docker:

```bash
docker compose up --build
```

## Service URLs

Service endpoints:
- Backend docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`
