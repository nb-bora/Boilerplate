from __future__ import annotations

"""
Entité domaine : User.

Rôle
----
Représenter un utilisateur (identité + auth) au niveau domaine.

Objectifs
---------
- Encapsuler les attributs métier (email, rôles, statut actif).
- Offrir des méthodes métier (ex: `has_permission`) sans dépendre de HTTP/DB.

Intervient dans
--------------
- Use-cases : register/login/get_me
- Persistence mapper : `app/adapters/persistence/mappers/user.py`

Cas alternatifs / limitations
----------------------------
- `has_permission` est minimaliste en V1 (admin => tout, sinon rien). Extension V2 prévue.
"""

from dataclasses import dataclass, field
from enum import Enum

from app.domain.base import Entity
from app.domain.users.value_objects import Email, HashedPassword


class Role(str, Enum):
    """Rôle utilisateur (RBAC minimal)."""
    ADMIN = "admin"
    USER = "user"


@dataclass(slots=True)
class User(Entity):
    """Entité User (domaine)."""
    email: Email = field(default_factory=lambda: Email("user@example.com"))
    hashed_password: HashedPassword = field(default_factory=lambda: HashedPassword(""))
    roles: list[Role] = field(default_factory=lambda: [Role.USER])
    is_active: bool = True

    def has_permission(self, permission: str) -> bool:
        """
        Vérifie une permission.

        Scénario nominal (V1)
        - ADMIN : toujours True.
        - USER : aucune permission implicite (retourne False).
        """
        # V1 : mapping simple rôles → permissions.
        if Role.ADMIN in self.roles:
            return True
        return permission in set()
