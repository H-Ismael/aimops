from pydantic import BaseModel


class ClassifyRequest(BaseModel):
    model_ids: list[str]
    top_k: int = 5
