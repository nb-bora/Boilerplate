## Workflows (référence)

Ce document décrit les workflows “nominal / alternatifs / exceptions” du boilerplate. Les mêmes
sections existent aussi en docstrings dans le code pour garder la doc près de l’implémentation.

### Démarrage (lifespan)

- **Nominal**: charge `Settings` → init DB engine → init Redis si activé → checks → app up.
- **Alternatifs**:
  - Redis désactivé : pas de check Redis.
  - Dépendance down au boot : app up, mais readiness = `503`.
- **Exceptions**: erreurs de connexion capturées/loguées, ressources fermées au shutdown.

### Healthchecks

- **Nominal**:
  - `/api/v1/health/live` = `200`
  - `/api/v1/health/ready` = `200` si DB OK (+ Redis OK si activé)
- **Alternatifs**: Redis off → readiness ne dépend que DB.
- **Exceptions**: wiring incomplet → readiness “safe” = `503`.

### Enveloppe de réponse

- **Nominal**: toutes réponses de succès/erreur doivent respecter `SuccessEnvelope`/`ErrorEnvelope`.
- **Alternatifs**: `request_id` vide uniquement si middleware non exécuté (tests bas niveau).
- **Exceptions**: erreurs non gérées → enveloppe `TECH.INTERNAL`.

### Migrations (Alembic async)

- **Nominal**: `alembic upgrade head` applique les migrations via `DATABASE_URL`.
- **Alternatifs**: `.env` absent → valeurs env/process utilisées.
- **Exceptions**: DB down/credentials invalides → Alembic échoue (comportement attendu).

