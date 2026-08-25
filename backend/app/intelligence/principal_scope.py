"""Resolve the principal visible to a request at one authorization boundary."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.models.user import User


async def resolve_principal(
    db: AsyncSession, user: User, requested_profile_id: UUID | None = None
) -> Profile:
    """Return the request's principal, enforcing principal isolation.

    Superadmins may select an existing profile explicitly. Principals are always
    bound to the profile on their account and cannot override it via query
    parameters.
    """
    if user.role == "superadmin":
        profile_id = requested_profile_id
        if profile_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="profile_id is required for superadmin intelligence views",
            )
    else:
        if requested_profile_id is not None and requested_profile_id != user.principal_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Principal scope cannot be overridden")
        profile_id = user.principal_id
        if profile_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No principal linked to this account")

    profile = await db.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Principal not found")
    return profile
