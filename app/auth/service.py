from fastapi import Depends, HTTPException, status
from app.users.repository import UserRepository
from app.users.service import UserService, verify_password, dummy_password_hash
from app.auth.repository import OtpRepository
from app.mail.service import MailService
from app.roles.service import RoleService
from datetime import datetime, timedelta, timezone
from app.auth.dto.LoginResponse import LoginResponse
from app.auth.dto.MessageResponse import MessageResponse
from app.database.config import algorithm, secret, expire_minutes, otp_expire_minutes, otp_max_attempts
import hmac
import hashlib
import secrets
import jwt

if not secret:
    raise RuntimeError("JWT_SECRET_KEY is not set in the environment / .env")

def utc_now() -> datetime:
    # DB TIMESTAMP columns are naive, so compare in naive UTC
    return datetime.now(timezone.utc).replace(tzinfo=None)

def hash_code(code: str) -> str:
    return hmac.new(secret.encode(), code.encode(), hashlib.sha256).hexdigest()

class AuthService():
    def __init__(
        self,
        repository: UserRepository = Depends(),
        otp_repository: OtpRepository = Depends(),
        user_service: UserService = Depends(),
        mail_service: MailService = Depends(),
        role_service: RoleService = Depends(),
    ):
        self.repository = repository
        self.otp_repository = otp_repository
        self.user_service = user_service
        self.mail_service = mail_service
        self.role_service = role_service

    def sign_up(self, data):
        user = self.user_service.create_user(data)
        self.role_service.assign_default_role(user)
        self.send_code(user, "verify_email")
        return user

    def resend_verification(self, data) -> MessageResponse:
        user = self.repository.get_by_email(data.email)
        if user and user.email_verified_at is None:
            self.send_code(user, "verify_email")
        return MessageResponse(message="If the email is registered and not yet verified, a verification code has been sent")

    def verify_email(self, data) -> LoginResponse:
        user = self.repository.get_by_email(data.email)
        self.check_code(user, "verify_email", data.code)
        if user.email_verified_at is None:
            self.repository.mark_email_verified(user)
        return self.create_token(user)

    def login(self, data) -> LoginResponse:
        invalid = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
        user = self.repository.get_by_email(data.email)
        if not user:
            raise invalid
        if not verify_password(data.password, user.password):
            raise invalid
        if user.email_verified_at is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified",
            )
        return self.create_token(user)

    def send_code(self, user, purpose: str):
        code = f"{secrets.randbelow(10**6):06d}"
        expires_at = utc_now() + timedelta(minutes=otp_expire_minutes)
        self.otp_repository.create(user.id, purpose, hash_code(code), expires_at)

        subject = "Verify your email"
        body = f"Your verification code is {code}. It expires in {otp_expire_minutes} minutes."
        self.mail_service.send(user.email, subject, body)

    def check_code(self, user, purpose: str, code: str):
        invalid = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired code",
        )
        if not user:
            raise invalid

        otp = self.otp_repository.get_active(user.id, purpose, utc_now())
        if not otp:
            raise invalid

        if not hmac.compare_digest(otp.code, hash_code(code)):
            self.otp_repository.increment_attempts(otp)
            if otp.attempts >= otp_max_attempts:
                self.otp_repository.delete(otp)
            raise invalid

        self.otp_repository.mark_used(otp)

    def create_token(self, user) -> LoginResponse:
        expiry_time = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
        # PyJWT requires "sub" to be a string
        token = jwt.encode({"sub": str(user.id), "exp": expiry_time}, secret, algorithm)
        return LoginResponse(access_token=token)
