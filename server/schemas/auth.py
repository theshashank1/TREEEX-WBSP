from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class Provider(str, Enum):
    """Login providers"""

    email = "Email"
    google = "Google"
    github = "GitHub"


class Signup(BaseModel):
    """Request model for Signup"""

    email: EmailStr
    password: str
    name: Optional[str] = None  # Changed from username to match DB 'name'


class SignupResponse(BaseModel):
    """Response model for successful signup"""

    user_id: UUID
    name: str
    email: EmailStr

    class Config:
        from_attributes = True


class SigninResponse(BaseModel):
    """Response model for successful login"""

    user_id: UUID
    access_token: str
    token_type: str = "bearer"

    class Config:
        from_attributes = True


__all__ = ["Provider", "Signup", "SignupResponse", "SigninResponse"]
