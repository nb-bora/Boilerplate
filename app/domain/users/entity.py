from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.domain.base import Entity
from app.domain.users.value_objects import Email, HashedPassword


class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"


@dataclass(slots=True)
class User(Entity):
    email: Email = field(default_factory=lambda: Email("user@example.com"))
    hashed_password: HashedPassword = field(default_factory=lambda: HashedPassword(""))
    roles: list[Role] = field(default_factory=lambda: [Role.USER])
    is_active: bool = True

    def has_permission(self, permission: str) -> bool:
        # V1 : mapping simple rôles → permissions.
        if Role.ADMIN in self.roles:
            return True
        return permission in set()
