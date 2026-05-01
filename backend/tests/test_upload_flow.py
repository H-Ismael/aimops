from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


def _image_bytes(fmt: str = "PNG"):
    bio = BytesIO()
    Image.new("RGB", (32, 32), color=(10, 20, 30)).save(bio, format=fmt)
    return bio.getvalue()


def test_upload_and_fetch_artifact():
    client = TestClient(app)
    payload = _image_bytes("PNG")
    res = client.post(
        "/images/upload",
        files={"file": ("t.png", payload, "image/png")},
    )
    assert res.status_code == 200
    body = res.json()
    art = client.get(f"/artifacts/{body['artifact_id']}")
    assert art.status_code == 200
    dl = client.get(f"/artifacts/{body['artifact_id']}/download")
    assert dl.status_code == 200
