from __future__ import annotations

"""
Package Adapter Persistence.

Rôle
----
Implémentations concrètes des ports de persistance (repos) via SQLAlchemy async, ainsi que :
- models ORM,
- mappers ORM↔domain,
- unit of work (transactions + events post-commit).
"""