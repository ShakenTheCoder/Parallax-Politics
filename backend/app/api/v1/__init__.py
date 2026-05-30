from fastapi import APIRouter

from app.api.v1 import admin, auth, briefs, profiles, runs, search, superadmin

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(profiles.router)
api_router.include_router(runs.router)
api_router.include_router(search.router)
api_router.include_router(admin.router)
api_router.include_router(superadmin.router)
api_router.include_router(briefs.router)
