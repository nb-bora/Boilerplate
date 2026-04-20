## Contexte

Redis est **optionnel** dans ce boilerplate.
Quand il est activé, il sert à :

- **rate limiting** (compteurs),
- **idempotency** (rejeu de réponses),
- **révocation best-effort** (blacklist `jti` access token sur logout).

Quand il est désactivé :

- rate limiting / idempotency basculent en **fallback in-memory** (utile en dev/test),
- la révocation “blacklist” est inactive (logout devient stateless).

> Important: le fallback in-memory n’est **pas distribué** (multi-instances) et n’est pas persistant.

---

## Fichiers concernés

- Configuration: `app/core/config.py` + `.env.example`
- Client Redis: `app/infrastructure/redis.py`
- Cache store: `app/adapters/cache/store.py`
- Health readiness: `app/adapters/http/v1/health.py`
- Rate limit: `app/adapters/cache/rate_limiter.py`
- Idempotency: `app/adapters/cache/idempotency.py`

---

## Étapes détaillées (local/dev)

### 1) Démarrer Redis via Docker Compose

Le service redis est déclaré avec un **profil**:

```bash
docker compose --profile redis up -d redis
```

### 2) Activer Redis dans l’environnement

Dans `.env` (ou via variables d’environnement):

- `REDIS_ENABLED=true`
- `REDIS_URL=redis://localhost:6379/0`

### 3) Lancer l’API

```bash
make dev
```

### 4) Vérifier la readiness

```bash
curl -i http://localhost:8000/api/v1/health/ready
```

Attendu :

- `200` si DB OK + Redis OK
- `503` si Redis down (quand `REDIS_ENABLED=true`)

---

## Étapes (prod)

- Utiliser une URL Redis managée (TLS si nécessaire).
- Ajuster les paramètres retry/backoff (`REDIS_RETRY_ATTEMPTS`, `REDIS_RETRY_BACKOFF_MS`).
- Vérifier la compat multi-instances (Redis requis si tu scales horizontalement pour le rate limit/idempotency).

---

## Troubleshooting

- **Ready = 503** alors que Redis est up :
  - vérifier `REDIS_URL` (host/port/db)
  - vérifier auth si Redis nécessite un mot de passe
  - vérifier réseau (Docker Desktop / firewall)

