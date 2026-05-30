"""Debug endpoint for SGA / EXA."""
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser
from app.search.exa import ExaQuotaExceeded, get_exa_client

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(
    _user: CurrentUser,
    q: str = Query(min_length=2, max_length=400),
    n: int = Query(default=8, ge=1, le=25),
) -> dict:
    exa = get_exa_client()
    try:
        results = await exa.search(q, num_results=n)
    except ExaQuotaExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)
        ) from exc
    return {
        "query": q,
        "count": len(results),
        "results": [r.__dict__ for r in results],
        "exa_usage": await exa.usage_snapshot(),
    }

