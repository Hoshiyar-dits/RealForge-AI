from fastapi import Depends, HTTPException, status
from pwdlib import PasswordHash
from app.users.repository import UserRepository
from app.roles.repository import RoleRepository
from app.auth.dto.MessageResponse import MessageResponse

password_hasher = PasswordHash.recommended()
# verified against when the user doesn't exist, so failed logins take the same time
dummy_password_hash = password_hasher.hash("dummy-password")

technician_role = "technician"

def hash_password(password: str) -> str:
    return password_hasher.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)

class UserService():
    def __init__(self, repository: UserRepository = Depends(), role_repository: RoleRepository = Depends()):
        self.repository = repository
        self.role_repository = role_repository

    def create_user(self, data):
        if self.repository.get_by_email(data.email):
            raise HTTPException(status_code=409, detail="Email already registered")
        return self.repository.create(data, hash_password(data.password))

    def list_users(self):
        return self.repository.list()

    # technicians (added by admin)

    def create_technician(self, data):
        role = self.role_repository.get_role_by_name(technician_role)
        if not role:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Technician role not found; run the roles seeder")
        user = self.create_user(data)
        # the admin adds them, so no email verification code is needed
        self.repository.mark_email_verified(user)
        self.role_repository.add_user_roles(user.id, [role.id])
        return user

    def list_technicians(self):
        return self.repository.list_by_role(technician_role)

    def get_technician(self, user_id: int):
        user = self.repository.get_by_id_and_role(user_id, technician_role)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technician not found")
        return user

    def update_technician(self, user_id: int, data):
        user = self.get_technician(user_id)
        if data.email != user.email and self.repository.get_by_email(data.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        return self.repository.update(user, data, hash_password(data.password))

    def delete_technician(self, user_id: int) -> MessageResponse:
        user = self.get_technician(user_id)
        self.repository.delete(user)
        return MessageResponse(message="Technician deleted")
