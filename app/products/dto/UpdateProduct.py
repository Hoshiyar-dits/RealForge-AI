from typing import Literal, Optional
from pydantic import BaseModel, Field

class UpdateProduct(BaseModel):
    # sent as multipart form; files sent with it replace the product's documents
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    model_number: Optional[str] = Field(None, min_length=1, max_length=255)
    brand: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    status: Optional[Literal["0", "1"]] = None
    doc_type: Literal["manual", "repair_guide", "specification", "other"] = "manual"
