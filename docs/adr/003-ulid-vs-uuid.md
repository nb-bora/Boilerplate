---
id: 003
title: ULID vs UUID
status: accepted
date: 2026-04-20
---

## Contexte
IDs stables, URL-safe, et triables pour logs et DB.

## Décision
Adopter **ULID** (26 chars) pour `id`, `request_id`, `jti`.

## Alternatives considérées
- UUIDv4
- UUIDv7

## Conséquences
- IDs triables, lisibles, bons pour corrélation
- Nécessite une lib ULID et des colonnes `String(26)`

