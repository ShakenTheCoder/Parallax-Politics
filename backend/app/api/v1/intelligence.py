"""Authenticated political-intelligence control-plane endpoints."""
from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.intelligence.fleet import AGENT_FLEET
from app.intelligence.service import (
    collect_source,
    create_collection_source,
    create_collection_subscription,
    create_scenario,
    decide_verdict,
    intelligence_overview,
    list_collection_sources,
    list_collection_subscriptions,
    list_scenarios,
    list_verdicts,
)
from app.schemas.intelligence import (
    AgentFleetOut,
    CollectionRequest,
    CollectionResult,
    CollectionSourceCreate,
    CollectionSourceOut,
    CollectionSubscriptionCreate,
    CollectionSubscriptionOut,
    IntelligenceOverview,
    ScenarioCreate,
    ScenarioCreateResult,
    ScenarioOut,
    VerdictDecision,
    VerdictOut,
)

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get("/agents", response_model=AgentFleetOut)
async def get_agent_fleet(_user: CurrentUser) -> AgentFleetOut:
    return AgentFleetOut(
        agents=AGENT_FLEET,
        invariant="Agents may draft estimates and strategies; only an authorized analyst can create a Verdict.",
    )


@router.get("/overview", response_model=IntelligenceOverview)
async def get_overview(db: DbSession, user: CurrentUser) -> IntelligenceOverview:
    return await intelligence_overview(db, user)


@router.get("/sources", response_model=list[CollectionSourceOut])
async def get_sources(db: DbSession, _admin: AdminUser) -> list[CollectionSourceOut]:
    return await list_collection_sources(db)


@router.post("/sources", response_model=CollectionSourceOut, status_code=status.HTTP_201_CREATED)
async def register_source(
    payload: CollectionSourceCreate,
    db: DbSession,
    admin: AdminUser,
) -> CollectionSourceOut:
    return await create_collection_source(db, admin, payload)


@router.post("/sources/{source_id}/collect", response_model=CollectionResult)
async def run_collection(
    source_id: UUID,
    payload: CollectionRequest,
    db: DbSession,
    admin: AdminUser,
) -> CollectionResult:
    return await collect_source(db, admin, source_id, payload)


@router.get("/subscriptions", response_model=list[CollectionSubscriptionOut])
async def get_subscriptions(
    db: DbSession,
    _admin: AdminUser,
) -> list[CollectionSubscriptionOut]:
    return await list_collection_subscriptions(db)


@router.post(
    "/sources/{source_id}/subscriptions",
    response_model=CollectionSubscriptionOut,
    status_code=status.HTTP_201_CREATED,
)
async def schedule_collection(
    source_id: UUID,
    payload: CollectionSubscriptionCreate,
    db: DbSession,
    admin: AdminUser,
) -> CollectionSubscriptionOut:
    return await create_collection_subscription(db, admin, source_id, payload)


@router.get("/scenarios", response_model=list[ScenarioOut])
async def get_scenarios(db: DbSession, user: CurrentUser) -> list[ScenarioOut]:
    return await list_scenarios(db, user)


@router.post("/scenarios", response_model=ScenarioCreateResult, status_code=status.HTTP_201_CREATED)
async def simulate_scenario(
    payload: ScenarioCreate,
    db: DbSession,
    user: CurrentUser,
) -> ScenarioCreateResult:
    scenario, verdict = await create_scenario(db, user, payload)
    return ScenarioCreateResult(scenario=scenario, verdict=verdict)


@router.get("/verdicts", response_model=list[VerdictOut])
async def get_verdicts(db: DbSession, user: CurrentUser) -> list[VerdictOut]:
    return await list_verdicts(db, user)


@router.patch("/verdicts/{verdict_id}", response_model=VerdictOut)
async def review_verdict(
    verdict_id: UUID,
    payload: VerdictDecision,
    db: DbSession,
    admin: AdminUser,
) -> VerdictOut:
    return await decide_verdict(db, admin, verdict_id, payload.decision, payload.review_note)
