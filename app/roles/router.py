from typing import List
from fastapi import APIRouter, Depends
from app.roles.dto.RoleResponse import RoleResponse
from app.roles.dto.PermissionResponse import PermissionResponse
from app.roles.dto.SyncPermissionsRequest import SyncPermissionsRequest
from app.roles.dto.SyncRolesRequest import SyncRolesRequest
from app.roles.dto.UserAccessResponse import UserAccessResponse
from app.roles.service import RoleService
from app.auth.dependecies import get_current_user, require_permissions

router = APIRouter(prefix="", tags=['role'])

@router.get("/user/me/access", response_model=UserAccessResponse)
def get_my_access(service: RoleService = Depends(), current_user = Depends(get_current_user)):
    return service.get_user_access(current_user.id)

@router.put("/role/{role_id}/permissions", response_model=List[PermissionResponse])
def sync_role_permissions(role_id: int, data: SyncPermissionsRequest, service: RoleService = Depends(), current_user = Depends(require_permissions("role.manage"))):
    return service.sync_role_permissions(role_id, data)

@router.put("/user/{user_id}/roles", response_model=List[RoleResponse])
def sync_user_roles(user_id: int, data: SyncRolesRequest, service: RoleService = Depends(), current_user = Depends(require_permissions("user.manage"))):
    return service.sync_user_roles(user_id, data, current_user)
