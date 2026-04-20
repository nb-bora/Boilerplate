from __future__ import annotations

"""
DTOs applicatifs (Users).

Rôle
----
Définir la forme des données renvoyées par les use-cases Users.

Objectifs
---------
- Stabiliser l'API interne de la couche Application.
- Eviter d'exposer directement des entités du domaine au niveau adapter HTTP.
"""

from pydantic import BaseModel


class UserOutput(BaseModel):
    """Sortie applicative d'un user (profil)."""
    id: str
    email: str
    roles: list[str]
    is_active: bool
