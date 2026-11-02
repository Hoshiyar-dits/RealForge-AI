from typing import Optional
from pydantic import BaseModel

class SourceResponse(BaseModel):
    document_id: int
    title: str
    doc_type: str
    product_id: Optional[int]
    page: Optional[int]
