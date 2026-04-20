from __future__ import annotations

"""
Helpers HTTP pour produire l'enveloppe de réponse.

Workflows documentés
--------------------

Cas nominal (succès)
- Utiliser `success(request, data=...)` dans les handlers FastAPI.
- `request.state.request_id` est injecté par `RequestIdMiddleware`.

Cas alternatifs
- Si le middleware n'a pas été exécuté (tests très bas niveau), `request_id` peut être vide.

Cas d'exception
- Ces fonctions doivent rester "sans side-effects" : elles ne font que sérialiser des modèles.
"""

from typing import Any

from fastapi import Request

from app.common.response_envelope import EnvelopeMeta, ErrorDetail, ErrorEnvelope, SuccessEnvelope


def success(request: Request, data: Any, message: str | None = None) -> dict[str, Any]:
    request_id = getattr(request.state, "request_id", "")
    env = SuccessEnvelope(data=data, message=message, meta=EnvelopeMeta(request_id=request_id))
    return env.model_dump()


def error(
    request: Request, message: str, errors: list[ErrorDetail], *, status_code: int
) -> tuple[dict[str, Any], int]:
    request_id = getattr(request.state, "request_id", "")
    env = ErrorEnvelope(message=message, errors=errors, meta=EnvelopeMeta(request_id=request_id))
    return env.model_dump(), status_code
