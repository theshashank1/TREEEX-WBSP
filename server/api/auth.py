from datetime import datetime
from typing import Annotated

from database import get_db_session
from dependencies import get_supabase_client
from fastapi import APIRouter, Depends, HTTPException
from models import users
from passlib.hash import bcrypt
from schemas.auth import Provider, SigninResponse, Signup, SignupResponse
from sqlmodel import Session
from utils.generator import generate_username
from utils.supabase import Client, get_user

router = APIRouter(tags=["Authentication"])

# Define the dependency type
SessionDep = Annotated[Session, Depends(get_db_session)]
SupabaseDep = Annotated[Client, Depends(get_supabase_client)]


@router.post("/signup", response_model=SignupResponse)
async def signup(
    data: Signup,
    session: SessionDep,
    supabase: SupabaseDep,
    provider: Provider = Provider.email,
):
    if provider == "Email":
        if not data.email or not data.password:
            raise HTTPException(
                status_code=400, detail="Email and password are required"
            )

        try:
            response = supabase.auth.sign_up(
                {"email": data.email, "password": data.password}
            )

            if not response.user:
                raise HTTPException(status_code=400, detail="Sign-up failed")

            hashed_password = bcrypt.hash(data.password)

            user = users.User(
                id=response.user.id,
                email=data.email,
                username=data.username or generate_username(data.email),
                hashed_password=hashed_password,
                is_verified=response.user.email_confirmed_at is not None,
                created_at=response.user.created_at,
            )

            session.add(user)
            session.commit()
            session.refresh(user)

            return SignupResponse(user_id=response.user.id, username=user.username)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail="Unsupported provider")


@router.post("/signin", response_model=SigninResponse)
async def signin(
    data: Signup,
    session: SessionDep,
    supabase: SupabaseDep,
    provider: Provider = Provider.email,
):
    if provider == "Email":
        if not data.email or not data.password:
            raise HTTPException(
                status_code=400, detail="Email and password are required"
            )

        try:
            response = supabase.auth.sign_in_with_password(
                {"email": data.email, "password": data.password}
            )

            if not response.user:
                raise HTTPException(status_code=401, detail="Invalid credentials")

            user = (
                session.query(users.User)
                .filter(users.User.id == response.user.id)
                .first()
            )

            if not user:
                raise HTTPException(
                    status_code=404, detail="User not found in database"
                )

            user.is_verified = response.user.email_confirmed_at is not None
            user.last_login_at = datetime.now()

            session.commit()
            session.refresh(user)

            return SigninResponse(
                user_id=response.user.id, access_token=response.session.access_token
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail="Unsupported provider")


@router.get("/me")
async def me(supabase: SupabaseDep):
    return get_user(supabase)
