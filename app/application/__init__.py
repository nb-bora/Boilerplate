from __future__ import annotations

"""
Package `app.application`.

Rôle
----
La couche Application orchestre les cas d'usage (use-cases) du domaine.
Elle ne contient pas de logique HTTP/DB/Redis : elle travaille via des ports (ex: repositories)
fournis par les adapters.

Objectifs
---------
- Encapsuler les workflows métier sous forme d'objets invocables (use-cases).
- Définir des DTOs d'entrée/sortie (interfaces applicatives) stables.

Intervient dans
--------------
- Adapters HTTP : `app/adapters/http/v1/*` appellent les use-cases.
- Adapters Persistence : `AsyncUnitOfWork` fournit les repos utilisés par les use-cases.
"""
