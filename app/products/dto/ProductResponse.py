from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.products.dto.DocumentResponse import DocumentResponse

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    model_number: str
    brand: Optional[str]
    category: Optional[str]
    description: Optional[str]
    status: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    # filled only by GET /product/{id}
    documents: List[DocumentResponse] = []
