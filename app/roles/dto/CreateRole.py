from typing import Optional
from pydantic import BaseModel, Field

class CreateRole(BaseModel):
    name: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9_-]+$")
    description: Optional[str] = Field(None, max_length=255)
