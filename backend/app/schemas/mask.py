from pydantic import BaseModel


class MaskRequest(BaseModel):
    mask_type: str = "gaussian_noise"
    strength: float = 0.01
    coverage: float = 0.15
    seed: int = 42
    distribution: str = "uniform_spatial"
    per_channel: bool = True
    preserve_edges: bool = False
    output_format: str = "png"
