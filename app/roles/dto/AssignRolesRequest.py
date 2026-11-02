from typing import List
from pydantic import BaseModel, Field

class AssignRolesRequest(BaseModel):
    role_ids: List[int] = Field(min_length=1)
