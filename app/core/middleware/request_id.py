from __future__ import annotations

from ulid import ULID

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        incoming_correlation = request.headers.get("X-Correlation-Id")
        incoming_request_id = request.headers.get("X-Request-Id")

        request_id = incoming_request_id or str(ULID())
        correlation_id = incoming_correlation or request_id

        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        response: Response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Correlation-Id"] = correlation_id
        return response

