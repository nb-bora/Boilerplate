from __future__ import annotations

from app.adapters.persistence.models.user import UserModel
from app.domain.users.entity import Role, User
from app.domain.users.value_objects import Email, HashedPassword


def to_domain(model: UserModel) -> User:
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
    return UserModel(
        id=user.id,
        email=user.email.value,
        hashed_password=user.hashed_password.value,
        roles=[r.value for r in user.roles],
        is_active=user.is_active,
    )
