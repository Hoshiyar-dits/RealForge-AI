from typing import List
from pydantic import BaseModel

class UserAccessResponse(BaseModel):
    user_id: int
    roles: List[str]
    permissions: List[str]
