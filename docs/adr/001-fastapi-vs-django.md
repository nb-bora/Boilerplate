---
id: 001
title: FastAPI vs Django
status: accepted
date: 2026-04-20
---

## Contexte
On veut un boilerplate Python orienté API, async-first, typé, et facile à cloner/run.

## Décision
Adopter **FastAPI** (et Starlette) comme framework web.

## Alternatives considérées
- Django (+ DRF)
- Flask / Quart

## Conséquences
- Excellente DX, OpenAPI auto, perf async
- Moins “batteries included” que Django (admin/ORM opinionated à construire)

