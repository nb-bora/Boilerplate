from __future__ import annotations

"""
Constantes globales.

Rôle
----
Centraliser les codes d'erreur stables utilisés par le boilerplate.

Objectifs
---------
- Garantir que les codes renvoyés aux clients sont :
  - prévisibles,
  - documentables,
  - testables (tests de contrat).

Intervient dans
--------------
- Exceptions domaine : typiquement portent des codes `DOMAIN.*` (ou certains `TECH.*`).
- Adapter HTTP : mappe des erreurs techniques vers des `TECH.*`.
- Documentation : section "Contrats API" du README.

Cas alternatifs / exceptions
---------------------------
- Pas d'exception : fichier purement déclaratif.
- Si un code est modifié, cela peut casser des consumers : à faire via bump de version + tests.
"""


class ErrorCodes:
    """
    Espace de noms pour les codes d'erreur.

    Convention
    - `TECH.*` : erreurs techniques (validation, auth, rate limit, interne).
    - `DOMAIN.*` : erreurs métier stables.
    """

    class TECH:
        """Codes techniques (HTTP-level)."""

        VALIDATION_REQUIRED = "TECH.VALIDATION.REQUIRED"
        VALIDATION_INVALID = "TECH.VALIDATION.INVALID"
        VALIDATION_FORMAT = "TECH.VALIDATION.FORMAT"

        AUTH_INVALID_CREDENTIALS = "TECH.AUTH.INVALID_CREDENTIALS"
        AUTH_TOKEN_EXPIRED = "TECH.AUTH.TOKEN_EXPIRED"
        AUTH_TOKEN_INVALID = "TECH.AUTH.TOKEN_INVALID"
        AUTH_UNAUTHORIZED = "TECH.AUTH.UNAUTHORIZED"

        RATE_LIMIT_TOO_MANY_REQUESTS = "TECH.RATE_LIMIT.TOO_MANY_REQUESTS"
        CONFLICT = "TECH.CONFLICT"
        NOT_FOUND = "TECH.NOT_FOUND"
        INTERNAL = "TECH.INTERNAL"

    class DOMAIN:
        """Codes métier (domain-level)."""

        USER_ALREADY_EXISTS = "DOMAIN.USER.ALREADY_EXISTS"
        USER_INACTIVE = "DOMAIN.USER.INACTIVE"
        USER_NOT_FOUND = "DOMAIN.USER.NOT_FOUND"
