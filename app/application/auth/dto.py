from __future__ import annotations

"""
DTOs applicatifs (Auth).

Rôle
----
Définir des modèles d'entrée/sortie pour les use-cases d'authentification.

Objectifs
---------
- Stabiliser l'interface Application (indépendante des détails HTTP).
- Centraliser la validation minimale de l'entrée (ex: taille du password).

Intervient dans
--------------
- Use-cases : `register.py`, `login.py`
- Adapter HTTP : convertit schemas HTTP → DTOs (`app/adapters/http/v1/auth.py`)

Cas alternatifs / exceptions
---------------------------
- Les erreurs de validation Pydantic peuvent être :
  - interceptées côté HTTP (422) si la validation est déclenchée lors du parsing des DTOs,
  - ou gérées par le code appelant selon le contexte.
"""

from pydantic import BaseModel, Field


class RegisterInput(BaseModel):
    """Entrée de `RegisterUser`."""
    email: str
    password: str = Field(min_length=8, max_length=256)


class LoginInput(BaseModel):
    """Entrée de `LoginUser`."""
    email: str
    password: str


class TokenOutput(BaseModel):
    """Sortie commune : paire access/refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
