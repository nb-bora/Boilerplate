from __future__ import annotations

"""
Configuration des logs structurés (JSON).

Rôle
----
Configurer `structlog` pour produire des logs JSON homogènes.

Objectifs
---------
- Logs structurés (machine-readable) pour ingestion (ELK, Loki, Datadog...).
- `timestamp` UTC + `level` ajoutés automatiquement.
- Format d'exception sérialisé (`format_exc_info`).

Intervient dans
--------------
- Composition root : `app/main.py` appelle `configure_logging(APP_LOG_LEVEL)` au démarrage.
- Middleware : `app/core/middleware/logging.py` logge `request_finished`.
- Infra/event bus : logs d'erreur de handlers, etc.

Scénarios nominaux
-----------------
- `configure_logging("info")` configure stdlib logging + structlog.
- `get_logger()` retourne un BoundLogger prêt à `.info/.warning/.error`.

Cas alternatifs
--------------
- `log_level` invalide : fallback INFO.

Exceptions
----------
- Ne doit pas lever en usage normal ; les erreurs d'exception rendering sont encapsulées.

Workflows documentés
--------------------

Initialisation
~~~~~~~~~~~~~~
Cas nominal
- `configure_logging()` configure le logger stdlib + structlog en JSON.
- Les logs incluent `timestamp` (UTC ISO) et `level`.

Cas alternatifs
- Si `log_level` est invalide, on retombe sur `INFO`.

Cas d'exception
- Toute exception lors du rendu est capturée via `format_exc_info` (trace dans le JSON).
"""

import logging

import structlog


def configure_logging(log_level: str = "info") -> None:
    """
    Configure le pipeline structlog.

    Cas nominal
    - Le niveau de log est appliqué au logger stdlib et au BoundLogger structlog.

    Exceptions
    - Aucune attendue ; si un processor lève, `format_exc_info` capture l'exception.
    """
    logging.basicConfig(level=getattr(logging, log_level.upper(), logging.INFO))

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )


def get_logger() -> structlog.stdlib.BoundLogger:
    """
    Retourne un logger structlog.

    Cas nominal
    - Utiliser `get_logger().info("event", key=value)` pour des logs JSON.

    Cas alternatifs
    - Dans certains environnements, la configuration peut être faite ailleurs ; `get_logger()`
      retourne malgré tout un logger structlog (avec config par défaut).
    """
    return structlog.get_logger()
