from typing import List
from pydantic import BaseModel
from app.assistant.dto.SourceResponse import SourceResponse

class AskResponse(BaseModel):
    answer: str
    sources: List[SourceResponse]
