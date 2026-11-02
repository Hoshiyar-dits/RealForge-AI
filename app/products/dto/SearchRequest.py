from pydantic import BaseModel, Field

class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    k: int = Field(5, ge=1, le=20)
