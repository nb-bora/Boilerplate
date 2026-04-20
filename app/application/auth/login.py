from __future__ import annotations

"""
Use-case Application : LoginUser.

Rôle
----
Orchestrer la connexion :
- récupérer l'utilisateur par email,
- vérifier statut actif,
- vérifier mot de passe (bcrypt),
- persister un refresh token actif,
- émettre un événement de domaine,
- retourner access+refresh tokens.

Objectifs
---------
- Implémenter l'anti-énumération : mêmes signaux d'erreur côté client pour
  "email inconnu" et "mauvais mot de passe".
- Garder HTTP/DB/Redis hors du domaine.

Intervient dans
--------------
- Adapter HTTP : `app/adapters/http/v1/auth.py::login`
- UoW / repos : `app/adapters/persistence/unit_of_work.py`
- Sécurité : `app/core/security.py` (verify + JWT)
- Contexte request : `app/core/context.py` (request_id, ip)

Scénario nominal
----------------
1) Ouvre le UoW.
2) Cherche user par email.
3) Vérifie `is_active`.
4) Vérifie mot de passe (constant-time via passlib).
5) Ajoute un refresh token actif.
6) Bufferise `UserLoggedIn` puis commit (dispatch post-commit).
7) Retourne tokens.

Cas alternatifs / exceptions attendues
-------------------------------------
- `InvalidCredentials` si user absent OU mdp incorrect (anti-énumération).
- `UserInactive` si compte désactivé.
- Exceptions DB au commit si infra down.
"""

from ulid import ULID

from app.application.auth.dto import LoginInput, TokenOutput
from app.core.config import get_settings
from app.core.context import get_ip, get_request_id
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.domain.users.events import UserLoggedIn
from app.domain.users.exceptions import InvalidCredentials, UserInactive


class LoginUser:
    """Use-case de connexion."""

    def __init__(self, *, uow) -> None:  # noqa: ANN001
        self.uow = uow

    async def execute(self, data: LoginInput) -> TokenOutput:
        """Exécute la connexion et retourne des tokens."""
        settings = get_settings()
        async with self.uow:
            user = await self.uow.users.get_by_email(data.email)
            # Anti-énumération : même exception pour "unknown email" et "bad password".
            if user is None:
                raise InvalidCredentials()
            if not user.is_active:
                raise UserInactive()
            if not verify_password(data.password, user.hashed_password.value):
                raise InvalidCredentials()

            refresh_jti = str(ULID())
            access_jti = str(ULID())
            await self.uow.refresh_tokens.add_active(
                user_id=user.id, jti=refresh_jti, expires_days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
            self.uow.collect_event(
                UserLoggedIn(
                    aggregate_id=user.id, payload={"request_id": get_request_id(), "ip": get_ip()}
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
