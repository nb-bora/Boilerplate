from __future__ import annotations

"""
Port `IUserRepository`.

Rôle
----
Définir l'interface de persistance des users (recherche + ajout).

Objectifs
---------
- Permettre à la couche Application de manipuler des `User` sans connaître l'ORM.

Intervient dans
--------------
- Adapter persistence : `app/adapters/persistence/repositories/user.py` implémente.
"""

from typing import Protocol

from app.domain.users.entity import User


class IUserRepository(Protocol):
    """Port de persistance des users."""
    async def get_by_id(self, user_id: str) -> User | None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def add(self, user: User) -> None: ...
