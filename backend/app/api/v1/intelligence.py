"""Authenticated political-intelligence control-plane endpoints."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.intelligence.activity_monitor import (
    activity_monitor,
    collect_political_activity,
    list_activity_sources,
)
from app.intelligence.activity_sources import bootstrap_activity_sources
from app.intelligence.brief_view import build_brief_view
from app.intelligence.fleet import AGENT_FLEET
from app.intelligence.free_feeds import bootstrap_free_feeds, collect_free_feeds
from app.intelligence.live_analysis import build_analysis_center, build_command_view
from app.intelligence.momentum import (
    COMPONENT_WEIGHTS,
    MOMENTUM_VERSION,
    RANK_COVERAGE_THRESHOLD,
)
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
    ActivityWindow,
    AgentFleetOut,
    AnalysisCenterOut,
    AppearanceListOut,
    BriefViewOut,
    CollectionRequest,
    CollectionResult,
    CollectionSourceCreate,
    CollectionSourceOut,
    CollectionSubscriptionCreate,
    CollectionSubscriptionOut,
    CommandViewOut,
    EvidenceExplorerOut,
    FreeFeedCollectionOut,
    IntelligenceOverview,
    MethodologyOut,
    PoliticalActivityCollectionOut,
    PoliticalActivityMonitorOut,
    PoliticalActivitySourceOut,
    ScenarioComparisonCreate,
    ScenarioComparisonOut,
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


@router.get("/command", response_model=CommandViewOut, deprecated=True)
async def get_command_view(db: DbSession, user: CurrentUser, profile_id: UUID | None = None) -> CommandViewOut:
    return await build_command_view(db, user, profile_id)


@router.get("/brief", response_model=BriefViewOut)
async def get_brief_view(
    db: DbSession,
    user: CurrentUser,
    window: ActivityWindow = "24h",
    profile_id: UUID | None = None,
) -> BriefViewOut:
    """Return the mobile 30-second Brief without fixture substitution."""
    return await build_brief_view(db, user, activity_window=window, profile_id=profile_id)


@router.get("/analysis", response_model=AnalysisCenterOut)
async def get_analysis_center(
    db: DbSession, user: CurrentUser, window: ActivityWindow = "7d", profile_id: UUID | None = None
) -> AnalysisCenterOut:
    return await build_analysis_center(db, user, window=window, profile_id=profile_id)


@router.get("/activity-monitor", response_model=PoliticalActivityMonitorOut)
async def get_activity_monitor(
    db: DbSession,
    _admin: AdminUser,
    window: ActivityWindow = "24h",
) -> PoliticalActivityMonitorOut:
    """Return the superadmin's glossary-wide structured activity picture."""
    return await activity_monitor(db, window=window)


@router.get("/activity-monitor/sources", response_model=list[PoliticalActivitySourceOut])
async def get_activity_sources(
    db: DbSession, _admin: AdminUser
) -> list[PoliticalActivitySourceOut]:
    return await list_activity_sources(db)


@router.post("/activity-monitor/sources/bootstrap", response_model=list[PoliticalActivitySourceOut])
async def bootstrap_activity_source_registry(
    db: DbSession, _admin: AdminUser
) -> list[PoliticalActivitySourceOut]:
    """Idempotently synchronize the reviewed glossary and publication source catalog."""
    await bootstrap_activity_sources(db)
    await db.commit()
    return await list_activity_sources(db)


@router.post("/activity-monitor/collect", response_model=PoliticalActivityCollectionOut)
async def run_activity_monitor(db: DbSession, _admin: AdminUser) -> PoliticalActivityCollectionOut:
    """Run one bounded allowlisted Scrapling/feed acquisition and Ollama analysis batch."""
    return await collect_political_activity(db, max_analyses=2)


@router.get("/appearances", response_model=AppearanceListOut)
async def get_appearances(db: DbSession, user: CurrentUser, window: ActivityWindow = "24h", profile_id: UUID | None = None) -> AppearanceListOut:
    payload = (await build_analysis_center(db, user, window=window, profile_id=profile_id)).model_dump()
    return AppearanceListOut(
        snapshot_effective_at=datetime.now(UTC),
        appearances=payload["appearances"],
    )


@router.get("/evidence", response_model=EvidenceExplorerOut)
async def get_evidence(db: DbSession, user: CurrentUser, window: ActivityWindow = "7d", profile_id: UUID | None = None) -> EvidenceExplorerOut:
    payload = (await build_analysis_center(db, user, window=window, profile_id=profile_id)).model_dump()
    signals = payload["evidence"]
    return EvidenceExplorerOut(
        snapshot_effective_at=datetime.now(UTC),
        signals=signals,
        count=len(signals),
    )


@router.get("/methodology", response_model=MethodologyOut)
async def get_methodology(_user: CurrentUser) -> MethodologyOut:
    return MethodologyOut(
        model_version=MOMENTUM_VERSION,
        window="seven complete days",
        comparison_window="immediately preceding seven complete days",
        component_weights=COMPONENT_WEIGHTS,
        eligible_layers=["observed", "owned"],
        excluded_layers=["polling", "synthetic"],
        rank_coverage_threshold=RANK_COVERAGE_THRESHOLD,
        missing_data_policy="Missing is null, never zero; rank is withheld below threshold.",
        documentation_path="docs/knowledge/philippines/metrics-and-ranking-methodology.md",
    )


@router.post("/scenario-comparison", response_model=ScenarioComparisonOut)
async def compare_scenario_variants(
    payload: ScenarioComparisonCreate,
    _user: CurrentUser,
) -> ScenarioComparisonOut:
    raise HTTPException(status_code=status.HTTP_410_GONE, detail="Deterministic scenario comparison has been retired; use audience experiments")


@router.get("/sources", response_model=list[CollectionSourceOut])
async def get_sources(db: DbSession, _admin: AdminUser) -> list[CollectionSourceOut]:
    return await list_collection_sources(db)


@router.post("/sources/free/bootstrap", response_model=list[CollectionSourceOut])
async def bootstrap_free_sources(db: DbSession, admin: AdminUser) -> list[CollectionSourceOut]:
    """Register the curated zero-credential Philippine publisher feeds."""
    return await bootstrap_free_feeds(db, admin)


@router.post("/sources/free/collect", response_model=FreeFeedCollectionOut)
async def collect_free_sources(db: DbSession, admin: AdminUser) -> FreeFeedCollectionOut:
    """Collect publisher-feed mentions and refresh 36-hour media assessments."""
    return await collect_free_feeds(db, admin)


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
