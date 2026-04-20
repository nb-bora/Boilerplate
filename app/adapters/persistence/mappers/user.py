from __future__ import annotations

"""
Mapper ORM ↔ Domain : User.

Rôle
----
Convertir entre :
- `UserModel` (SQLAlchemy ORM) et
- `User` (entité domaine).

Objectifs
---------
- Empêcher la fuite de types ORM dans le domaine/application.
- Centraliser la normalisation/translation (roles, value objects).

Intervient dans
--------------
- Repos : `app/adapters/persistence/repositories/user.py`
- Domaine : `app/domain/users/*`

Exceptions
----------
- `Role(r)` peut lever si la valeur DB n'est pas un rôle valide (donnée corrompue).
- `Email(model.email)` peut lever si l'email stocké est invalide (donnée corrompue).
"""

from app.adapters.persistence.models.user import UserModel
from app.domain.users.entity import Role, User
from app.domain.users.value_objects import Email, HashedPassword


def to_domain(model: UserModel) -> User:
    """Mappe `UserModel` → `User` (domaine)."""
    return User(
        id=model.id,
        email=Email(model.email),
        hashed_password=HashedPassword(model.hashed_password),
        roles=[Role(r) for r in model.roles],
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_model(user: User) -> UserModel:
    """Mappe `User` (domaine) → `UserModel` (ORM)."""
    return UserModel(
        id=user.id,
        email=user.email.value,
        hashed_password=user.hashed_password.value,
        roles=[r.value for r in user.roles],
        is_active=user.is_active,
    )
