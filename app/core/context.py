from __future__ import annotations

import contextvars

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
ip_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("ip", default=None)


def get_request_id() -> str | None:
    return request_id_var.get()


def get_ip() -> str | None:
    return ip_var.get()
