from __future__ import annotations

"""
Contexte de requête via `contextvars`.

Rôle
----
Fournir un mécanisme "thread-safe / task-safe" pour accéder à certaines valeurs de contexte
sans les propager explicitement partout (ex: request_id, IP).

Objectifs
---------
- Permettre à la couche Application d'injecter du contexte (request_id/ip) dans les événements de domaine
  sans dépendre des objets HTTP (`Request`) ni de `request.state`.

Intervient dans
--------------
- Middleware : `app/core/middleware/request_id.py` renseigne les variables.
- Use-cases : `app/application/auth/register.py`, `app/application/auth/login.py` lisent `get_request_id/get_ip`.

Scénario nominal
----------------
- Au début d'une requête : middleware set `request_id_var` et `ip_var`.
- Plus tard : `get_request_id()` / `get_ip()` récupèrent la valeur courante.

Cas alternatifs
--------------
- Hors contexte HTTP (scripts, tests sans middleware) : les valeurs peuvent être `None`.

Exceptions
----------
- Aucune : accès/assignation via contextvars.
"""

import contextvars

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
ip_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("ip", default=None)


def get_request_id() -> str | None:
    """Retourne le request_id courant, ou `None` si non défini."""
    return request_id_var.get()


def get_ip() -> str | None:
    """Retourne l'IP courante, ou `None` si non définie."""
    return ip_var.get()
