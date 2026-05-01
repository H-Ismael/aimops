from pydantic import BaseModel


class MetadataImportRequest(BaseModel):
    content: dict
    source_format: str = "json"


class MetadataExportRequest(BaseModel):
    source: str = "extracted"


class MetadataStripRequest(BaseModel):
    mode: str = "strip_all"
    output_format: str = "png"
    export_removed_metadata: bool = True
