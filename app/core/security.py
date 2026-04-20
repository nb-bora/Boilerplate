from __future__ import annotations

"""
Primitives de sécurité : hashing + JWT (HS256).

Rôle
----
- Hashing : `hash_password` / `verify_password` (bcrypt via passlib).
- JWT :
  - création access token (claims: sub, jti, iat, exp),
  - création refresh token (claims: sub, jti, iat, exp, typ=refresh),
  - décodage/validation (signature + exp).

Objectifs
---------
- Centraliser l'implémentation crypto et éviter la duplication.
- Garder la couche Application simple : elle appelle ces helpers.
- Fournir des erreurs normalisées (`TOKEN_INVALID` / `TOKEN_EXPIRED`) mappées en HTTP.

Intervient dans
--------------
- Use-cases : `app/application/auth/*.py` (create_* + verify_password)
- Dépendances HTTP : `app/adapters/http/dependencies.py` (decode_token)
- Exception handlers : `app/adapters/http/exception_handlers.py` mappe `ValueError("TOKEN_*")`.

Scénarios nominaux
-----------------
- Hashing :
  - `hash_password` retourne un hash bcrypt.
  - `verify_password` compare en constant-time (impl passlib).
- JWT :
  - encode payload avec `APP_SECRET_KEY`.
  - decode valide la signature et l'expiration.

Cas alternatifs
--------------
- `APP_SECRET_KEY` vide : en dev/test, ça peut fonctionner mais est insecure.
  En prod, doit être un secret fort (README).

Exceptions
----------
- `decode_token` :
  - lève `ValueError("TOKEN_EXPIRED")` si exp dépassée,
  - lève `ValueError("TOKEN_INVALID")` si signature/format invalide.
"""

from datetime import datetime, timedelta, timezone

from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash un mot de passe en bcrypt (stockage DB)."""
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe en comparant au hash bcrypt stocké."""
    return pwd_context.verify(password, hashed_password)


def create_access_token(*, subject: str, jti: str, expires_minutes: int) -> str:
    """
    Crée un access token JWT.

    Claims
    - `sub` : user_id
    - `jti` : identifiant unique du token (révocation via blacklist Redis optionnelle)
    - `iat` / `exp` : timestamps epoch seconds
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.APP_SECRET_KEY, algorithm="HS256")


def create_refresh_token(*, subject: str, jti: str, expires_days: int) -> str:
    """
    Crée un refresh token JWT.

    Différences vs access token
    - Claim `typ="refresh"` pour distinguer l'usage.
    - Durée typiquement plus longue.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=expires_days)).timestamp()),
        "typ": "refresh",
    }
    return jwt.encode(payload, settings.APP_SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    """
    Décode et valide un JWT.

    Retour
    - dict payload si token valide.

    Exceptions
    - `ValueError("TOKEN_EXPIRED")` si le token est expiré.
    - `ValueError("TOKEN_INVALID")` sinon.
    """
    settings = get_settings()
    try:
        return jwt.decode(token, settings.APP_SECRET_KEY, algorithms=["HS256"])
    except ExpiredSignatureError as exc:
        raise ValueError("TOKEN_EXPIRED") from exc
    except JWTError as exc:
        raise ValueError("TOKEN_INVALID") from exc
