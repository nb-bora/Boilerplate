---
id: 007
title: JWT HS256 + refresh tokens
status: accepted
date: 2026-04-20
---

## Contexte
Auth simple en service unique, avec rotation via refresh token.

## Décision
- JWT **HS256** pour access/refresh
- Refresh tokens persistés en DB (`refresh_tokens`) via `jti`
- Révocation/blacklist via Redis optionnel

## Alternatives considérées
- RS256 (plus adapté multi-services)
- Sessions server-side

## Conséquences
- Simple à déployer, peu de moving parts
- En multi-service, migration possible vers RS256/IdP

