from pathlib import Path

import numpy as np
from PIL import Image

from app.core.storage import new_id
from app.services.artifact_service import create_derived_artifact, ensure_processed_dir, get_artifact, operation_insert, validate_output_format


def _psnr(a: np.ndarray, b: np.ndarray) -> float:
    mse = np.mean((a - b) ** 2)
    if mse == 0:
        return 99.0
    return float(20 * np.log10(255.0 / np.sqrt(mse)))


def _ssim_approx(a: np.ndarray, b: np.ndarray) -> float:
    # Lightweight channel-agnostic SSIM approximation for MVP metrics.
    x = a.astype(np.float64)
    y = b.astype(np.float64)
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    mu_x = x.mean()
    mu_y = y.mean()
    sigma_x = x.var()
    sigma_y = y.var()
    sigma_xy = ((x - mu_x) * (y - mu_y)).mean()
    return float(((2 * mu_x * mu_y + c1) * (2 * sigma_xy + c2)) / ((mu_x**2 + mu_y**2 + c1) * (sigma_x + sigma_y + c2)))


def apply_mask(artifact_id: str, params: dict):
    artifact = get_artifact(artifact_id)
    if not artifact:
        raise ValueError("Artifact not found")

    fmt = validate_output_format(params["output_format"])
    src = Path(artifact["stored_path"])
    out_dir = ensure_processed_dir(artifact["image_id"])
    out_path = out_dir / f"{new_id('mask')}.{fmt}"

    rng = np.random.default_rng(params["seed"])
    strength = float(params["strength"])
    coverage = float(params["coverage"])

    with Image.open(src) as img:
        arr = np.array(img.convert("RGB"), dtype=np.float32)

    h, w, c = arr.shape
    total = h * w
    mask_count = int(total * coverage)
    indices = rng.choice(total, size=max(1, mask_count), replace=False)

    flat = arr.reshape(total, c)
    noise = rng.normal(0.0, strength * 255.0, size=(len(indices), c if params["per_channel"] else 1))
    if not params["per_channel"]:
        noise = np.repeat(noise, c, axis=1)

    original = flat.copy()
    flat[indices] = np.clip(flat[indices] + noise, 0, 255)
    out = flat.reshape(h, w, c).astype(np.uint8)
    Image.fromarray(out, mode="RGB").save(out_path, format=fmt.upper())

    changed = np.abs(flat - original)
    changed_pixels = np.any(changed > 0, axis=1).sum()
    metrics = {
        "psnr": _psnr(original.reshape(h, w, c), out.astype(np.float32)),
        "ssim": _ssim_approx(original.reshape(h, w, c), out.astype(np.float32)),
        "changed_pixel_ratio": float(changed_pixels / total),
        "mean_absolute_delta": float(np.mean(np.abs(out.astype(np.float32) - original.reshape(h, w, c)))),
    }

    out_art = create_derived_artifact(artifact_id, "masked", out_path, f"image/{fmt}")
    op_id = operation_insert(artifact_id, out_art, "mask_gaussian_noise", params, metrics)

    return {
        "operation_id": op_id,
        "source_artifact_id": artifact_id,
        "output_artifact_id": out_art,
        "metrics": metrics,
    }
