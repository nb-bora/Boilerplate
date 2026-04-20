from __future__ import annotations

"""
Routes HTTP V1 : Auth.

Rôle
----
Expose les endpoints d'authentification au format REST sous `/api/v1/auth/*`.
Cette couche :
- valide l'entrée (Pydantic schemas),
- applique les règles transverses HTTP (rate limit, idempotency),
- appelle les use-cases applicatifs (couche `app/application/*`),
- sérialise les réponses via l'enveloppe uniforme (`app/adapters/http/response.py`).

Endpoints
---------
- `POST /api/v1/auth/register` :
  - Idempotency (header `Idempotency-Key`) : rejoue la même réponse si payload identique, sinon 409.
  - Rate limiting : `RATE_LIMIT_REGISTER_PER_HOUR`.
- `POST /api/v1/auth/login` :
  - Rate limiting : `RATE_LIMIT_LOGIN_PER_MINUTE`.
  - Anti-énumération : assurée au niveau use-case (même exception pour email inconnu / mauvais mdp).
- `POST /api/v1/auth/refresh` :
  - Attend un refresh token (Bearer) avec claim `typ=refresh`.
  - Rotation : révoque l'ancien `jti`, crée un nouveau refresh + access.
- `POST /api/v1/auth/logout` :
  - Blacklist du `jti` access token (si Redis activé), TTL basé sur l'exp.

Intervient dans
--------------
- Dépendances : `app/adapters/http/dependencies.py` (`get_uow`, `get_cache_store`, `get_current_user_id`)
- Idempotency : `app/adapters/cache/idempotency.py`
- Rate limiting : `app/adapters/cache/rate_limiter.py`
- Use-cases : `app/application/auth/register.py`, `app/application/auth/login.py`
- Sécurité JWT : `app/core/security.py`
- Contrat enveloppe : `app/adapters/http/response.py` + `app/common/response_envelope.py`

Scénarios nominaux / alternatifs / exceptions
--------------------------------------------
Chaque fonction ci-dessous détaille son propre workflow. En synthèse :
- Si la DB est down, les use-cases peuvent lever (500) sauf si les dépendances sont overridées en tests.
- Les erreurs de validation request (422) sont enveloppées par `validation_exception_handler`.
- Les erreurs d'idempotency conflit renvoient 409 `TECH.CONFLICT` (enveloppe d'erreur).
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from ulid import ULID

from app.adapters.cache.idempotency import (
    StoredResponse,
    idempotency_lookup,
    idempotency_payload_hash,
    idempotency_store,
)
from app.adapters.cache.rate_limiter import enforce_rate_limit
from app.adapters.http.dependencies import get_cache_store, get_current_user_id, get_uow
from app.adapters.http.response import error, success
from app.adapters.http.schemas.auth import LoginRequest, RegisterRequest
from app.application.auth.dto import LoginInput, RegisterInput
from app.application.auth.login import LoginUser
from app.application.auth.register import RegisterUser
from app.common.response_envelope import ErrorDetail
from app.core.security import create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/auth")


@router.post("/register")
async def register(
    request: Request,
    payload: RegisterRequest,
    uow=Depends(get_uow),  # noqa: ANN001
    store=Depends(get_cache_store),  # noqa: ANN001
):
    """
    Inscription utilisateur.

    Objectifs
    - Créer un user (via use-case) et retourner access+refresh tokens (enveloppe succès).
    - Supporter l'idempotency : mêmes key + payload → même réponse, key + payload différent → 409.
    - Appliquer un rate limit par IP.

    Interactions
    - Use-case : `app/application/auth/register.py::RegisterUser`
    - Cache store : `app/adapters/cache/store.py` (Redis ou in-memory)

    Scénario nominal
    1) Rate limit `auth.register` (TTL 1h).
    2) Si `Idempotency-Key` :
       - calcule un hash du payload (body + content-type + auth),
       - si une réponse existe et hash identique → rejoue la réponse,
       - si hash différent → renvoie 409 enveloppé.
    3) Exécute le use-case (transaction via UoW).
    4) Si idempotency active → stocke la réponse enveloppée avec TTL.

    Exceptions / cas alternatifs
    - 422 : validation payload (Pydantic) → handler global.
    - 409 : `DOMAIN.USER.ALREADY_EXISTS` (via handler d'exceptions) ou conflit idempotency.
    - 429 : rate limit.
    """
    settings = request.app.state.settings if hasattr(request.app.state, "settings") else None
    # Rate limit (par IP)
    from app.core.config import get_settings

    settings = settings or get_settings()
    await enforce_rate_limit(
        request=request,
        store=store,
        key="auth.register",
        limit=settings.RATE_LIMIT_REGISTER_PER_HOUR,
        window_seconds=3600,
    )

    idem_key = request.headers.get("Idempotency-Key")
    if idem_key:
        payload_hash = await idempotency_payload_hash(request)
        existing = await idempotency_lookup(store=store, key=idem_key)
        if existing is not None:
            if existing.payload_hash != payload_hash:
                body, status_code = error(
                    request,
                    message="Conflict",
                    errors=[ErrorDetail(code="TECH.CONFLICT", message="Idempotency key conflict")],
                    status_code=409,
                )
                return JSONResponse(content=body, status_code=status_code)
            return JSONResponse(
                content=existing.body, status_code=existing.status_code, headers=existing.headers
            )

    usecase = RegisterUser(uow=uow)
    out = await usecase.execute(RegisterInput(email=payload.email, password=payload.password))
    body = success(request, data=out.model_dump())
    if idem_key:
        headers = {
            "X-Request-Id": request.state.request_id,
            "X-Correlation-Id": request.state.correlation_id,
        }
        await idempotency_store(
            store=store,
            key=idem_key,
            ttl_seconds=settings.IDEMPOTENCY_TTL_SECONDS,
            payload_hash=payload_hash,
            response=StoredResponse(
                payload_hash=payload_hash, status_code=200, headers=headers, body=body
            ),
        )
    return body


@router.post("/login")
async def login(
    request: Request,
    payload: LoginRequest,
    uow=Depends(get_uow),  # noqa: ANN001
    store=Depends(get_cache_store),  # noqa: ANN001
):
    """
    Connexion utilisateur.

    Objectifs
    - Retourner access+refresh tokens si credentials OK.
    - Anti-énumération : mêmes signaux d'erreur côté client pour email inconnu / mauvais mdp.
    - Appliquer un rate limit par IP.

    Interactions
    - Use-case : `app/application/auth/login.py::LoginUser`

    Exceptions
    - 422 : validation payload.
    - 401 : `TECH.AUTH.INVALID_CREDENTIALS` via handler DomainError.
    - 429 : rate limit.
    """
    from app.core.config import get_settings

    settings = get_settings()
    await enforce_rate_limit(
        request=request,
        store=store,
        key="auth.login",
        limit=settings.RATE_LIMIT_LOGIN_PER_MINUTE,
        window_seconds=60,
    )
    usecase = LoginUser(uow=uow)
    out = await usecase.execute(LoginInput(email=payload.email, password=payload.password))
    return success(request, data=out.model_dump())


@router.post("/logout")
async def logout(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    store=Depends(get_cache_store),  # noqa: ANN001
):
    """
    Déconnexion (révocation best-effort).

    Objectifs
    - Si Redis activé : blacklister le `jti` de l'access token, TTL = durée restante.
    - Retourner un succès enveloppé (même si Redis désactivé).

    Interactions
    - `get_current_user_id` a déjà validé le bearer token et, si Redis activé, la blacklist.
    - `app/core/security.py::decode_token` relit le token pour récupérer `jti`/`exp`.

    Cas alternatifs
    - Redis désactivé : aucune blacklist (logout devient "stateless").

    Exceptions
    - 401 si token manquant/invalide (dépendance).
    """
    # Blacklist du jti access token si Redis activé.
    if getattr(request.app.state, "redis_enabled", False):
        auth = request.headers.get("Authorization") or ""
        token = auth.removeprefix("Bearer ").strip()
        payload = decode_token(token)
        jti = payload.get("jti")
        exp = payload.get("exp")
        if isinstance(jti, str) and isinstance(exp, int):
            ttl = max(0, exp - int(datetime.now(timezone.utc).timestamp()))
            await store.set(f"blacklist:jti:{jti}", "1", ttl=ttl)
    return success(request, data={"status": "ok", "user_id": user_id})


@router.post("/refresh")
async def refresh(
    request: Request,
    uow=Depends(get_uow),  # noqa: ANN001
):
    """
    Rotation refresh token → (nouvel access token + nouveau refresh token).

    Objectifs
    - Vérifier que le token Bearer est un refresh (`typ=refresh`).
    - Vérifier qu'il est actif en DB (présent, non révoqué).
    - Révoquer l'ancien refresh, créer un nouveau refresh (nouveau jti) et un nouvel access (jti).

    Interactions
    - Persistance refresh tokens : `app/adapters/persistence/repositories/refresh_token.py`
    - JWT helpers : `app/core/security.py`

    Scénario nominal
    1) Lire `Authorization: Bearer <refresh>`.
    2) `decode_token` :
       - peut lever `TOKEN_INVALID` / `TOKEN_EXPIRED` (géré par exception handler).
    3) Vérifier claims (`typ`, `sub`, `jti`).
    4) Transaction UoW :
       - `get_active(jti)` puis `revoke(jti)` puis `add_active(new_jti)`
       - commit.
    5) Répondre enveloppé avec nouveaux tokens.

    Exceptions (HTTP)
    - 401 si header manquant, token invalide/expiré, token non refresh, token révoqué/inconnu.
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = auth.removeprefix("Bearer ").strip()

    payload = decode_token(token)
    if payload.get("typ") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    jti = payload.get("jti")
    if not isinstance(user_id, str) or not isinstance(jti, str):
        raise HTTPException(status_code=401, detail="Invalid token")

    settings = request.app.state.settings

    async with uow:
        db_token = await uow.refresh_tokens.get_active(jti=jti)
        if db_token is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        await uow.refresh_tokens.revoke(jti=jti)
        new_refresh_jti = str(ULID())
        new_access_jti = str(ULID())
        await uow.refresh_tokens.add_active(
            user_id=user_id, jti=new_refresh_jti, expires_days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await uow.commit()

    return success(
        request,
        data={
            "access_token": create_access_token(
                subject=user_id,
                jti=new_access_jti,
                expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            ),
            "refresh_token": create_refresh_token(
                subject=user_id,
                jti=new_refresh_jti,
                expires_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
            ),
            "token_type": "bearer",
        },
    )
