from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class Provider(str, Enum):
    """Login providers"""

    email = "Email"
    google = "Google"
    github = "GitHub"


class Signin(BaseModel):
    """Request model for Signin"""

    email: EmailStr
    password: str


class Signup(Signin):
    """Request model for Signup"""

    name: Optional[str] = None  # Changed from username to match DB 'name'


class SignupResponse(BaseModel):
    """Response model for successful signup"""

    user_id: UUID
    name: str
    email: EmailStr
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

    class Config:
        from_attributes = True


class SigninResponse(BaseModel):
    """Response model for successful login"""

    user_id: UUID
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    class Config:
        from_attributes = True


class RefreshRequest(BaseModel):
    """Request model for token refresh"""

    refresh_token: str


__all__ = [
    "Provider",
    "Signin",
    "Signup",
    "SignupResponse",
    "SigninResponse",
    "RefreshRequest",
]
