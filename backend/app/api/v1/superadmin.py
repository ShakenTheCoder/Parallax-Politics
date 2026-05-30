"""Superadmin console endpoints.

Authentication: PSP26 code → superadmin JWT (role=superadmin).
All other routes in this file require that JWT via SuperadminToken dep.
"""
from __future__ import annotations

import secrets
import string
import uuid
from datetime import UTC, timedelta, datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, SuperadminToken
from app.agents.disambiguation import run_disambiguation
from app.contexts import default_pack_id
from app.models.principal_identity import PrincipalIdentity
from app.models.profile import Profile
from app.models.run import Run, RunStatus
from app.models.user import User
from app.schemas.superadmin import (
    CreatePrincipalIn,
    CreatePrincipalOut,
    DisambiguateIn,
    GeneratedCredentials,
    IdentityCandidate,
    PrincipalDetail,
    PrincipalIdentitySection,
    PrincipalSummary,
    SuperadminVerifyIn,
    SuperadminVerifyOut,
)
from app.security import create_access_token, hash_password
from app.services.orchestrator import execute_run

import re

router = APIRouter(prefix="/superadmin", tags=["superadmin"])

_SUPERADMIN_CODE = "PSP26"
_SUPERADMIN_JWT_HOURS = 4
_SLUG_STRIP = re.compile(r"[^a-z0-9]+")
_PWD_CHARS = string.ascii_letters + string.digits


def _make_slug(full_name: str) -> str:
    base = _SLUG_STRIP.sub("-", full_name.lower().strip()).strip("-")
    suffix = secrets.token_hex(4)
    return f"{base}-{suffix}"


def _generate_password(length: int = 16) -> str:
    return "".join(secrets.choice(_PWD_CHARS) for _ in range(length))


def _make_username(full_name: str) -> str:
    parts = full_name.lower().split()
    if len(parts) >= 2:
        base = f"{parts[0][0]}{parts[-1]}"
    else:
        base = parts[0] if parts else "user"
    base = _SLUG_STRIP.sub("", base)
    return f"{base}{secrets.token_hex(3)}"


# --- Auth --------------------------------------------------------------------

@router.post("/verify", response_model=SuperadminVerifyOut)
async def verify_superadmin(payload: SuperadminVerifyIn) -> SuperadminVerifyOut:
    """Exchange the superadmin code for a short-lived JWT."""
    if payload.code != _SUPERADMIN_CODE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid superadmin code")
    token = create_access_token(
        subject="superadmin",
        extra={
            "role": "superadmin",
            "exp": int((datetime.now(UTC) + timedelta(hours=_SUPERADMIN_JWT_HOURS)).timestamp()),
        },
    )
    return SuperadminVerifyOut(token=token)


# --- Disambiguation ----------------------------------------------------------

@router.post("/disambiguate", response_model=IdentityCandidate)
async def disambiguate(
    payload: DisambiguateIn,
    _sa: SuperadminToken,
) -> IdentityCandidate:
    """Run a quick identity-disambiguation lookup. Stateless — does not create any DB rows."""
    return await run_disambiguation(payload.name_query, payload.hint)


# --- Principal creation ------------------------------------------------------

