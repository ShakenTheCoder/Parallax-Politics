import contextlib
import hashlib

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.config import get_settings
from app.models.user import User
from app.models.user_profile import UserProfile
from app.redis import get_redis
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserOut,
)
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
_DUMMY_PASSWORD_HASH = hash_password("parallax-invalid-credential-sentinel")


async def _enforce_login_limit(request: Request, username: str) -> list[str]:
    client = request.client.host if request.client else "unknown"
    identity = hashlib.sha256(f"{client}:{username}".encode()).hexdigest()
    account = hashlib.sha256(username.encode()).hexdigest()
    limits = {
        f"auth:login:pair:{identity}": settings.login_attempt_limit,
        f"auth:login:account:{account}": settings.login_attempt_limit * 2,
    }
    try:
        redis = get_redis()
        for key, limit in limits.items():
            attempts = await redis.incr(key)
            if attempts == 1:
                await redis.expire(key, settings.login_attempt_window_seconds)
            if attempts > limit:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Authentication temporarily unavailable")
    except HTTPException:
        raise
    except Exception as exc:
        if settings.is_prod:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication temporarily unavailable") from exc
    return list(limits)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, db: DbSession) -> TokenResponse:
    limit_keys = await _enforce_login_limit(request, payload.username)
    res = await db.execute(select(User).where(User.username == payload.username))
    user = res.scalar_one_or_none()
    password_valid = verify_password(
        payload.password,
        user.password_hash if user else _DUMMY_PASSWORD_HASH,
    )
    if not user or not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
        )
    profile_res = await db.execute(
        select(UserProfile).where(UserProfile.user_id == str(user.id))
    )
    has_profile = profile_res.scalar_one_or_none() is not None
    token = create_access_token(subject=str(user.id), extra={"role": user.role})
    with contextlib.suppress(Exception):
        await get_redis().delete(*limit_keys)
    return TokenResponse(
        access_token=token,
        user=UserOut(
            id=str(user.id),
            username=user.username,
            display_name=user.display_name,
            role=user.role,
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
        has_profile=has_profile,
    )
