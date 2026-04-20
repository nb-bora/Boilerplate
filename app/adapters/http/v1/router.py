from __future__ import annotations

"""
Router V1 racine (`/api/v1`).

Rôle
----
Assembler les routers métier sous un préfixe versionné.

Objectifs
---------
- Fournir un point d'inclusion unique dans `app/main.py`.
- Permettre de versionner l'API (v1, v2...) sans casser les consumers.

Intervient dans
--------------
- Composition root : `app/main.py` fait `app.include_router(v1_router)`.
"""

from fastapi import APIRouter

from app.adapters.http.v1.auth import router as auth_router
from app.adapters.http.v1.health import router as health_router
from app.adapters.http.v1.users import router as users_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router, tags=["health"])
router.include_router(auth_router, tags=["auth"])
router.include_router(users_router, tags=["users"])
