from __future__ import annotations

"""
Configuration applicative (Pydantic Settings).

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
    """
    return Settings()
