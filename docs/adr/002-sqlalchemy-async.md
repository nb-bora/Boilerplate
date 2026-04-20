---
id: 002
title: SQLAlchemy async 2.x
status: accepted
date: 2026-04-20
---

## Contexte
Besoin d’un ORM mature, standard, compatible async, et supportant Alembic.

## Décision
Utiliser **SQLAlchemy 2.x async** + **asyncpg** + **Alembic**.

## Alternatives considérées
- Tortoise ORM
- SQLModel (surcouche)

## Conséquences
- Contrôle fin, écosystème standard
- Discipline nécessaire (scope session, éviter lazy loading implicite)

