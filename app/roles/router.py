from typing import List
from fastapi import APIRouter, Depends, status
from app.roles.dto.CreateRole import CreateRole
from app.roles.dto.UpdateRole import UpdateRole
from app.roles.dto.RoleResponse import RoleResponse
from app.roles.dto.CreatePermission import CreatePermission
from app.roles.dto.UpdatePermission import UpdatePermission
from app.roles.dto.PermissionResponse import PermissionResponse
from app.roles.dto.AssignPermissionsRequest import AssignPermissionsRequest
from app.roles.dto.AssignRolesRequest import AssignRolesRequest
from app.roles.dto.UserAccessResponse import UserAccessResponse
from app.roles.service import RoleService
from app.auth.dto.MessageResponse import MessageResponse
from app.auth.dependecies import get_current_user, require_permissions

router = APIRouter(prefix="", tags=['role'])

# roles

@router.post("/role", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(data: CreateRole, service: RoleService = Depends(), current_user = Depends(require_permissions("role.manage"))):
    return service.create_role(data)

@router.get("/role", response_model=List[RoleResponse])
def list_roles(service: RoleService = Depends(), current_user = Depends(require_permissions("role.manage"))):
    return service.list_roles()

@router.get("/role/{role_id}", response_model=RoleResponse)
def get_role(role_id: int, service: RoleService = Depends(), current_user = Depends(require_permissions("role.manage"))):
    return service.get_role(role_id)

@router.patch("/role/{role_id}", response_model=RoleResponse)
def update_role(role_id: int, data: UpdateRole, service: RoleService = Depends(), current_user = Depends(require_permissions("role.manage"))):
    return service.update_role(role_id, data)

@router.delete("/role/{role_id}", response_model=MessageResponse)
def delete_role(role_id: int, service: RoleService = Depends(), current_user = Depends(require_permissions("role.manage"))):
    return service.delete_role(role_id)

# role -> permissions

@router.get("/role/{role_id}/permissions", response_model=List[PermissionResponse])
def list_role_permissions(role_id: int, service: RoleService = Depends(), current_user = Depends(require_permissions("role.manage"))):
    return service.list_role_permissions(role_id)

@router.post("/role/{role_id}/permissions", response_model=List[PermissionResponse])
def assign_role_permissions(role_id: int, data: AssignPermissionsRequest, service: RoleService = Depends(), current_user = Depends(require_permissions("role.manage"))):
    return service.assign_role_permissions(role_id, data)

@router.delete("/role/{role_id}/permissions/{permission_id}", response_model=MessageResponse)
def revoke_role_permission(role_id: int, permission_id: int, service: RoleService = Depends(), current_user = Depends(require_permissions("role.manage"))):
    return service.revoke_role_permission(role_id, permission_id)

# permissions

@router.post("/permission", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
def create_permission(data: CreatePermission, service: RoleService = Depends(), current_user = Depends(require_permissions("permission.manage"))):
    return service.create_permission(data)

@router.get("/permission", response_model=List[PermissionResponse])
def list_permissions(service: RoleService = Depends(), current_user = Depends(require_permissions("permission.manage"))):
    return service.list_permissions()

@router.get("/permission/{permission_id}", response_model=PermissionResponse)
def get_permission(permission_id: int, service: RoleService = Depends(), current_user = Depends(require_permissions("permission.manage"))):
    return service.get_permission(permission_id)

@router.patch("/permission/{permission_id}", response_model=PermissionResponse)
def update_permission(permission_id: int, data: UpdatePermission, service: RoleService = Depends(), current_user = Depends(require_permissions("permission.manage"))):
    return service.update_permission(permission_id, data)

@router.delete("/permission/{permission_id}", response_model=MessageResponse)
def delete_permission(permission_id: int, service: RoleService = Depends(), current_user = Depends(require_permissions("permission.manage"))):
    return service.delete_permission(permission_id)

# user -> roles / permissions ("/user/me/access" must stay above "/user/{user_id}/...")

@router.get("/user/me/access", response_model=UserAccessResponse)
def get_my_access(service: RoleService = Depends(), current_user = Depends(get_current_user)):
    return service.get_user_access(current_user.id)

@router.get("/user/{user_id}/access", response_model=UserAccessResponse)
def get_user_access(user_id: int, service: RoleService = Depends(), current_user = Depends(require_permissions("user.manage"))):
    return service.get_user_access(user_id)

@router.get("/user/{user_id}/roles", response_model=List[RoleResponse])
def list_user_roles(user_id: int, service: RoleService = Depends(), current_user = Depends(require_permissions("user.manage"))):
    return service.list_user_roles(user_id)

@router.post("/user/{user_id}/roles", response_model=List[RoleResponse])
def assign_user_roles(user_id: int, data: AssignRolesRequest, service: RoleService = Depends(), current_user = Depends(require_permissions("user.manage"))):
    return service.assign_user_roles(user_id, data)

@router.delete("/user/{user_id}/roles/{role_id}", response_model=MessageResponse)
def revoke_user_role(user_id: int, role_id: int, service: RoleService = Depends(), current_user = Depends(require_permissions("user.manage"))):
    return service.revoke_user_role(user_id, role_id, current_user)

@router.get("/user/{user_id}/permissions", response_model=List[PermissionResponse])
def list_user_permissions(user_id: int, service: RoleService = Depends(), current_user = Depends(require_permissions("user.manage"))):
    return service.list_user_permissions(user_id)

@router.post("/user/{user_id}/permissions", response_model=List[PermissionResponse])
def assign_user_permissions(user_id: int, data: AssignPermissionsRequest, service: RoleService = Depends(), current_user = Depends(require_permissions("user.manage"))):
    return service.assign_user_permissions(user_id, data)

@router.delete("/user/{user_id}/permissions/{permission_id}", response_model=MessageResponse)
def revoke_user_permission(user_id: int, permission_id: int, service: RoleService = Depends(), current_user = Depends(require_permissions("user.manage"))):
    return service.revoke_user_permission(user_id, permission_id)
