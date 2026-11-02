from typing import Optional
from pydantic import BaseModel

class SearchResultResponse(BaseModel):
    document_id: int
    title: str
    doc_type: str
    page: Optional[int]
    content: str
    score: float
