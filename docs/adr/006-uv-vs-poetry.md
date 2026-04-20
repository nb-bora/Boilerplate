---
id: 006
title: uv vs Poetry
status: accepted
date: 2026-04-20
---

## Contexte
Installer vite et de manière déterministe.

## Décision
Recommander **uv** (avec `pyproject.toml`) ; fallback `pip -r requirements*.txt`.

## Alternatives considérées
- Poetry
- Pipenv

## Conséquences
- DX très rapide avec uv
- Fallback simple pour environnements sans uv

