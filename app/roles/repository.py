from typing import List
from app.database.database import get_db
from app.roles.models.roles import Role
from app.roles.models.permissions import Permission
from app.roles.models.role_permissions import RolePermission
from app.roles.models.user_roles import UserRole
from app.roles.models.user_permissions import UserPermission
from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
class RoleRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def update(self, instance, data):
        # shared by roles and permissions
        try:
            for field, value in data.model_dump(exclude_none=True).items():
                setattr(instance, field, value)
            self.db.commit()
            self.db.refresh(instance)
            return instance
        except Exception:
            self.db.rollback()
            raise

    def delete_link(self, link):
        # soft-deletes one row of role_permissions / user_roles / user_permissions
        try:
            link.deleted_at = func.now()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # roles

    def create_role(self, data):
        try:
            role = Role(name=data.name, description=data.description)
            self.db.add(role)
            self.db.commit()
            self.db.refresh(role)
            return role
        except Exception:
            self.db.rollback()
            raise

    def get_role_by_id(self, role_id: int):
        return self.db.query(Role).filter(Role.id == role_id, Role.deleted_at.is_(None)).first()

    def get_role_by_name(self, name: str):
        return self.db.query(Role).filter(Role.name == name, Role.deleted_at.is_(None)).first()

    def get_roles_by_ids(self, role_ids: List[int]):
        return self.db.query(Role).filter(Role.id.in_(role_ids), Role.deleted_at.is_(None)).all()

    def list_roles(self):
        return self.db.query(Role).filter(Role.deleted_at.is_(None)).order_by(Role.id).all()

    def delete_role(self, role: Role):
        try:
            self.db.query(RolePermission).filter(RolePermission.role_id == role.id, RolePermission.deleted_at.is_(None)).update({RolePermission.deleted_at: func.now()})
            self.db.query(UserRole).filter(UserRole.role_id == role.id, UserRole.deleted_at.is_(None)).update({UserRole.deleted_at: func.now()})
            role.deleted_at = func.now()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # permissions

    def create_permission(self, data):
        try:
            permission = Permission(name=data.name, description=data.description)
            self.db.add(permission)
            self.db.commit()
            self.db.refresh(permission)
            return permission
        except Exception:
            self.db.rollback()
            raise

    def get_permission_by_id(self, permission_id: int):
        return self.db.query(Permission).filter(Permission.id == permission_id, Permission.deleted_at.is_(None)).first()

    def get_permission_by_name(self, name: str):
        return self.db.query(Permission).filter(Permission.name == name, Permission.deleted_at.is_(None)).first()

    def get_permissions_by_ids(self, permission_ids: List[int]):
        return self.db.query(Permission).filter(Permission.id.in_(permission_ids), Permission.deleted_at.is_(None)).all()

    def list_permissions(self):
        return self.db.query(Permission).filter(Permission.deleted_at.is_(None)).order_by(Permission.name).all()

    def delete_permission(self, permission: Permission):
        try:
            self.db.query(RolePermission).filter(RolePermission.permission_id == permission.id, RolePermission.deleted_at.is_(None)).update({RolePermission.deleted_at: func.now()})
            self.db.query(UserPermission).filter(UserPermission.permission_id == permission.id, UserPermission.deleted_at.is_(None)).update({UserPermission.deleted_at: func.now()})
            permission.deleted_at = func.now()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # role -> permissions

    def list_role_permissions(self, role_id: int):
        return self.db.query(Permission).join(RolePermission, RolePermission.permission_id == Permission.id).filter(
            RolePermission.role_id == role_id,
            RolePermission.deleted_at.is_(None),
            Permission.deleted_at.is_(None),
        ).order_by(Permission.name).all()

    def get_role_permission(self, role_id: int, permission_id: int):
        return self.db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
            RolePermission.deleted_at.is_(None),
        ).first()

    def add_role_permissions(self, role_id: int, permission_ids: List[int]):
        try:
            existing = {p.id for p in self.list_role_permissions(role_id)}
            for permission_id in set(permission_ids) - existing:
                self.db.add(RolePermission(role_id=role_id, permission_id=permission_id))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # user -> roles

    def list_user_roles(self, user_id: int):
        return self.db.query(Role).join(UserRole, UserRole.role_id == Role.id).filter(
            UserRole.user_id == user_id,
            UserRole.deleted_at.is_(None),
            Role.deleted_at.is_(None),
        ).order_by(Role.id).all()

    def get_user_role(self, user_id: int, role_id: int):
        return self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
            UserRole.deleted_at.is_(None),
        ).first()

    def add_user_roles(self, user_id: int, role_ids: List[int]):
        try:
            existing = {r.id for r in self.list_user_roles(user_id)}
            for role_id in set(role_ids) - existing:
                self.db.add(UserRole(user_id=user_id, role_id=role_id))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # user -> direct permissions

    def list_user_permissions(self, user_id: int):
        return self.db.query(Permission).join(UserPermission, UserPermission.permission_id == Permission.id).filter(
            UserPermission.user_id == user_id,
            UserPermission.deleted_at.is_(None),
            Permission.deleted_at.is_(None),
        ).order_by(Permission.name).all()

    def get_user_permission(self, user_id: int, permission_id: int):
        return self.db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.permission_id == permission_id,
            UserPermission.deleted_at.is_(None),
        ).first()

    def add_user_permissions(self, user_id: int, permission_ids: List[int]):
        try:
            existing = {p.id for p in self.list_user_permissions(user_id)}
            for permission_id in set(permission_ids) - existing:
                self.db.add(UserPermission(user_id=user_id, permission_id=permission_id))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def get_user_permission_names(self, user_id: int):
        # effective permissions = permissions of the user's active roles + direct permissions
        from_roles = self.db.query(Permission.name).join(RolePermission, RolePermission.permission_id == Permission.id).join(
            UserRole, UserRole.role_id == RolePermission.role_id
        ).join(Role, Role.id == UserRole.role_id).filter(
            UserRole.user_id == user_id,
            UserRole.deleted_at.is_(None),
            RolePermission.deleted_at.is_(None),
            Role.deleted_at.is_(None),
            Role.status == "1",
            Permission.deleted_at.is_(None),
        ).all()
        direct = [(p.name,) for p in self.list_user_permissions(user_id)]
        return {name for (name,) in from_roles + direct}
