from fastapi import Depends, HTTPException, status
from app.knowledge.service import KnowledgeService
from app.products.repository import ProductRepository
from app.assistant.dto.AskResponse import AskResponse

class AssistantService():
    def __init__(self, knowledge_service: KnowledgeService = Depends(), product_repository: ProductRepository = Depends()):
        self.knowledge_service = knowledge_service
        self.product_repository = product_repository

    def ask(self, role: str, data) -> AskResponse:
        # TODO: answer data.question for the given role ("product", "technician" or "admin")
        # data has question, product_id and history; return AskResponse(answer=..., sources=[...])
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="The assistant is not written yet")
