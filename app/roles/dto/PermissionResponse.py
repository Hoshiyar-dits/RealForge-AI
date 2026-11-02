from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
