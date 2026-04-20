from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Ajoute des headers de sécurité par défaut.

    Spécification README V1 :
    - Toujours : nosniff, DENY, referrer-policy, CSP, permissions-policy
    - Strict-Transport-Security : uniquement en preprod/prod
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )

        app_env = getattr(getattr(request, "app", None), "state", None)
        env_value = getattr(app_env, "app_env", None)
        if env_value in {"preprod", "prod"}:
            response.headers.setdefault("Strict-Transport-Security", "max-age=63072000")

        return response
