from typing import List
from pydantic import BaseModel, Field

class AssignPermissionsRequest(BaseModel):
    permission_ids: List[int] = Field(min_length=1)
