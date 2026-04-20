## Vue d’ensemble (lecture progressive)

Cette documentation décrit **la solution telle qu’implémentée dans le dépôt** `f:\Boilerplate`, en allant du
général vers le particulier : vue d’ensemble → couches → fichiers → fonctions → workflows → exceptions.

Le projet suit une **Clean Architecture** pragmatique :
- **Domain** : logique métier pure (aucune dépendance à FastAPI/SQLAlchemy/Redis)
- **Application** : use-cases (orchestration) + DTOs
- **Adapters** : HTTP / persistance / cache (intégrations techniques “bordure”)
- **Infrastructure** : implémentations concrètes (DB/Redis/bus/clock/audit)
- **Core** : transversal technique (config/logs/sécurité/middlewares/context)
- **Common** : contrats et constantes partagés (enveloppe, codes)

---

## Quick mental model

- **Une requête HTTP** entre dans FastAPI (`app/main.py`).
- Les **middlewares** ajoutent headers et logs, et établissent un contexte (`request_id`, `ip`).
- La route (adapter HTTP) valide l’entrée, applique rate limiting / idempotency si applicable,
  puis appelle un **use-case** (Application).
- Le use-case ouvre un **Unit of Work** (transaction), appelle les **repositories**, bufferise des **DomainEvents**,
  commit, puis les events sont dispatch **post-commit**.
- Des side-effects (ex: audit) sont gérés par des handlers (Infrastructure), idéalement **sans rollback**.

---

## Contrats API (invariants)

### Enveloppe de réponse uniforme

Définie dans `app/common/response_envelope.py` et construite via `app/adapters/http/response.py`.

- **Succès** : `success=true`, `errors=null`, `meta.request_id` toujours présent.
- **Erreur** : `success=false`, `data=null`, `errors[]` avec `code` stable (`TECH.*`/`DOMAIN.*`),
  `meta.request_id` toujours présent.

### Codes d’erreur stables

Centralisés dans `app/common/constants.py` et utilisés par :
- le domaine (exceptions `DomainError` avec codes `DOMAIN.*` et certains `TECH.*`),
- l’adapter HTTP (validation, 404, 429, token errors…).

### Headers de corrélation

Gérés par `app/core/middleware/request_id.py`.

- `X-Request-Id` : toujours renvoyé
- `X-Correlation-Id` : toujours renvoyé (propagé si fourni sinon aligné sur request_id)

---

## Couche 0 — Composition Root (`app/main.py`)

### Objectif

Assembler l’application FastAPI :
- settings
- lifespan (startup/shutdown)
- middlewares (ordre important)
- routers V1
- exception handlers
- wiring DB/Redis/cache/event bus/audit

### Fichier : `app/main.py`

#### `lifespan(app)`

- **Rôle** : initialisation/cleanup des ressources.
- **Nominal** :
  - charge `Settings`,
  - instancie DB engine + session factory,
  - instancie event bus local et y branche le handler d’audit,
  - instancie cache store (in-memory) et remplace par Redis si `REDIS_ENABLED=true`,
  - exécute `check_db` et `check_redis` (si activé),
  - expose `app.state.*` pour les healthchecks.
- **Alternatifs** :
  - DB down au boot : app démarre quand même, `db_ready=false` (readiness = 503).
  - Redis off : aucun client créé, readiness ne dépend pas de Redis.
  - Redis down au boot : app démarre, `redis_ready=false`.
- **Exceptions** :
  - erreurs DB/Redis capturées et loguées (WARNING),
  - cleanup best-effort au shutdown (close redis, dispose engine).

#### `create_app()`

- **Rôle** : construire l’instance FastAPI et enregistrer handlers/middlewares/routers.
- **Ordre middlewares (README)** :
  1. `SecurityHeadersMiddleware`
  2. `RequestIdMiddleware`
  3. `LoggingMiddleware`
  4. `CORSMiddleware`
- **Exceptions** :
  - settings invalides → exception au démarrage (ex: CORS wildcard en prod).

---

## Couche 1 — Core (`app/core/`)

### `app/core/config.py`

- **`Settings`** : configuration typée (env + `.env`).
  - **Nominal** : defaults DX-friendly, parsing CSV `CORS_ORIGINS` via `cors_origins_list`.
  - **Alternatifs** : `.env` absent, CSV avec espaces/valeurs vides.
  - **Exceptions** : types invalides (Pydantic), wildcard CORS en prod (`ValueError`).
- **`get_settings()`** : singleton via `lru_cache`.

### `app/core/security.py`

- **Hashing** : `hash_password`, `verify_password` (bcrypt via passlib).
- **JWT** : `create_access_token`, `create_refresh_token`, `decode_token`.
  - **Exceptions normalisées** :
    - `ValueError("TOKEN_EXPIRED")`
    - `ValueError("TOKEN_INVALID")`

