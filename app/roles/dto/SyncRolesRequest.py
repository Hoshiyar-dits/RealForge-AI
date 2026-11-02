from typing import List
from pydantic import BaseModel

class SyncRolesRequest(BaseModel):
    role_ids: List[int]
