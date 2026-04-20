---
id: 005
title: Soft delete optionnel
status: accepted
date: 2026-04-20
---

## Contexte
Le soft delete impacte toutes les requêtes, l’unicité, et les perfs.

## Décision
Soft delete **désactivé par défaut** (`SOFT_DELETE_ENABLED=false`).

## Alternatives considérées
- Soft delete par défaut
- Hard delete only

## Conséquences
- Moins de complexité par défaut
- Si activé, nécessite filtres globaux et index partiels (PostgreSQL)