### `app/core/context.py`

- **Rôle** : `contextvars` pour `request_id` et `ip` (lisibles dans la couche Application).
- **Nominal** : set par middleware request_id, get dans use-cases.
- **Alternatif** : hors requête HTTP → valeurs `None`.

### `app/core/logging.py`

- **`configure_logging`** : configure structlog JSON, fallback INFO si niveau invalide.
- **`get_logger`** : retourne un BoundLogger structlog.

### Middlewares (`app/core/middleware/`)

#### `request_id.py` — `RequestIdMiddleware`

- **Rôle** : injecter request_id/correlation_id dans `request.state`, headers, et `contextvars`.
- **Nominal** : ULID si absent, correlation alignée, headers toujours renvoyés.
- **Alternatifs** : proxy ne fournit que correlation, `request.client` absent.

#### `logging.py` — `LoggingMiddleware` + `_parse_traceparent`

- **Rôle** : log “request_finished” (JSON) avec corrélation + latence.
- **Alternatifs** : traceparent absent/invalide, request_id absent (tests très bas niveau).

#### `security_headers.py` — `SecurityHeadersMiddleware`

- **Rôle** : ajouter headers de sécurité par défaut.
- **Nominal** : `nosniff`, `DENY`, `CSP`, `Permissions-Policy`, etc.
- **Alternatif** : HSTS seulement en `preprod/prod`.

---

## Couche 2 — Common (`app/common/`)

### `app/common/response_envelope.py`

- **Rôle** : modèles Pydantic du contrat d’enveloppe.
- **Classes** : `SuccessEnvelope`, `ErrorEnvelope`, `ErrorDetail`, `EnvelopeMeta`.
- **Exception notable** : si `data` n’est pas JSON-serializable, la sérialisation peut échouer (erreur de code appelant).

### `app/common/constants.py`

- **Rôle** : codes d’erreur stables (`TECH.*`, `DOMAIN.*`).

---

## Couche 3 — Domain (`app/domain/`)

### `app/domain/base.py`

- `Entity` : id ULID + timestamps UTC.
- `DomainEvent` : event_id, occurred_at, aggregate_id, payload.

### `app/domain/users/`

- `value_objects.py` :
  - `Email` normalise (lower/strip) et valide minimalement (sinon `ValueError`).
  - `HashedPassword` encapsule un hash.
- `entity.py` :
  - `User` (email, hashed_password, roles, is_active),
  - `Role` (ADMIN/USER),
  - `has_permission` V1 minimal (admin => true, sinon false).
- `exceptions.py` :
  - `DomainError` (code + message),
  - `UserAlreadyExists`, `InvalidCredentials`, `UserNotFound`, `UserInactive`.
- `events.py` : `UserRegistered`, `UserLoggedIn`.
- `repository.py` : port `IUserRepository`.

### `app/domain/audit/`

- `entity.py` : `AuditLog` (action/resource/metadata/request_id/ip/timestamp).
- `repository.py` : port `IAuditRepository`.

### `app/domain/events/bus.py`

- port `EventBusPort.publish(event)`.

---

## Couche 4 — Application (`app/application/`)

### DTOs

- `auth/dto.py` : `RegisterInput`, `LoginInput`, `TokenOutput`.
- `users/dto.py` : `UserOutput`.

### Use-cases

#### `auth/register.py` — `RegisterUser.execute(data)`

- **Nominal** :
  - vérifie email unique,
  - crée User (Email VO + hash),
  - ajoute refresh token DB,
  - émet `UserRegistered` (avec request_id/ip),
  - commit post-commit dispatch,
  - retourne access+refresh tokens.
- **Exceptions** :
  - `UserAlreadyExists` (409 via adapter HTTP),
  - erreurs DB au commit (500 via handler global).

#### `auth/login.py` — `LoginUser.execute(data)`

- **Nominal** :
  - récupère user,
  - vérifie actif,
  - vérifie mdp,
  - ajoute refresh token DB,
  - émet `UserLoggedIn`,
  - commit,
  - retourne tokens.
- **Anti-énumération** :
  - user absent ou mdp mauvais → `InvalidCredentials` identique côté client.

#### `users/get_me.py` — `GetCurrentUser.execute(user_id)`

- **Nominal** : get user par id, retourne `UserOutput`.
- **Exception** : `UserNotFound` (404 via adapter HTTP).

---

## Couche 5 — Adapters (`app/adapters/`)

## A) Adapter HTTP (`app/adapters/http/`)

### `response.py`

