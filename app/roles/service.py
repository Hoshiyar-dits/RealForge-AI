from typing import List
from fastapi import Depends, HTTPException, status
from app.roles.repository import RoleRepository
from app.users.repository import UserRepository
from app.roles.dto.UserAccessResponse import UserAccessResponse
from app.auth.dto.MessageResponse import MessageResponse
import os

default_role = os.getenv("DEFAULT_ROLE", "user")

class RoleService():
    def __init__(self, repository: RoleRepository = Depends(), user_repository: UserRepository = Depends()):
        self.repository = repository
        self.user_repository = user_repository

    # roles

    def create_role(self, data):
        if self.repository.get_role_by_name(data.name):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role already exists")
        return self.repository.create_role(data)

    def list_roles(self):
        return self.repository.list_roles()

    def get_role(self, role_id: int):
        role = self.repository.get_role_by_id(role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        return role

    def update_role(self, role_id: int, data):
        role = self.get_role(role_id)
        if data.name and data.name != role.name and self.repository.get_role_by_name(data.name):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role already exists")
        return self.repository.update(role, data)

    def delete_role(self, role_id: int) -> MessageResponse:
        role = self.get_role(role_id)
        self.repository.delete_role(role)
        return MessageResponse(message="Role deleted")

    # permissions

    def create_permission(self, data):
        if self.repository.get_permission_by_name(data.name):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Permission already exists")
        return self.repository.create_permission(data)

    def list_permissions(self):
        return self.repository.list_permissions()

    def get_permission(self, permission_id: int):
        permission = self.repository.get_permission_by_id(permission_id)
        if not permission:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
        return permission

    def update_permission(self, permission_id: int, data):
        permission = self.get_permission(permission_id)
        if data.name and data.name != permission.name and self.repository.get_permission_by_name(data.name):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Permission already exists")
        return self.repository.update(permission, data)

    def delete_permission(self, permission_id: int) -> MessageResponse:
        permission = self.get_permission(permission_id)
        self.repository.delete_permission(permission)
        return MessageResponse(message="Permission deleted")

    def check_permission_ids(self, permission_ids: List[int]):
        if len(self.repository.get_permissions_by_ids(permission_ids)) != len(set(permission_ids)):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more permissions not found")

    # role -> permissions

    def list_role_permissions(self, role_id: int):
        self.get_role(role_id)
        return self.repository.list_role_permissions(role_id)

    def assign_role_permissions(self, role_id: int, data):
        self.get_role(role_id)
        self.check_permission_ids(data.permission_ids)
        self.repository.add_role_permissions(role_id, data.permission_ids)
        return self.repository.list_role_permissions(role_id)

    def revoke_role_permission(self, role_id: int, permission_id: int) -> MessageResponse:
        link = self.repository.get_role_permission(role_id, permission_id)
        if not link:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission is not assigned to this role")
        self.repository.delete_link(link)
        return MessageResponse(message="Permission removed from role")

    # user -> roles / permissions

    def get_user(self, user_id: int):
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def list_user_roles(self, user_id: int):
        self.get_user(user_id)
        return self.repository.list_user_roles(user_id)

    def assign_user_roles(self, user_id: int, data):
        self.get_user(user_id)
        if len(self.repository.get_roles_by_ids(data.role_ids)) != len(set(data.role_ids)):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more roles not found")
        self.repository.add_user_roles(user_id, data.role_ids)
        return self.repository.list_user_roles(user_id)

    def revoke_user_role(self, user_id: int, role_id: int, current_user) -> MessageResponse:
        if user_id == current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot remove your own roles")
        link = self.repository.get_user_role(user_id, role_id)
        if not link:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role is not assigned to this user")
        self.repository.delete_link(link)
        return MessageResponse(message="Role removed from user")

    def list_user_permissions(self, user_id: int):
        self.get_user(user_id)
        return self.repository.list_user_permissions(user_id)

    def assign_user_permissions(self, user_id: int, data):
        self.get_user(user_id)
        self.check_permission_ids(data.permission_ids)
        self.repository.add_user_permissions(user_id, data.permission_ids)
        return self.repository.list_user_permissions(user_id)

    def revoke_user_permission(self, user_id: int, permission_id: int) -> MessageResponse:
        link = self.repository.get_user_permission(user_id, permission_id)
        if not link:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission is not assigned to this user")
        self.repository.delete_link(link)
        return MessageResponse(message="Permission removed from user")

    def get_user_access(self, user_id: int) -> UserAccessResponse:
        self.get_user(user_id)
        return UserAccessResponse(
            user_id=user_id,
            roles=[role.name for role in self.repository.list_user_roles(user_id)],
            permissions=sorted(self.repository.get_user_permission_names(user_id)),
        )

    def assign_default_role(self, user):
        role = self.repository.get_role_by_name(default_role)
        if role:
            self.repository.add_user_roles(user.id, [role.id])
