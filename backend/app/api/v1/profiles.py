from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.profile import Profile

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/{slug}")
async def get_profile(slug: str, db: DbSession, _user: CurrentUser) -> dict:
    res = await db.execute(select(Profile).where(Profile.slug == slug))
    profile = res.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return {
        "id": str(profile.id),
        "slug": profile.slug,
        "full_name": profile.full_name,
        "role_title": profile.role_title,
        "party": profile.party,
        "pack_id": profile.pack_id,
        "identity": profile.identity,
        "career": profile.career,
        "stances": profile.stances,
        "voice_patterns": profile.voice_patterns,
        "vulnerabilities": profile.vulnerabilities,
        "allies_rivals": profile.allies_rivals,
        "media_footprint": profile.media_footprint,
    }


@router.get("")
async def list_profiles(db: DbSession, _user: CurrentUser) -> list[dict]:
    res = await db.execute(select(Profile).order_by(Profile.created_at.desc()))
    return [
        {
            "id": str(p.id),
            "slug": p.slug,
            "full_name": p.full_name,
            "role_title": p.role_title,
            "party": p.party,
            "pack_id": p.pack_id,
        }
        for p in res.scalars().all()
    ]
