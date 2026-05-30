from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserOut,
)
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    res = await db.execute(select(User).where(User.username == payload.username))
    user = res.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
        )
    profile_res = await db.execute(
        select(UserProfile).where(UserProfile.user_id == str(user.id))
    )
    has_profile = profile_res.scalar_one_or_none() is not None
    token = create_access_token(subject=str(user.id), extra={"role": user.role})
    return TokenResponse(
        access_token=token,
        user=UserOut(
            id=str(user.id),
            username=user.username,
            display_name=user.display_name,
            role=user.role,
            access_code=user.access_code,
            has_profile=has_profile,
        ),
    )


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser, db: DbSession) -> UserOut:
    profile_res = await db.execute(
        select(UserProfile).where(UserProfile.user_id == str(user.id))
    )
    has_profile = profile_res.scalar_one_or_none() is not None
    return UserOut(
        id=str(user.id),
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        access_code=user.access_code,
        has_profile=has_profile,
    )
