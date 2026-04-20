from __future__ import annotations

"""
Configuration applicative (Pydantic Settings).

Rôle
----
Ce module définit `Settings` (Pydantic BaseSettings) et `get_settings()` (singleton cache)
pour centraliser la configuration runtime : env, secrets, DB, Redis, et flags.

Objectifs
---------
- Charger `.env` (si présent) + variables d'environnement.
- Fournir une API typée et stable.
- Valider des politiques de sécurité (ex: CORS wildcard interdit en prod).

Intervient dans
--------------
- Composition root : `app/main.py` charge et stocke `app.state.settings`.
- Sécurité : `app/core/security.py` lit `APP_SECRET_KEY` + expirations.
- Infra DB/Redis : engine et client sont construits à partir de ces settings.
- Adapters : rate limiting, idempotency, Redis enabled, etc.

Scénarios nominaux
-----------------
- Chargement : les champs ont des defaults permettant un clone/run rapide.
- Parsing : `CORS_ORIGINS` est converti en liste via `cors_origins_list`.
- Validation : `validate_cors_policy` bloque une configuration dangereuse en prod.

Cas alternatifs
--------------
- `.env` absent : Pydantic lit uniquement l'environnement process.
- `CORS_ORIGINS` avec espaces/valeurs vides : nettoyé/ignoré.

Exceptions
----------
- Pydantic lève si types invalides (ex: bool mal formé).
- `validate_cors_policy` lève `ValueError` si policy violée (prod + wildcard).

Workflows documentés
--------------------

Chargement de configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~
Cas nominal
- Les variables d'environnement sont chargées depuis le process, et `.env` si présent.
- Les clés inconnues sont ignorées (`extra="ignore"`) pour faciliter l'onboarding.
- `CORS_ORIGINS` est une liste CSV d'origins.

Cas alternatifs
- Si `.env` est absent, seule l'environnement système est utilisé (comportement standard).
- Si `CORS_ORIGINS` contient des espaces, ils sont supprimés lors du parsing.

Cas d'exception
- Si certaines variables sont mal typées (ex: `REDIS_ENABLED=notabool`), Pydantic lèvera une
  erreur au chargement.

Remarque
--------
La validation "policy" (ex: interdire `*` en prod) peut être ajoutée via validators, mais n'est
pas encore appliquée dans cette V1 minimaliste.
"""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Settings runtime typés.

    Notes
    - Les champs sont volontairement "DX-friendly" en dev.
    - En prod, certaines politiques doivent être satisfaites (ex: secret fort, CORS strict).
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_ENV: str = Field(default="dev")
    APP_NAME: str = Field(default="fastapi-boilerplate")
    APP_LOG_LEVEL: str = Field(default="info")

    APP_SECRET_KEY: str = Field(default="")
    CORS_ORIGINS: str = Field(default="http://localhost:3000")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/boilerplate"
    )

    REDIS_ENABLED: bool = Field(default=False)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_RETRY_ATTEMPTS: int = Field(default=3)
    REDIS_RETRY_BACKOFF_MS: int = Field(default=100)

    RATE_LIMIT_LOGIN_PER_MINUTE: int = Field(default=5)
    RATE_LIMIT_REGISTER_PER_HOUR: int = Field(default=10)

    IDEMPOTENCY_TTL_SECONDS: int = Field(default=900)

    SOFT_DELETE_ENABLED: bool = Field(default=False)
    MYPY_STRICT: bool = Field(default=False)

    @model_validator(mode="after")
    def validate_cors_policy(self) -> Settings:
        """
        Valide les politiques de configuration.

        Scénario nominal
        - En dev/test/staging : pas de restriction supplémentaire.

        Exception
        - En prod : interdit `*` dans `CORS_ORIGINS`.
        """
        # En prod, interdire le wildcard pour éviter une exposition involontaire.
        if self.APP_ENV == "prod" and "*" in self.cors_origins_list:
            raise ValueError("CORS wildcard interdit en production")
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        """
        Parse `CORS_ORIGINS` en liste d'origins.

        Cas nominal
        - `http://localhost:3000,https://app.example.com` → `["http://localhost:3000", "https://app.example.com"]`

        Cas alternatifs
        - Champs vides ignorés : `a,,b` → `["a", "b"]`
        """
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """
    Retourne une instance singleton de `Settings`.

    Cas nominal
    - Évite de reparcourir l'environnement à chaque injection.

    Cas alternatifs
    - En test : si besoin de recharger, il faut invalider le cache LRU (ou ne pas utiliser le singleton).
    """
    return Settings()
