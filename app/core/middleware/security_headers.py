from __future__ import annotations

"""
Middleware security headers.

Rôle
----
Appliquer des en-têtes HTTP de sécurité par défaut à toutes les réponses.

Objectifs
---------
- Réduire l'exposition aux attaques client-side (clickjacking, MIME sniffing, etc.).
- Fournir un baseline cohérent sans configuration.
- Activer HSTS uniquement dans des environnements TLS (preprod/prod).

Intervient dans
--------------
- Montage middleware : `app/main.py`
- Utilise `request.app.state.app_env` (initialisé dans `app/main.py`) pour décider HSTS.

Scénario nominal
----------------
1) Appelle le handler suivant.
2) Ajoute des headers (si non déjà présents).
3) Ajoute HSTS si `app_env ∈ {preprod, prod}`.

Cas alternatifs
--------------
- Si un proxy/serveur amont ajoute déjà certains headers, `setdefault` ne les écrase pas.
- Si `app.state.app_env` absent, HSTS n'est pas ajouté (safe default).

Exceptions
----------
- Ce middleware ne doit pas lever ; il doit rester best-effort.
"""

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
        """Ajoute les headers de sécurité après exécution de la route."""
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
