from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    title: str
    doc_type: str
    file_name: str
    content_type: Optional[str]
    file_size: Optional[int]
    ingest_status: str
    ingested_at: Optional[datetime]
    pages_done: int
    pages_total: int
    uploaded_by: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
