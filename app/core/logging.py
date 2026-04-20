from __future__ import annotations

"""
Configuration des logs structurés (JSON).

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
    """
    return structlog.get_logger()
