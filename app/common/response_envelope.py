from __future__ import annotations

"""
Contrat d'enveloppe de réponse.

Workflows documentés
--------------------

Réponses succès
~~~~~~~~~~~~~~~
Cas nominal
- `SuccessEnvelope.success = true`
- `data` contient le payload métier
- `errors = null`
- `meta.request_id` est toujours présent

Réponses erreur
~~~~~~~~~~~~~~~
Cas nominal
- `ErrorEnvelope.success = false`
- `data = null`
- `message` est lisible par un humain
- `errors[]` contient une liste de `ErrorDetail` (code stable + message + field optionnel)
- `meta.request_id` est toujours présent

Cas d'exception
- Cette couche est purement déclarative (Pydantic) : elle ne doit pas lever en usage normal.
"""

from typing import Any, Literal

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None


class EnvelopeMeta(BaseModel):
    request_id: str


class SuccessEnvelope(BaseModel):
    success: Literal[True] = True
    data: Any
    message: str | None = None
    errors: None = None
    meta: EnvelopeMeta


class ErrorEnvelope(BaseModel):
    success: Literal[False] = False
    data: None = None
    message: str
    errors: list[ErrorDetail]
    meta: EnvelopeMeta
