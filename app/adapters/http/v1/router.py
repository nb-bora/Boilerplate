from __future__ import annotations

from fastapi import APIRouter

from app.adapters.http.v1.auth import router as auth_router
from app.adapters.http.v1.health import router as health_router
from app.adapters.http.v1.users import router as users_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router, tags=["health"])
router.include_router(auth_router, tags=["auth"])
router.include_router(users_router, tags=["users"])
