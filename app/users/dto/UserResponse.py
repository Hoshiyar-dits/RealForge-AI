from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    email: str
    photo: Optional[str]
    email_verified_at: Optional[datetime]
    created_at: Optional[datetime]
