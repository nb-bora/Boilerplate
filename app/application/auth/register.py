from __future__ import annotations

"""
Use-case Application : RegisterUser.

Rôle
----
Orchestrer l'inscription :
- vérifier l'unicité email,
- créer l'utilisateur (domaine),
- persister (via repos du UoW),
- émettre un événement de domaine,
- retourner des tokens (access + refresh).

Objectifs
---------
- Concentrer la logique d'orchestration (workflow) dans la couche Application.
- Garder le domaine indépendant des détails de persistance/HTTP.
- Produire des événements utilisables post-commit (audit, intégrations futures).

Intervient dans
--------------
- Adapter HTTP : `app/adapters/http/v1/auth.py::register`
- UoW : `app/adapters/persistence/unit_of_work.py`
- Repos :
  - users : `app/adapters/persistence/repositories/user.py`
  - refresh_tokens : `app/adapters/persistence/repositories/refresh_token.py`
- Sécurité : `app/core/security.py` (hash + JWT)
- Contexte request : `app/core/context.py` (request_id, ip)

Scénario nominal
----------------
1) `async with uow:` ouvre une session transactionnelle.
2) `users.get_by_email` : si existe → conflit.
3) Crée un `User` (Email VO, HashedPassword VO) et l'ajoute au repo.
4) Crée un refresh token actif en DB.
5) Bufferise un event `UserRegistered` (payload minimal + contexte request_id/ip).
6) `uow.commit()` commit DB, puis dispatch post-commit.
7) Retourne `TokenOutput` (JWT access + refresh).

Cas alternatifs
--------------
- Si DB down, le commit échouera et remontera une exception (en HTTP → enveloppe 500).

Exceptions attendues
--------------------
- `UserAlreadyExists` si email déjà enregistré (HTTP 409 via exception handler).
- `ValueError` potentielle depuis `Email(...)` si format invalide (typiquement déjà filtré côté HTTP).
"""

from ulid import ULID

from app.application.auth.dto import RegisterInput, TokenOutput
from app.core.config import get_settings
from app.core.context import get_ip, get_request_id
from app.core.security import create_access_token, create_refresh_token, hash_password
from app.domain.users.entity import User
from app.domain.users.events import UserRegistered
from app.domain.users.exceptions import UserAlreadyExists
from app.domain.users.value_objects import Email, HashedPassword


class RegisterUser:
    """Use-case d'inscription."""

    def __init__(self, *, uow) -> None:  # noqa: ANN001
        self.uow = uow

    async def execute(self, data: RegisterInput) -> TokenOutput:
        """
        Exécute l'inscription.

        Paramètres
        - `data` : DTO applicatif (email + password).

        Retour
        - `TokenOutput` : access_token + refresh_token.
        """
        settings = get_settings()
        async with self.uow:
            existing = await self.uow.users.get_by_email(data.email)
            if existing is not None:
                raise UserAlreadyExists()

            user = User(
                email=Email(data.email),
                hashed_password=HashedPassword(hash_password(data.password)),
            )
            await self.uow.users.add(user)

            refresh_jti = str(ULID())
            access_jti = str(ULID())
            await self.uow.refresh_tokens.add_active(
                user_id=user.id, jti=refresh_jti, expires_days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )

            self.uow.collect_event(
                UserRegistered(
                    aggregate_id=user.id,
                    payload={
                        "email": user.email.value,
                        "request_id": get_request_id(),
                        "ip": get_ip(),
                    },
                )
            )
            await self.uow.commit()

        return TokenOutput(
            access_token=create_access_token(
                subject=user.id,
                jti=access_jti,
                expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            ),
            refresh_token=create_refresh_token(
                subject=user.id, jti=refresh_jti, expires_days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            ),
        )
