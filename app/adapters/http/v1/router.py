from __future__ import annotations

from fastapi import APIRouter

from app.adapters.http.v1.health import router as health_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router, tags=["health"])

