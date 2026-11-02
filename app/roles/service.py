from fastapi import Depends, HTTPException, status
from app.roles.repository import RoleRepository
from app.users.repository import UserRepository
from app.roles.dto.UserAccessResponse import UserAccessResponse
import os

default_role = os.getenv("DEFAULT_ROLE", "user")

class RoleService():
    def __init__(self, repository: RoleRepository = Depends(), user_repository: UserRepository = Depends()):
        self.repository = repository
        self.user_repository = user_repository

    def sync_role_permissions(self, role_id: int, data):
        if not self.repository.get_role_by_id(role_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        if len(self.repository.get_permissions_by_ids(data.permission_ids)) != len(set(data.permission_ids)):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more permissions not found")
        self.repository.sync_role_permissions(role_id, data.permission_ids)
        return self.repository.list_role_permissions(role_id)

    def sync_user_roles(self, user_id: int, data, current_user):
        if user_id == current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot change your own roles")
        if not self.user_repository.get_by_id(user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if len(self.repository.get_roles_by_ids(data.role_ids)) != len(set(data.role_ids)):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more roles not found")
        self.repository.sync_user_roles(user_id, data.role_ids)
        return self.repository.list_user_roles(user_id)

    def get_user_access(self, user_id: int) -> UserAccessResponse:
        return UserAccessResponse(
            user_id=user_id,
            roles=[role.name for role in self.repository.list_user_roles(user_id)],
            permissions=sorted(self.repository.get_user_permission_names(user_id)),
        )

    def assign_default_role(self, user):
        role = self.repository.get_role_by_name(default_role)
        if role:
            self.repository.add_user_roles(user.id, [role.id])
