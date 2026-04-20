from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logging import get_logger


def _parse_traceparent(value: str | None) -> tuple[str | None, str | None]:
    """
    Parse minimal d'un header W3C traceparent.

    Format: version-trace-id-span-id-flags (hex) ex:
    00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
    """
    if not value:
        return None, None
    parts = value.split("-")
    if len(parts) != 4:
        return None, None
    _ver, trace_id, span_id, _flags = parts
    if len(trace_id) != 32 or len(span_id) != 16:
        return None, None
    try:
        int(trace_id, 16)
        int(span_id, 16)
    except ValueError:
        return None, None
    if trace_id == "0" * 32 or span_id == "0" * 16:
        return None, None
    return trace_id, span_id


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)

        request_id = getattr(request.state, "request_id", None)
        correlation_id = getattr(request.state, "correlation_id", None)
        trace_id, span_id = _parse_traceparent(request.headers.get("traceparent"))

        log = get_logger()
        log.info(
            "request_finished",
            request_id=request_id,
            correlation_id=correlation_id,
            user_id=getattr(request.state, "user_id", None),
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=duration_ms,
            trace_id=trace_id,
            span_id=span_id,
        )
        return response
