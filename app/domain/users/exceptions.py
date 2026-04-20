from __future__ import annotations

"""
Exceptions métier (Users).

Rôle
----
Définir des exceptions stables (code + message) utilisables par la couche Application,
et mappées vers HTTP par l'Adapter.

Objectifs
---------
- Les exceptions domaine ne connaissent pas HTTP mais portent un code stable `TECH.*` ou `DOMAIN.*`.
- L'Adapter HTTP décide du status code (401/403/404/409...).

Intervient dans
--------------
- Use-cases : `app/application/auth/*.py`, `app/application/users/get_me.py`
- Adapter HTTP : `app/adapters/http/exception_handlers.py` mappe `DomainError` → enveloppe.
"""

from dataclasses import dataclass


@dataclass(slots=True)
class DomainError(Exception):
    """Base des erreurs métier stables (code + message)."""
    code: str
    message: str


class UserAlreadyExists(DomainError):
    """Erreur métier : email déjà enregistré."""
    def __init__(self) -> None:
        super().__init__(code="DOMAIN.USER.ALREADY_EXISTS", message="Email already registered")


class InvalidCredentials(DomainError):
    """Erreur technique/métier : credentials invalides (anti-énumération)."""
    def __init__(self) -> None:
        super().__init__(code="TECH.AUTH.INVALID_CREDENTIALS", message="Invalid credentials")


class UserNotFound(DomainError):
    """Erreur métier : utilisateur introuvable."""
    def __init__(self) -> None:
        super().__init__(code="DOMAIN.USER.NOT_FOUND", message="User not found")


class UserInactive(DomainError):
    """Erreur métier : compte désactivé."""
    def __init__(self) -> None:
        super().__init__(code="DOMAIN.USER.INACTIVE", message="User inactive")
