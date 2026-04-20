from __future__ import annotations

"""
Exception handlers FastAPI → enveloppe d'erreur.

Objectif
--------
Garantir que les erreurs fréquentes (validation, 404, 500) respectent le contrat d'enveloppe.

Workflows documentés
--------------------

Validation (422)
~~~~~~~~~~~~~~~~
Cas nominal
- Les erreurs de validation FastAPI/Pydantic sont converties en `TECH.VALIDATION.*`.
- Chaque erreur produit un `ErrorDetail` avec `field` si disponible.

Cas alternatifs
- Si le champ n'est pas déterminable, `field=null`.

Cas d'exception
- En cas de structure inattendue de l'erreur, on renvoie une erreur générique de validation.

Erreur interne (500)
~~~~~~~~~~~~~~~~~~~~
Cas nominal
- Toute exception non gérée renvoie une enveloppe `TECH.INTERNAL`.
"""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.adapters.http.response import error
from app.common.response_envelope import ErrorDetail
from app.core.logging import get_logger
from app.domain.users.exceptions import DomainError


def _field_from_loc(loc: tuple[object, ...]) -> str | None:
    # loc typique: ("body", "email") ou ("query", "limit")
    parts = [str(p) for p in loc if p not in ("body", "query", "path", "header")]
    return ".".join(parts) if parts else None


def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details: list[ErrorDetail] = []
    for e in exc.errors():
        loc = tuple(e.get("loc") or ())
        field = _field_from_loc(loc)
        typ = str(e.get("type") or "")
        code = "TECH.VALIDATION.INVALID"
        if typ.endswith("missing"):
            code = "TECH.VALIDATION.REQUIRED"
        details.append(
            ErrorDetail(code=code, message=str(e.get("msg") or "Validation error"), field=field)
        )

    payload, status_code = error(
        request, message="Validation error", errors=details, status_code=422
    )
    return JSONResponse(content=payload, status_code=status_code)


def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code == 404:
        code = "TECH.NOT_FOUND"
    elif exc.status_code == 401:
        code = "TECH.AUTH.TOKEN_INVALID"
    elif exc.status_code == 403:
        code = "TECH.AUTH.UNAUTHORIZED"
    elif exc.status_code == 429:
        code = "TECH.RATE_LIMIT.TOO_MANY_REQUESTS"
    elif exc.status_code == 409:
        code = "TECH.CONFLICT"
    else:
        code = "TECH.INTERNAL"
    payload, status_code = error(
        request,
        message=exc.detail if isinstance(exc.detail, str) else "HTTP error",
        errors=[ErrorDetail(code=code, message="HTTP error")],
        status_code=exc.status_code,
    )
    return JSONResponse(content=payload, status_code=status_code)


def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: BLE001
    log = get_logger()
    log.error("unhandled_exception", error=str(exc))
    if isinstance(exc, DomainError):
        status = 400
        if exc.code == "DOMAIN.USER.ALREADY_EXISTS":
            status = 409
        elif exc.code == "DOMAIN.USER.NOT_FOUND":
            status = 404
        elif exc.code == "DOMAIN.USER.INACTIVE":
            status = 403
        elif exc.code == "TECH.AUTH.INVALID_CREDENTIALS":
            status = 401
        payload, status_code = error(
            request,
            message=exc.message,
            errors=[ErrorDetail(code=exc.code, message=exc.message)],
            status_code=status,
        )
        return JSONResponse(content=payload, status_code=status_code)
    if isinstance(exc, ValueError) and str(exc) in {"TOKEN_INVALID", "TOKEN_EXPIRED"}:
        code = (
            "TECH.AUTH.TOKEN_INVALID" if str(exc) == "TOKEN_INVALID" else "TECH.AUTH.TOKEN_EXPIRED"
        )
        payload, status_code = error(
            request,
            message="Token error",
            errors=[ErrorDetail(code=code, message="Token error")],
            status_code=401,
        )
        return JSONResponse(content=payload, status_code=status_code)
    payload, status_code = error(
        request,
        message="Internal error",
        errors=[ErrorDetail(code="TECH.INTERNAL", message="Internal error")],
        status_code=500,
    )
    return JSONResponse(content=payload, status_code=status_code)
