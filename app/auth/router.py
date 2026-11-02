from fastapi import APIRouter, Depends, status
from app.auth.dto.LoginRequest import LoginRequest
from app.auth.dto.LoginResponse import LoginResponse
from app.auth.dto.MessageResponse import MessageResponse
from app.auth.dto.VerifyCodeRequest import VerifyCodeRequest
from app.auth.dto.ResendVerificationRequest import ResendVerificationRequest
from app.users.dto.CreateUser import CreateUser
from app.users.dto.UserResponse import UserResponse
from app.auth.service import AuthService

router = APIRouter(prefix="", tags=['login'])

@router.post("/sign-up", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def sign_up(data: CreateUser, service: AuthService = Depends()):
    return service.sign_up(data)


@router.post("/verify-email", response_model=LoginResponse)
def verify_email(data: VerifyCodeRequest, service: AuthService = Depends()):
    return service.verify_email(data)


@router.post("/verify-email/resend", response_model=MessageResponse)
def resend_verification(data: ResendVerificationRequest, service: AuthService = Depends()):
    return service.resend_verification(data)


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, service: AuthService = Depends()):
    return service.login(data)
