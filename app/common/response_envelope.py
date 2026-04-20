from __future__ import annotations

"""
Contrat d'enveloppe de réponse.

Rôle
----
Définir le *contrat* de sérialisation des réponses API (succès/erreur) sous forme de modèles Pydantic.
Ces modèles sont utilisés par l'Adapter HTTP pour garantir une enveloppe uniforme.

Objectifs
---------
- Standardiser la structure de réponse pour toutes les routes.
- Fournir un endroit unique pour faire évoluer le contrat (ajouts dans `meta`, champs d'erreur, etc.).

Intervient dans
--------------
- Helpers : `app/adapters/http/response.py` construit ces modèles.
- Exception mapping : `app/adapters/http/exception_handlers.py` produit des `ErrorDetail`.

Scénarios nominaux
-----------------
- `SuccessEnvelope` :
  - `success=true`, `data` non null, `errors=null`, `meta.request_id` présent.
- `ErrorEnvelope` :
  - `success=false`, `data=null`, `errors[]` non vide, `meta.request_id` présent.

Cas alternatifs
--------------
- `data` peut être de tout type JSON-serializable (dict, list, primitive).
- `field` dans `ErrorDetail` peut être null si non déterminable.

Exceptions
----------
- Ces classes ne devraient pas lever en usage normal.
- Toute erreur indiquerait un problème de sérialisation (ex: objet non JSON-serializable dans `data`).

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
    """
    Détail d'erreur stable.

    Champs
    - `code` : code stable (TECH.* / DOMAIN.*).
    - `message` : message lisible humain.
    - `field` : chemin du champ en erreur (optionnel), ex: "email".
    """

    code: str
    message: str
    field: str | None = None


class EnvelopeMeta(BaseModel):
    """
    Métadonnées transverses de réponse.

    Convention
    - `request_id` : toujours présent et identique au header `X-Request-Id`.
    """

    request_id: str


class SuccessEnvelope(BaseModel):
    """Enveloppe de succès uniforme."""

    success: Literal[True] = True
    data: Any
    message: str | None = None
    errors: None = None
    meta: EnvelopeMeta


class ErrorEnvelope(BaseModel):
    """Enveloppe d'erreur uniforme."""

    success: Literal[False] = False
    data: None = None
    message: str
    errors: list[ErrorDetail]
    meta: EnvelopeMeta
