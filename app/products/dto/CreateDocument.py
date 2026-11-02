from typing import Literal
from pydantic import BaseModel, Field

class CreateDocument(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    doc_type: Literal["manual", "repair_guide", "specification", "other"] = "other"
