from typing import List
from fastapi import APIRouter, Depends, status
from app.users.dto.CreateUser import CreateUser
from app.users.dto.UserResponse import UserResponse
from app.users.service import UserService
from app.auth.dto.MessageResponse import MessageResponse
from app.auth.dependecies import get_current_user, require_permissions

router = APIRouter(prefix="/user", tags=['user'])

@router.get("/me", response_model=UserResponse)
def get_me(current_user = Depends(get_current_user)):
    return current_user

@router.get("", response_model=List[UserResponse])
def list_users(service: UserService = Depends(), current_user = Depends(require_permissions("user.manage"))):
    return service.list_users()

# technicians

@router.post("/technician", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_technician(data: CreateUser, service: UserService = Depends(), current_user = Depends(require_permissions("technician.manage"))):
    return service.create_technician(data)

@router.get("/technician", response_model=List[UserResponse])
def list_technicians(service: UserService = Depends(), current_user = Depends(require_permissions("technician.manage"))):
    return service.list_technicians()

@router.get("/technician/{user_id}", response_model=UserResponse)
def get_technician(user_id: int, service: UserService = Depends(), current_user = Depends(require_permissions("technician.manage"))):
    return service.get_technician(user_id)

@router.put("/technician/{user_id}", response_model=UserResponse)
def update_technician(user_id: int, data: CreateUser, service: UserService = Depends(), current_user = Depends(require_permissions("technician.manage"))):
    return service.update_technician(user_id, data)

@router.delete("/technician/{user_id}", response_model=MessageResponse)
def delete_technician(user_id: int, service: UserService = Depends(), current_user = Depends(require_permissions("technician.manage"))):
    return service.delete_technician(user_id)
