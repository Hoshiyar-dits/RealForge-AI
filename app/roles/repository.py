from typing import List
from app.database.database import get_db
from app.roles.models.roles import Role
from app.roles.models.permissions import Permission
from app.roles.models.role_permissions import RolePermission
from app.roles.models.user_roles import UserRole
from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
class RoleRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    # roles

    def create_role(self, name: str, description: str):
        try:
            role = Role(name=name, description=description)
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

    # permissions

    def create_permission(self, name: str, description: str):
        try:
            permission = Permission(name=name, description=description)
            self.db.add(permission)
            self.db.commit()
            self.db.refresh(permission)
            return permission
        except Exception:
            self.db.rollback()
            raise

    def get_permission_by_name(self, name: str):
        return self.db.query(Permission).filter(Permission.name == name, Permission.deleted_at.is_(None)).first()

    def get_permissions_by_ids(self, permission_ids: List[int]):
        return self.db.query(Permission).filter(Permission.id.in_(permission_ids), Permission.deleted_at.is_(None)).all()

    # role -> permissions

    def list_role_permissions(self, role_id: int):
        return self.db.query(Permission).join(RolePermission, RolePermission.permission_id == Permission.id).filter(
            RolePermission.role_id == role_id,
            RolePermission.deleted_at.is_(None),
            Permission.deleted_at.is_(None),
        ).order_by(Permission.name).all()

    def add_role_permissions(self, role_id: int, permission_ids: List[int]):
        try:
            existing = {p.id for p in self.list_role_permissions(role_id)}
            for permission_id in set(permission_ids) - existing:
                self.db.add(RolePermission(role_id=role_id, permission_id=permission_id))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def sync_role_permissions(self, role_id: int, permission_ids: List[int]):
        # the role ends up with exactly these permissions
        try:
            self.db.query(RolePermission).filter(
                RolePermission.role_id == role_id,
                RolePermission.permission_id.notin_(permission_ids),
                RolePermission.deleted_at.is_(None),
            ).update({RolePermission.deleted_at: func.now()}, synchronize_session=False)
            self.add_role_permissions(role_id, permission_ids)
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

    def add_user_roles(self, user_id: int, role_ids: List[int]):
        try:
            existing = {r.id for r in self.list_user_roles(user_id)}
            for role_id in set(role_ids) - existing:
                self.db.add(UserRole(user_id=user_id, role_id=role_id))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def sync_user_roles(self, user_id: int, role_ids: List[int]):
        # the user ends up with exactly these roles
        try:
            self.db.query(UserRole).filter(
                UserRole.user_id == user_id,
                UserRole.role_id.notin_(role_ids),
                UserRole.deleted_at.is_(None),
            ).update({UserRole.deleted_at: func.now()}, synchronize_session=False)
            self.add_user_roles(user_id, role_ids)
        except Exception:
            self.db.rollback()
            raise

    def get_user_permission_names(self, user_id: int):
        # effective permissions = permissions of the user's active roles
        rows = self.db.query(Permission.name).join(RolePermission, RolePermission.permission_id == Permission.id).join(
            UserRole, UserRole.role_id == RolePermission.role_id
        ).join(Role, Role.id == UserRole.role_id).filter(
            UserRole.user_id == user_id,
            UserRole.deleted_at.is_(None),
            RolePermission.deleted_at.is_(None),
            Role.deleted_at.is_(None),
            Role.status == "1",
            Permission.deleted_at.is_(None),
        ).all()
        return {name for (name,) in rows}
