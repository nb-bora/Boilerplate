## Contexte
Activer Redis pour rate limiting, idempotency et révocation.

## Étapes
1. Mettre `REDIS_ENABLED=true`
2. Configurer `REDIS_URL`
3. Démarrer le service redis : `docker compose --profile redis up -d redis`
4. Vérifier `/api/v1/health/ready`

## Notes
Sans Redis, le boilerplate utilise un fallback in-memory (utile dev/test, non distribué).

