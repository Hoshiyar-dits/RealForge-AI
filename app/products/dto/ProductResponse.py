from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

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