@router.post("/principals", response_model=CreatePrincipalOut, status_code=status.HTTP_201_CREATED)
async def create_principal(
    payload: CreatePrincipalIn,
    db: DbSession,
    _sa: SuperadminToken,
    background: BackgroundTasks,
) -> CreatePrincipalOut:
    """Confirm a candidate and kick off the full PIDAA build.

    1. Create Profile.
    2. Create User (auto credentials).
    3. Create PrincipalIdentity skeleton (status=pending).
    4. Create Run (kind=pidaa_build).
    5. Fire orchestrator in background.

    Returns credentials — shown ONCE. Never stored in plaintext after this response.
    """
    pack_id = default_pack_id()
    c = payload.candidate

    # 1. Profile
    slug = _make_slug(c.full_name)
    profile = Profile(
        slug=slug,
        full_name=c.full_name,
        role_title=c.current_role,
        party=c.party,
        pack_id=pack_id,
        identity={},
        career={},
        stances={},
        voice_patterns={},
        vulnerabilities={},
        allies_rivals={},
        media_footprint={},
    )
    db.add(profile)
    await db.flush()

    # 2. User (auto credentials)
    username = _make_username(c.full_name)
    # Ensure uniqueness
    existing = await db.execute(select(User).where(User.username == username))
    if existing.scalar_one_or_none():
        username = f"{username}{secrets.token_hex(2)}"
    raw_password = _generate_password()

    user = User(
        username=username,
        password_hash=hash_password(raw_password),
        display_name=c.full_name,
        role="principal",
        principal_id=profile.id,
    )
    db.add(user)
    await db.flush()

    # Link profile → user
    profile.identity = {}  # will be filled by PIDAA

    # 3. PrincipalIdentity skeleton
    pi = PrincipalIdentity(
        profile_id=profile.id,
        status="pending",
    )
    db.add(pi)
    await db.flush()

    # 4. Run
    situation = (
        f"Build complete identity dossier for confirmed Philippine principal: {c.full_name}. "
        f"Role: {c.current_role or 'unknown'}. Party: {c.party or 'unknown'}. "
        f"Birthplace: {c.birthplace or 'unknown'}. Bio: {c.one_line_bio or ''}"
    )
    run = Run(
        subject_id=profile.id,
        requested_by=user.id,
        situation_prompt=situation,
        status=RunStatus.queued,
        meta={
            "kind": "pidaa_build",
            "pack_id": pack_id,
            "confirmed_candidate": c.model_dump(),
            "profile_id": str(profile.id),
            "identity_id": str(pi.id),
        },
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    await db.refresh(pi)
    await db.refresh(profile)

    # 5. Update identity status to building
    pi.status = "building"
    await db.commit()

    background.add_task(execute_run, run.id)

    return CreatePrincipalOut(
        profile_id=profile.id,
        identity_id=pi.id,
        run_id=run.id,
        credentials=GeneratedCredentials(username=username, password=raw_password),
    )


# --- Principal management ----------------------------------------------------

@router.get("/principals", response_model=list[PrincipalSummary])
async def list_principals(db: DbSession, _sa: SuperadminToken) -> list[PrincipalSummary]:
    profiles_res = await db.execute(
        select(Profile).order_by(Profile.created_at.desc())
    )
    profiles = profiles_res.scalars().all()

    result: list[PrincipalSummary] = []
    for p in profiles:
        pi_res = await db.execute(
            select(PrincipalIdentity).where(PrincipalIdentity.profile_id == p.id)
        )
        pi = pi_res.scalar_one_or_none()

        user_res = await db.execute(select(User).where(User.principal_id == p.id))
        u = user_res.scalar_one_or_none()

        result.append(PrincipalSummary(
            profile_id=p.id,
            identity_id=pi.id if pi else uuid.UUID(int=0),
            full_name=p.full_name,
            role_title=p.role_title,
            party=p.party,
            pack_id=p.pack_id,
            pidaa_status=pi.status if pi else "no_identity",
            built_at=pi.built_at.isoformat() if (pi and pi.built_at) else None,
            username=u.username if u else "—",
        ))
    return result


@router.get("/principals/{profile_id}", response_model=PrincipalDetail)
async def get_principal(
    profile_id: uuid.UUID,
    db: DbSession,
    _sa: SuperadminToken,
) -> PrincipalDetail:
    prof_res = await db.execute(select(Profile).where(Profile.id == profile_id))
    p = prof_res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Principal not found")

    pi_res = await db.execute(
        select(PrincipalIdentity).where(PrincipalIdentity.profile_id == profile_id)
    )
    pi = pi_res.scalar_one_or_none()

    user_res = await db.execute(select(User).where(User.principal_id == profile_id))
    u = user_res.scalar_one_or_none()

    identity = PrincipalIdentitySection(
        basics=pi.basics if pi else {},
        family=pi.family if pi else {},
        education=pi.education if pi else {},
        career_timeline=pi.career_timeline if pi else {},
        current_position=pi.current_position if pi else {},
        party_history=pi.party_history if pi else {},
        electoral_record=pi.electoral_record if pi else {},
        policy_stances=pi.policy_stances if pi else {},
        voice_signature=pi.voice_signature if pi else {},
        controversies=pi.controversies if pi else {},
        network=pi.network if pi else {},
        source_index=pi.source_index if pi else {},
        coverage_gaps=list(pi.coverage_gaps or []) if pi else [],
    )

    return PrincipalDetail(
        profile_id=p.id,
        identity_id=pi.id if pi else uuid.UUID(int=0),
        full_name=p.full_name,
        role_title=p.role_title,
        party=p.party,
        pack_id=p.pack_id,
        username=u.username if u else "—",
        pidaa_status=pi.status if pi else "no_identity",
        built_at=pi.built_at.isoformat() if (pi and pi.built_at) else None,
        identity=identity,
    )


@router.post("/principals/{profile_id}/rerun", status_code=status.HTTP_202_ACCEPTED)
async def rerun_pidaa(
    profile_id: uuid.UUID,
    db: DbSession,
    _sa: SuperadminToken,
    background: BackgroundTasks,
) -> dict:
    """Re-queue a PIDAA build for an existing principal."""
    prof_res = await db.execute(select(Profile).where(Profile.id == profile_id))
    p = prof_res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Principal not found")

    pi_res = await db.execute(
        select(PrincipalIdentity).where(PrincipalIdentity.profile_id == profile_id)
    )
    pi = pi_res.scalar_one_or_none()
    if pi:
        pi.status = "building"

    user_res = await db.execute(select(User).where(User.principal_id == profile_id))
    u = user_res.scalar_one_or_none()

    situation = f"Rebuild complete identity dossier for: {p.full_name}."
    run = Run(
        subject_id=profile_id,
        requested_by=u.id if u else None,
        situation_prompt=situation,
        status=RunStatus.queued,
        meta={
            "kind": "pidaa_build",
            "pack_id": p.pack_id,
            "profile_id": str(profile_id),
            "identity_id": str(pi.id) if pi else None,
            "confirmed_candidate": {"full_name": p.full_name, "current_role": p.role_title, "party": p.party},
        },
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    background.add_task(execute_run, run.id)
    return {"run_id": str(run.id), "status": "queued"}


@router.delete("/principals/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_principal(
    profile_id: uuid.UUID,
    db: DbSession,
    _sa: SuperadminToken,
) -> None:
    """Hard-delete a principal and all related data."""
    prof_res = await db.execute(select(Profile).where(Profile.id == profile_id))
    p = prof_res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Principal not found")

    user_res = await db.execute(select(User).where(User.principal_id == profile_id))
    u = user_res.scalar_one_or_none()
    if u:
        # Delete UserProfile first so the ORM doesn't try to NULL the FK before the User delete
        from app.models.user_profile import UserProfile
        up_res = await db.execute(
            select(UserProfile).where(UserProfile.user_id == str(u.id))
        )
        up = up_res.scalar_one_or_none()
        if up:
            await db.delete(up)
        await db.flush()
        await db.delete(u)
        await db.flush()

    await db.delete(p)
    await db.commit()
