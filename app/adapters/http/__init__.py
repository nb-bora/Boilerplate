from __future__ import annotations

"""
Package Adapter HTTP.

Contenu
-------
- `v1/` : routes versionnées (`/api/v1/...`)
- `schemas/` : schémas Pydantic HTTP
- `dependencies.py` : injection (UoW, cache, user courant)
- `exception_handlers.py` : mapping exceptions → enveloppe
- `response.py` : helpers enveloppe succès/erreur
"""
