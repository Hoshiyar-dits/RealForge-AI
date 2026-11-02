from fastapi import APIRouter, Depends
from app.assistant.dto.AskRequest import AskRequest
from app.assistant.dto.AskResponse import AskResponse
from app.assistant.service import AssistantService
from app.auth.dependecies import require_permissions

router = APIRouter(prefix="/assistant", tags=['assistant'])

@router.post("/product-chat", response_model=AskResponse)
def product_chat(data: AskRequest, service: AssistantService = Depends(), current_user = Depends(require_permissions("assistant.product"))):
    return service.ask("product", data)

@router.post("/technician-chat", response_model=AskResponse)
def technician_chat(data: AskRequest, service: AssistantService = Depends(), current_user = Depends(require_permissions("assistant.technician"))):
    return service.ask("technician", data)

@router.post("/admin-chat", response_model=AskResponse)
def admin_chat(data: AskRequest, service: AssistantService = Depends(), current_user = Depends(require_permissions("assistant.admin"))):
    return service.ask("admin", data)
