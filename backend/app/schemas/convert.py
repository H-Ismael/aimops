from pydantic import BaseModel


class ConvertRequest(BaseModel):
    output_format: str
    quality: int = 95
    preserve_metadata: bool = False
