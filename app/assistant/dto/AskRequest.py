from typing import List, Optional
from pydantic import BaseModel, Field
from app.assistant.dto.ChatMessage import ChatMessage

class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    product_id: Optional[int] = None
    history: List[ChatMessage] = Field(default_factory=list, max_length=20)
