from typing import Literal, Optional
from pydantic import BaseModel, Field

class UpdateRole(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, pattern=r"^[a-z0-9_-]+$")
    description: Optional[str] = Field(None, max_length=255)
    status: Optional[Literal["0", "1"]] = None
