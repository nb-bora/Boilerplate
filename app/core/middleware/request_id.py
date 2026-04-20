from __future__ import annotations

"""
Middleware request_id / correlation_id.

Workflows documentés
--------------------

Propagation d'identifiants
~~~~~~~~~~~~~~~~~~~~~~~~~~
Cas nominal
- Si le client fournit `X-Request-Id`, on le reprend tel quel.
- Sinon, on génère un ULID.
- `X-Correlation-Id` est propagé si fourni ; sinon il est aligné sur `X-Request-Id`.
- Les deux headers sont toujours renvoyés en réponse.

Cas alternatifs
- Si un proxy fournit seulement `X-Correlation-Id`, le `X-Request-Id` est généré et la corrélation
  est conservée via `X-Correlation-Id`.

Cas d'exception
- Aucun : le middleware ne doit jamais faire échouer une requête ; il vise la robustesse DX/ops.

Intervient dans
--------------
- Helpers enveloppe : `app/adapters/http/response.py` lit `request.state.request_id`.
- Logging middleware : `app/core/middleware/logging.py` logge les IDs.
- Contextvars : `app/core/context.py` expose `get_request_id/get_ip` pour les use-cases.

Scénario nominal
----------------
1) Lire `X-Request-Id` et `X-Correlation-Id` entrants.
2) Générer un ULID si `X-Request-Id` absent.
3) Aligner corrélation sur request_id si absent.
4) Injecter dans `request.state` + `contextvars`.
5) Ajouter les headers en réponse.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from ulid import ULID

from app.core.context import ip_var, request_id_var


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """
        Injecte `request_id`/`correlation_id` dans `request.state` et les headers de réponse.

        Cas alternatifs
        - `request.client` absent : `ip_var` est set à None.
        """
        incoming_correlation = request.headers.get("X-Correlation-Id")
        incoming_request_id = request.headers.get("X-Request-Id")

        request_id = incoming_request_id or str(ULID())
        correlation_id = incoming_correlation or request_id

        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        request_id_var.set(request_id)
        ip_var.set(request.client.host if request.client else None)

        response: Response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Correlation-Id"] = correlation_id
        return response