- `success(request, data, message=None)` : construit `SuccessEnvelope` + `meta.request_id`.
- `error(request, message, errors, status_code=...)` : construit `ErrorEnvelope`.

### `exception_handlers.py`

- `validation_exception_handler` :
  - mappe erreurs FastAPI/Pydantic → `TECH.VALIDATION.REQUIRED|INVALID`.
- `http_exception_handler` :
  - mappe 404/401/403/409/429 → codes TECH.
- `unhandled_exception_handler` :
  - mappe `DomainError` → enveloppe + statut (401/403/404/409),
  - mappe `ValueError("TOKEN_*")` → 401 token,
  - sinon 500 `TECH.INTERNAL`.

### `dependencies.py`

- `get_db` : yield une session SQLAlchemy (si besoin).
- `get_uow` : construit un `AsyncUnitOfWork`.
- `get_cache_store` : retourne store unifié (Redis/in-memory).
- `get_current_user_id` :
  - decode JWT,
  - check blacklist `jti` si Redis activé,
  - set `request.state.user_id`.

### Routers V1 (`http/v1/*`)

#### `v1/health.py`

- `GET /api/v1/health/live` : toujours 200 enveloppé.
- `GET /api/v1/health/ready` : 200 si checks OK, sinon 503 (safe default si state incomplet).

#### `v1/auth.py`

- `POST /register`
  - rate limit,
  - idempotency (key+payload hash),
  - use-case register,
  - stocke réponse idempotency.
- `POST /login` : rate limit + use-case login.
- `POST /refresh` : refresh rotation DB (revoke old + add new).
- `POST /logout` : blacklist `jti` access token si Redis activé.

#### `v1/users.py`

- `GET /me` : auth via JWT + use-case get_me.

## B) Adapter Cache (`app/adapters/cache/`)

- `store.py`
  - `ICacheStore` port minimal,
  - `RedisCacheStore`,
  - `InMemoryCacheStore` (TTL opportuniste, non distribué).
- `rate_limiter.py`
  - `enforce_rate_limit` → 429 si limite dépassée.
- `idempotency.py`
  - calc hash payload,
  - lookup/store réponse sérialisée.

## C) Adapter Persistence (`app/adapters/persistence/`)

- `models/*` :
  - `BaseModel` (id ULID + timestamps),
  - `UserModel`, `RefreshTokenModel`, `AuditLogModel`.
- `mappers/user.py` :
  - ORM ↔ domain.
- `repositories/*` :
  - `SqlAlchemyUserRepository`,
  - `SqlAlchemyRefreshTokenRepository`,
  - `SqlAlchemyAuditRepository`.
- `unit_of_work.py` :
  - scope session,
  - rollback sur exception,
  - commit + dispatch post-commit.

---

## Couche 6 — Infrastructure (`app/infrastructure/`)

### `db.py`

- `create_engine`, `create_session_factory`, `check_db`.
- exceptions remontent (capturées au startup pour degraded mode).

### `redis.py`

- `create_redis_client`, `check_redis`, `close_redis`.

### `event_bus.py`

- `LocalEventBus` : register + publish.
- si handler lève → log error, pas d’exception remontée.

### `audit_handler.py`

- `make_audit_handler(session_factory)`
  - retourne un handler sync,
  - planifie une tâche async qui écrit `AuditLog` en DB.

---

## Migrations Alembic (`alembic/`)

### `alembic/env.py`

- exécution async online/offline depuis `DATABASE_URL`.

### `versions/0001_initial.py`

- `users` + index unique email.

### `versions/0002_auth_audit.py`

- ajoute `roles`, `is_active`,
- crée `refresh_tokens`, `audit_logs`.

---

## Tests (`tests/`)

### `tests/conftest.py`

- `app` : FastAPI avec lifespan actif (via `asgi-lifespan`).
- `contract_app` : override `get_uow` avec un fake UoW pour éviter DB dans tests de contrat.

### `tests/test_health.py`

- smoke/contract minimal : enveloppe + headers + 404 enveloppée.

### `tests/contract/*`

- `test_envelope.py` : envelope contract
- `test_headers.py` : headers contract
- `test_rate_limit.py` : 429 + code TECH attendu
- `test_idempotency.py` : conflit idempotency possible → 409 TECH.CONFLICT

---

## CI & Docker

- `.github/workflows/ci.yml` :
  - `ruff check`
  - `ruff format --check`
  - `pytest`
- `.github/workflows/docker.yml` :
  - build image sur tags `v*.*.*`

---

## Notes de vérité terrain (exécution locale)

- Les tests actuels sont conçus pour **passer sans DB** (contrat), grâce à `contract_app`.
- Pour valider `alembic upgrade head` et la persistance end-to-end, il faut une DB up (Docker).
