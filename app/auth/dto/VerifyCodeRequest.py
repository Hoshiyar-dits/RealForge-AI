from pydantic import BaseModel, EmailStr, Field

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(pattern=r"^\d{6}$")
