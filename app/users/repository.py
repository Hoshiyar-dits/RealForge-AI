from app.database.database import get_db
from app.users.models.users import User
from app.roles.models.roles import Role
from app.roles.models.user_roles import UserRole
from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
class UserRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create(self, data, password_hash: str):
        try:
            user = User(
                first_name=data.first_name,
                last_name=data.last_name,
                email=data.email,
                password=password_hash,
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception:
            self.db.rollback()
            raise

    def get_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()

    def get_by_id(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()

    def list(self):
        return self.db.query(User).filter(User.deleted_at.is_(None)).order_by(User.id).all()

    def query_by_role(self, role_name: str):
        # users that have the given role
        return self.db.query(User).join(UserRole, UserRole.user_id == User.id).join(Role, Role.id == UserRole.role_id).filter(
            Role.name == role_name,
            User.deleted_at.is_(None),
            UserRole.deleted_at.is_(None),
            Role.deleted_at.is_(None),
        )

    def list_by_role(self, role_name: str):
        return self.query_by_role(role_name).order_by(User.id).all()

    def get_by_id_and_role(self, user_id: int, role_name: str):
        return self.query_by_role(role_name).filter(User.id == user_id).first()

    def update(self, user: User, data, password_hash: str):
        try:
            user.first_name = data.first_name
            user.last_name = data.last_name
            user.email = data.email
            user.password = password_hash
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception:
            self.db.rollback()
            raise

    def delete(self, user: User):
        try:
            user.deleted_at = func.now()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def mark_email_verified(self, user: User):
        try:
            user.email_verified_at = func.now()
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception:
            self.db.rollback()
            raise
