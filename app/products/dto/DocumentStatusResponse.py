from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class DocumentStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    ingest_status: str
    pages_done: int
    pages_total: int
    ingested_at: Optional[datetime]
    updated_at: Optional[datetime]
