"""Admin / observability endpoints."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import AdminUser, DbSession
from app.llm.budget import TokenBudgetManager
from app.models.llm_call import LLMCall
from app.models.user import User
from app.models.user_profile import UserProfile
from app.redis import get_redis
from app.schemas.auth import AdminUserCreate, AdminUserOut
from app.security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])


def _user_out(user: User, has_profile: bool = False) -> AdminUserOut:
    return AdminUserOut(
        id=str(user.id),
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        created_at=user.created_at,
        has_profile=has_profile,
    )


@router.get("/users", response_model=list[AdminUserOut])
async def list_users(db: DbSession, _user: AdminUser) -> list[AdminUserOut]:
    users = (await db.execute(select(User).order_by(User.created_at.desc()))).scalars().all()
    return [_user_out(user, user.principal_id is not None) for user in users]


@router.post("/users", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: AdminUserCreate,
    db: DbSession,
    actor: AdminUser,
) -> AdminUserOut:
    existing = await db.execute(select(User).where(User.username == payload.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        role=payload.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _user_out(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: UUID, db: DbSession, actor: AdminUser) -> None:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == actor.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete yourself"
        )
    if user.role == "superadmin":
        privileged_count = await db.scalar(
            select(func.count(User.id)).where(User.role == "superadmin")
        )
        if (privileged_count or 0) <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete the last superadmin",
            )

    profile = None
    if user.principal_id:
        from app.models.profile import Profile

        profile = await db.get(Profile, user.principal_id)

    user_profile = (
        await db.execute(select(UserProfile).where(UserProfile.user_id == str(user.id)))
    ).scalar_one_or_none()
    if user_profile:
        await db.delete(user_profile)
    await db.delete(user)
    if profile:
        await db.delete(profile)
    await db.commit()


@router.get("/usage")
async def usage(db: DbSession, _user: AdminUser) -> dict:
    """Token & cost rollups — last 24h, last 7d, plus live Redis budget snapshot."""
    budget = TokenBudgetManager(get_redis())
    snapshot = await budget.usage_snapshot()

    now = datetime.now(UTC)
    since_24h = now - timedelta(hours=24)
    since_7d = now - timedelta(days=7)

    async def _rollup(since: datetime) -> dict:
        stmt = (
            select(
                LLMCall.model,
                LLMCall.agent,
                func.count(LLMCall.id),
                func.sum(LLMCall.input_tokens),
                func.sum(LLMCall.output_tokens),
                func.sum(LLMCall.cache_read_tokens),
                func.sum(LLMCall.cache_write_tokens),
                func.sum(LLMCall.cost_usd),
            )
            .where(LLMCall.created_at >= since)
            .group_by(LLMCall.model, LLMCall.agent)
        )
        rows = (await db.execute(stmt)).all()
        return {
            "by_model_agent": [
                {
                    "model": r[0],
                    "agent": r[1],
                    "calls": r[2],
                    "input_tokens": int(r[3] or 0),
                    "output_tokens": int(r[4] or 0),
                    "cache_read_tokens": int(r[5] or 0),
                    "cache_write_tokens": int(r[6] or 0),
                    "cost_usd": round(float(r[7] or 0.0), 6),
                }
                for r in rows
            ],
            "total_cost_usd": round(sum(float(r[7] or 0.0) for r in rows), 6),
        }

    return {
        "now": now.isoformat(),
        "budget": snapshot,
        "last_24h": await _rollup(since_24h),
        "last_7d": await _rollup(since_7d),
    }
