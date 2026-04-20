from __future__ import annotations

"""
Schémas HTTP (Pydantic) pour la surface `auth`.

Rôle
----
Décrire et valider le contrat HTTP (request/response) au niveau Adapter.

Objectifs
---------
- Validation d'entrée : contraintes minimales (ex: mot de passe >= 8 chars).
- Séparer les schémas HTTP des DTO applicatifs (`app/application/auth/dto.py`) :
  l'Adapter peut évoluer (headers, champs, naming) sans impacter le cœur applicatif.

Intervient dans
--------------
- Routes : `app/adapters/http/v1/auth.py`

Cas alternatifs / exceptions
---------------------------
- Les erreurs de validation Pydantic sont converties en enveloppe 422 par
  `app/adapters/http/exception_handlers.py::validation_exception_handler`.
"""

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=256)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
