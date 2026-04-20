from __future__ import annotations

"""
Schémas HTTP (Pydantic) pour la surface `users`.

Rôle
----
Décrire la forme des réponses HTTP exposées par l'Adapter Users.

Note
----
Dans ce boilerplate, certaines routes retournent directement des DTO applicatifs sérialisés.
Ce module sert de point d'ancrage si l'on veut stabiliser et versionner des schémas HTTP
distincts des DTOs applicatifs.
"""

from pydantic import BaseModel


class MeResponse(BaseModel):
    id: str
    email: str
    roles: list[str]
    is_active: bool
