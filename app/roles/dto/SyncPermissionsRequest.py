from typing import List
from pydantic import BaseModel

class SyncPermissionsRequest(BaseModel):
    permission_ids: List[int]
