---
id: 004
title: Redis optionnel
status: accepted
date: 2026-04-20
---

## Contexte
Redis est utile (rate limiting, idempotency, blacklist), mais tout projet n’en a pas besoin.

## Décision
Redis est **désactivé par défaut** (`REDIS_ENABLED=false`) avec fallback **in-memory** pour dev/test.

## Alternatives considérées
- Redis obligatoire
- Pas de Redis du tout

## Conséquences
- Onboarding simple
- Certains comportements “distribués” ne sont exacts qu’avec Redis activé

