from __future__ import annotations

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
