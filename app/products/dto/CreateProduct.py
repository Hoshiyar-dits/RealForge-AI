from typing import Literal, Optional
from pydantic import BaseModel, Field

class CreateProduct(BaseModel):
    # sent as multipart form together with optional files
    name: str = Field(min_length=1, max_length=255)
    model_number: str = Field(min_length=1, max_length=255)
    brand: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    doc_type: Literal["manual", "repair_guide", "specification", "other"] = "manual"
