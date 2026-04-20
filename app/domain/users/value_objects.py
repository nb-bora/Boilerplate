from __future__ import annotations

"""
Value objects (Users).

Rôle
----
- `Email` : normalise et valide un email.
- `HashedPassword` : encapsule un hash de mot de passe (évite de manipuler des strings "nues").

Objectifs
---------
- Porter les invariants (format) dans le domaine.
- Forcer une normalisation uniforme (lower/strip) dès la construction.

Intervient dans
--------------
- Entité `User` : `app/domain/users/entity.py`
- Mapper ORM↔domain : `app/adapters/persistence/mappers/user.py`
- Use-cases : `app/application/auth/register.py`

Exceptions
----------
- `Email.__post_init__` lève `ValueError` si format invalide.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Email:
    """Email normalisé (lower/strip) avec validation minimale."""

    value: str

    def __post_init__(self) -> None:
        """
        Normalise et valide.

        Cas alternatifs
        - Validation volontairement minimale (V1) : la couche HTTP peut ajouter une validation plus stricte.
        """
        v = self.value.strip().lower()
        object.__setattr__(self, "value", v)
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")


@dataclass(frozen=True, slots=True)
class HashedPassword:
    """Value object représentant un hash (pas un mot de passe en clair)."""

    value: str
