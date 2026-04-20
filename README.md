# FastAPI Boilerplate OSS

> **Vision** : Un boilerplate open-source, gratuit, clonable en 5 minutes, adapté à n'importe quel type de projet, évolutif à n'importe quel horizon — de la SaaS solo au microservice d'équipe.

---

## Quickstart (< 5 minutes)

### Prérequis

- **Python** : 3.12+
- **uv** : installé (recommandé)
- **Docker** : requis pour la DB (et Redis si activé)
- **make** :
  - Sur Linux/macOS : présent par défaut
  - Sur Windows : installe `make` (ex: via Chocolatey/Git Bash) ou utilise les commandes équivalentes ci-dessous

### Lancer en dev (DB incluse)

1. Cloner et préparer l'environnement :

```bash
git clone <URL_DU_REPO> fastapi-boilerplate
cd fastapi-boilerplate
cp .env.example .env
```

1. Démarrer la DB et l’API :

```bash
docker compose up -d db
uv sync
alembic upgrade head
fastapi dev app/main.py --host 0.0.0.0 --port 8000
```

### Vérifier que “ça marche”

- **Health live** :

```bash
curl -i http://localhost:8000/api/v1/health/live
```

- **Health ready** (vérifie DB, et Redis si activé) :

```bash
curl -i http://localhost:8000/api/v1/health/ready
```

Tu dois voir un `**200 OK**` et une réponse au format enveloppe (section [Contrats API](#5-contrats-api)).

### (Option) Lancer via Docker Compose

```bash
docker compose up --build
```

---

## Table des matières

1. [Vision & positionnement](#1-vision--positionnement)
2. [Principes non négociables](#2-principes-non-négociables)
3. [Choix techniques V1](#3-choix-techniques-v1)
4. [Arborescence cible](#4-arborescence-cible)
5. [Contrats API](#5-contrats-api)
6. [Phase 1 — Fondations & identité OSS](#6-phase-1--fondations--identité-oss)
7. [Phase 2 — Ossature Clean Architecture](#7-phase-2--ossature-clean-architecture)
8. [Phase 3 — Base de données & persistance](#8-phase-3--base-de-données--persistance)
9. [Phase 4 — Redis, Auth & Sécurité](#9-phase-4--redis-auth--sécurité)
10. [Phase 5 — Tests, CI/CD & Docker](#10-phase-5--tests-cicd--docker)
11. [Phase 6 — Documentation & évolutivité](#11-phase-6--documentation--évolutivité)
12. [Variables d'environnement](#12-variables-denvironnement)
13. [Roadmap V2](#13-roadmap-v2)
14. [Ordre d'implémentation](#14-ordre-dimplémentation)

---

## 1. Vision & positionnement

### Personas cibles


| Persona                 | Profil                               | Usage attendu                                 |
| ----------------------- | ------------------------------------ | --------------------------------------------- |
| **Solo / indie**        | Dev seul, SaaS, side-project         | Clone, adapte, ship vite                      |
| **Startup (3–5 devs)**  | Équipe petite, besoin de conventions | Base commune, onboarding rapide               |
| **Senior / architecte** | Référence et point de départ         | Comprend les trade-offs, adapte en profondeur |


### Niveaux de complexité exposés

- **Core** : ce qui tourne dès le clone (FastAPI, Postgres, Auth, healthchecks, tests)
- **Optionnel** : Redis, soft delete, mypy, refresh token — activables par config
- **Avancé** : RBAC complet, OTel, bus async, queues — documentés mais hors V1

### Test ultime d'accessibilité

> Si `git clone` + `make dev` prend plus de 5 minutes, c'est un bug de documentation ou de DX. Pas une feature manquante.

### Démo

- **Démo en ligne** : à ajouter (ex: `https://...`)
- **Repo exemple** : à ajouter (ex: “todo app” ou “mini SaaS” basé sur ce boilerplate)

---

## 2. Principes non négociables

### Optionnel par défaut

Redis, soft delete, mypy, refresh token : **désactivés par défaut**, activables par variable d'environnement ou flag. Un projet qui n'a pas besoin de Redis ne devrait pas avoir à le désinstaller.

### Interface avant implémentation

Chaque dépendance externe (DB, cache, mail, événements) est derrière un **port (interface)** défini dans `domain/`. L'implémentation concrète vit dans `adapters/` ou `infrastructure/`. Swapper PostgreSQL pour SQLite en test ne touche pas le domaine.

### OTel-ready dès V1

Pas d'OpenTelemetry complet en V1, mais :

- `request_id` au format **W3C Trace Context** (`trace-id` + `span-id`)
- Champs `trace_id` / `span_id` présents dans les logs structurés si fournis
- Middleware de tracing conçu comme point d'extension documenté

Objectif : la migration vers OTel en V2 ne casse ni les logs, ni les dashboards, ni la corrélation.

### Décisions documentées (ADR)

Chaque choix structurant a son **Architecture Decision Record** dans `docs/adr/`, avec contexte, alternatives considérées, et trade-offs explicites. Les utilisateurs comprennent *pourquoi*, pas juste *quoi*.

### Clone & run en 5 minutes

La commande `make dev` (ou `docker compose up`) doit suffire à avoir un service fonctionnel avec DB, migrations, seed, et tous les healthchecks verts.

---

## 3. Choix techniques V1


| Composant          | Choix                            | Justification                                              |
| ------------------ | -------------------------------- | ---------------------------------------------------------- |
| Framework          | **FastAPI** + Uvicorn            | Async natif, typage Pydantic, DX excellente, standard 2026 |
| CLI dev/prod       | `fastapi dev` / `fastapi run`    | Intégré FastAPI CLI, hot-reload, zero config               |
| Base de données    | **PostgreSQL**                   | Robuste, UUID/JSONB natif, standard prod                   |
| ORM                | **SQLAlchemy async 2.x**         | Async natif, cohérent avec FastAPI, performant             |
| Migrations         | **Alembic**                      | Standard Python, intégration SQLAlchemy parfaite           |
| Cache / rate limit | **Redis** (optionnel)            | Fallback in-memory en dev, activé par `REDIS_ENABLED=true` |
| Packaging          | **uv** + `pyproject.toml`        | Ultra-rapide, lock déterministe, standard 2026             |
| Lint / format      | **ruff**                         | Remplace flake8 + isort + black, 10–100x plus rapide       |
| Typage             | **mypy** (optionnel)             | Activé par flag CI, pas bloquant par défaut                |
| Tests              | **pytest** + **Testcontainers**  | Isolation parfaite, CI sans docker-compose externe         |
| IDs                | **ULID**                         | Sortable, URL-safe, meilleur que UUID séquentiel           |
| Temps              | **Clock abstraction**            | `Clock.now()` injectable, tests déterministes              |
| CI                 | **GitHub Actions**               | Standard OSS, gratuit, intégration native                  |
| Conteneurs         | **Docker multi-stage** + compose | Build optimisé, profils env, healthchecks                  |
| Licence            | **MIT**                          | Simple, très adoptée, aucune friction                      |


### ADR à créer

```
docs/adr/
├── 001-fastapi-vs-django.md
├── 002-sqlalchemy-async.md
├── 003-ulid-vs-uuid.md
├── 004-redis-optional.md
├── 005-soft-delete-optional.md
├── 006-uv-vs-poetry.md
└── 007-jwt-hs256-refresh.md
```

---

## 4. Arborescence cible

```
./
├── app/
│   ├── main.py                         # Composition root FastAPI
│   ├── core/
│   │   ├── config.py                   # Settings typées (Pydantic BaseSettings)
│   │   ├── logging.py                  # Logs structurés (JSON)
│   │   ├── security.py                 # Hashing + JWT helpers
│   │   ├── middleware/
│   │   │   ├── request_id.py           # Middleware request_id / correlation_id
│   │   │   └── security_headers.py     # X-Content-Type-Options, CSP, etc.
│   │   └── exceptions.py              # Exceptions techniques partagées
│   │
│   ├── domain/
│   │   ├── base.py                     # Entity(id: ULID), ValueObject, DomainEvent
│   │   ├── clock.py                    # Port Clock (interface)
│   │   ├── events/
│   │   │   └── bus.py                  # Interface EventBus (port)
│   │   ├── users/
│   │   │   ├── entity.py               # User entity + invariants
│   │   │   ├── value_objects.py        # Email, HashedPassword
│   │   │   ├── exceptions.py           # UserAlreadyExists, InvalidCredentials, etc.
│   │   │   ├── events.py               # UserRegistered, UserLoggedIn
│   │   │   └── repository.py           # Port IUserRepository (interface)
│   │   └── audit/
│   │       ├── entity.py               # AuditLog entity
│   │       └── repository.py           # Port IAuditRepository (interface)
│   │
│   ├── application/
│   │   ├── auth/
│   │   │   ├── register.py             # UseCase RegisterUser
│   │   │   ├── login.py                # UseCase LoginUser
│   │   │   └── dto.py                  # RegisterInput, LoginInput, TokenOutput
│   │   └── users/
│   │       ├── get_me.py               # UseCase GetCurrentUser
│   │       └── dto.py                  # UserOutput
│   │
│   ├── adapters/
│   │   ├── http/
│   │   │   ├── v1/
│   │   │   │   ├── router.py           # Router /api/v1
│   │   │   │   ├── auth.py             # Routes /auth/register, /auth/login
│   │   │   │   ├── users.py            # Routes /users/me
│   │   │   │   └── health.py           # Routes /api/v1/health/live, /api/v1/health/ready
│   │   │   ├── schemas/
│   │   │   │   ├── auth.py             # Schémas Pydantic request/response
│   │   │   │   └── users.py
│   │   │   ├── dependencies.py         # get_current_user, get_db, get_redis
│   │   │   ├── exception_handlers.py   # Mapping DomainException → HTTP + enveloppe
│   │   │   └── response.py             # Helpers enveloppe succès/erreur
│   │   ├── persistence/
│   │   │   ├── models/
│   │   │   │   ├── base.py             # Base ORM (id, created_at, updated_at)
│   │   │   │   ├── user.py             # Modèle ORM UserModel
│   │   │   │   └── audit_log.py        # Modèle ORM AuditLogModel
│   │   │   ├── repositories/
│   │   │   │   ├── user.py             # Impl SQLAlchemy IUserRepository
│   │   │   │   └── audit_log.py        # Impl SQLAlchemy IAuditRepository
│   │   │   ├── mappers/
│   │   │   │   └── user.py             # ORM ↔ Domain entity
│   │   │   └── unit_of_work.py         # AsyncUnitOfWork (transaction handling)
│   │   └── cache/
│   │       ├── rate_limiter.py         # Impl Redis + fallback in-memory
│   │       └── idempotency.py          # Impl Redis idempotency store
│   │
│   ├── infrastructure/
│   │   ├── db.py                       # Engine + AsyncSession factory + lifespan
│   │   ├── redis.py                    # Client Redis + lifespan (optionnel)
│   │   ├── clock.py                    # Impl SystemClock
│   │   └── event_bus.py               # Impl bus local sync (post-commit)
│   │
│   └── common/
│       ├── pagination.py               # PaginationParams + PaginatedResponse
│       ├── response_envelope.py        # SuccessEnvelope, ErrorEnvelope, ErrorDetail
│       └── constants.py               # Codes TECH.* / DOMAIN.*
│
├── alembic/
│   ├── env.py                          # Config async (documentée)
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial.py             # Migration initiale (users + audit_logs)
│
├── tests/
│   ├── conftest.py                     # Fixtures globales, Testcontainers setup
│   ├── unit/
│   │   ├── domain/
│   │   │   ├── test_user_entity.py
│   │   │   └── test_email_value_object.py
│   │   └── application/
│   │       ├── test_register_usecase.py
│   │       └── test_login_usecase.py
│   ├── integration/
│   │   ├── test_health.py
│   │   ├── test_auth.py
│   │   └── test_users.py
│   └── contract/
│       ├── test_response_envelope.py   # Enveloppe conforme sur toutes les routes
│       ├── test_error_codes.py         # Codes TECH./DOMAIN. présents et stables
│       └── test_headers.py             # X-Request-Id toujours présent
│
├── scripts/
│   └── seeds/
│       └── v1/
│           ├── dev.py                  # Seed dev (admin user, données pagination)
│           └── test.py                 # Seed test (fixtures minimales)
│
├── docs/
│   ├── adr/                            # Architecture Decision Records
│   ├── guides/
│   │   ├── add-entity.md
│   │   ├── add-endpoint.md
│   │   ├── add-migration.md
│   │   ├── add-error-code.md
│   │   └── enable-redis.md
│   └── architecture.md                 # Diagramme Clean Architecture
│
├── .github/
│   └── workflows/
│       ├── ci.yml                      # lint + mypy + pytest + audit + trivy
│       └── docker.yml                  # Build multi-arch (amd64 + arm64)
│
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
├── Makefile
├── Dockerfile
├── docker-compose.yml
├── docker-compose.override.yml
├── README.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
├── SECURITY.md
└── LICENSE
```

---

## 5. Contrats API

### Enveloppe de réponse (uniforme, toutes routes)

**Succès :**

```json
{
  "success": true,
  "data": {},
  "message": null,
  "errors": null,
  "meta": {
    "request_id": "01HX..."
  }
}
```

**Succès paginé :**

```json
{
  "success": true,
  "data": {
    "items": [],
    "total": 0
  },
  "message": null,
  "errors": null,
  "meta": {
    "limit": 20,
    "offset": 0,
    "has_next": false,
    "request_id": "01HX..."
  }
}
```

**Erreur :**

```json
{
  "success": false,
  "data": null,
  "message": "Validation error",
  "errors": [
    {
      "code": "TECH.VALIDATION.REQUIRED",
      "message": "Field required",
      "field": "email"
    }
  ],
  "meta": {
    "request_id": "01HX..."
  }
}
```

### Hiérarchie des codes d'erreur

#### Codes techniques (`TECH.*`)


| Code                                | HTTP | Description                       |
| ----------------------------------- | ---- | --------------------------------- |
| `TECH.VALIDATION.REQUIRED`          | 422  | Champ obligatoire absent          |
| `TECH.VALIDATION.INVALID`           | 422  | Valeur invalide                   |
| `TECH.VALIDATION.FORMAT`            | 422  | Format incorrect (email, UUID...) |
| `TECH.AUTH.INVALID_CREDENTIALS`     | 401  | Identifiants incorrects           |
| `TECH.AUTH.TOKEN_EXPIRED`           | 401  | JWT expiré                        |
| `TECH.AUTH.TOKEN_INVALID`           | 401  | JWT invalide ou révoqué           |
| `TECH.AUTH.UNAUTHORIZED`            | 403  | Permissions insuffisantes         |
| `TECH.RATE_LIMIT.TOO_MANY_REQUESTS` | 429  | Trop de requêtes                  |
| `TECH.CONFLICT`                     | 409  | Conflit (ex: idempotency key)     |
| `TECH.NOT_FOUND`                    | 404  | Ressource introuvable             |
| `TECH.INTERNAL`                     | 500  | Erreur serveur inattendue         |


#### Codes métier (`DOMAIN.*`)


| Code                         | HTTP | Description             |
| ---------------------------- | ---- | ----------------------- |
| `DOMAIN.USER.ALREADY_EXISTS` | 409  | Email déjà enregistré   |
| `DOMAIN.USER.INACTIVE`       | 403  | Compte désactivé        |
| `DOMAIN.USER.NOT_FOUND`      | 404  | Utilisateur introuvable |


> **Règle** : les exceptions métier (`domain/`) portent leur code. L'adapter HTTP (`adapters/http/`) mappe vers le statut HTTP et l'enveloppe d'erreur. La logique métier ne connaît pas HTTP.

### Headers de traçage


| Header             | Direction           | Description                                              |
| ------------------ | ------------------- | -------------------------------------------------------- |
| `X-Correlation-Id` | Entrant (optionnel) | ID fourni par le client, propagé tel quel                |
| `X-Request-Id`     | Sortant (toujours)  | ULID généré par le serveur si absent                     |
| `X-Correlation-Id` | Sortant             | Renvoyé tel quel, ou aligné sur `X-Request-Id` si absent |


### Idempotency

- **Header entrant** (optionnel) : `Idempotency-Key`
- **Stockage** : Redis (TTL configurable via `IDEMPOTENCY_TTL_SECONDS`)
- **Hash** : SHA-256 du corps + `Content-Type` + `Authorization` si présent
- **Stocké** : `status_code` + `response_headers` + `response_body`
- **Conflit** (même clé, payload différent) : `409 TECH.CONFLICT`
- **Routes V1** : `POST /api/v1/auth/register`

### Security headers (middleware)

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'
Permissions-Policy: geolocation=(), microphone=(), camera=()
Strict-Transport-Security: max-age=63072000 (preprod/prod uniquement)
```

---

## Exemples API (curl) — V1

> Les exemples utilisent l’URL locale du Quickstart. Adapte si tu exposes l’API derrière un reverse proxy.

### Inscription — `POST /api/v1/auth/register`

```bash
curl -i -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: 01HX9MFBQ3NDXK7BPTHZ4B5FGS" \
  -d '{"email":"test@example.com","password":"secure123"}'
```

### Connexion — `POST /api/v1/auth/login`

```bash
curl -i -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"secure123"}'
```

### Profil courant — `GET /api/v1/users/me`

```bash
curl -i http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

## 6. Phase 1 — Fondations & identité OSS

### Objectif

Poser les bases du projet OSS : identité, outils, et conventions. Livrable : un repo clonable avec `make help` fonctionnel.

### Fichiers OSS

```
LICENSE                  # MIT
README.md                # Voir Phase 6 pour le contenu complet
CONTRIBUTING.md          # Fork, branch, PR, conventions de commit
CODE_OF_CONDUCT.md       # Contributor Covenant
CHANGELOG.md             # Format Keep a Changelog + SemVer
SECURITY.md              # Comment reporter une vulnérabilité
```

### ADR initiaux

Créer les 7 ADR listés en section 3, avec pour chacun :

- **Contexte** : quel problème on résout
- **Décision** : ce qu'on a choisi
- **Alternatives** : ce qu'on a écarté et pourquoi
- **Conséquences** : trade-offs acceptés

### Tooling projet

`**pyproject.toml`** — dépendances structurées :

```toml
[project]
name = "fastapi-boilerplate"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi[standard]>=0.115",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29",            # Driver async PostgreSQL
    "alembic>=1.13",
    "pydantic-settings>=2.0",
    "python-ulid>=2.0",
    "python-jose[cryptography]>=3.3",
    "passlib[bcrypt]>=1.7",
    "structlog>=24.0",
]

[dependency-groups]
dev = [
    "ruff>=0.4",
    "mypy>=1.10",
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "httpx>=0.27",
    "testcontainers[postgres,redis]>=4.0",
    "faker>=25.0",
]
```

`**Makefile**` — cibles principales :

```makefile
.PHONY: help dev test lint format audit

help:           ## Affiche les commandes disponibles
dev:            ## Lance le serveur en mode dev (hot-reload)
test-unit:      ## Tests unitaires (sans DB)
test-int:       ## Tests d'intégration (Testcontainers)
test:           ## Tous les tests + coverage
lint:           ## Ruff lint
format:         ## Ruff format
audit:          ## pip-audit (vulnérabilités deps)
migrate:        ## Alembic upgrade head
seed:           ## Lance les seeds dev
```

`**.env.example**` — exhaustif, commenté, voir section [Variables d'environnement](#12-variables-denvironnement).

`**.gitignore**` — inclure : `.env`, `__pycache__`, `.mypy_cache`, `.ruff_cache`, `.pytest_cache`, `*.pyc`, `dist/`, `.venv/`.

---

## 7. Phase 2 — Ossature Clean Architecture

### Objectif

Mettre en place la structure complète, le router `/api/v1`, les middlewares essentiels, et l'enveloppe de réponse. Livrable : `GET /api/v1/health/live` et `GET /api/v1/health/ready` fonctionnels avec logs structurés.

### `app/main.py` — composition root

```python
# Responsabilités :
# - Créer l'instance FastAPI
# - Inclure les routers
# - Enregistrer les middlewares (ordre important)
# - Enregistrer les exception_handlers
# - Gérer le lifespan (DB + Redis)
```

Ordre des middlewares (du plus externe au plus interne) :

1. `SecurityHeadersMiddleware`
2. `RequestIdMiddleware` (injecte `X-Request-Id` + `X-Correlation-Id`)
3. `LoggingMiddleware` (log structuré début/fin requête)
4. `CORSMiddleware`

### Healthchecks

`**GET /api/v1/health/live**` — répond `200 OK` si le process est vivant (pas de vérification DB).

`**GET /api/v1/health/ready**` — répond `200 OK` si :

- Connexion DB active (requête `SELECT 1`)
- Connexion Redis active si `REDIS_ENABLED=true`

Réponse `503 Service Unavailable` si l'un des checks échoue.

### Domain model — bases

```python
# app/domain/base.py

class Entity:
    id: ULID
    created_at: datetime
    updated_at: datetime

class ValueObject:
    # Immutable, égalité par valeur

class DomainEvent:
    event_id: ULID
    occurred_at: datetime
    aggregate_id: ULID
```

### Bus d'événements local — spécification critique

```python
# app/infrastructure/event_bus.py

class LocalEventBus:
    """
    Bus synchrone, dispatch POST-COMMIT uniquement.

    Règles :
    - Les événements sont collectés pendant la transaction
    - Le dispatch se fait APRÈS le commit, jamais pendant
    - Si un handler lève une exception : log ERROR + métrique future
      → PAS de rollback de la transaction principale
    - Interface identique à EventBusPort pour migration V2 (Celery, etc.)
    """
```

> **Pourquoi post-commit ?** Si le dispatch est dans la transaction et qu'un handler plante, on rollback une opération métier réussie. Post-commit découple les side-effects de la transaction principale et facilite la migration vers un bus async.

### Observabilité V1

`**request_id`** : ULID (ex: `01HX9MFBQ3NDXK7BPTHZ4B5FGS`). Compatible W3C Trace Context : si un `traceparent` header est présent, extraire `trace-id` et `span-id` dans le contexte de log.

**Logs structurés** — champs minimaux par requête :

```json
{
  "timestamp": "2026-01-15T10:30:00.123Z",
  "level": "info",
  "event": "request_finished",
  "request_id": "01HX...",
  "correlation_id": "01HX...",
  "user_id": "01HX..." ,
  "method": "POST",
  "path": "/api/v1/auth/login",
  "status_code": 200,
  "duration_ms": 45,
  "trace_id": null,
  "span_id": null
}
```

**Extension OTel documentée** : `docs/guides/enable-opentelemetry.md` — comment brancher `opentelemetry-sdk` sur le middleware existant sans modifier le domaine.

---

## 8. Phase 3 — Base de données & persistance

### Objectif

SQLAlchemy async bien configuré, migrations Alembic fonctionnelles, base repository générique. Livrable : migration initiale jouable, User persistable.

### Guide pièges async SQLAlchemy 2.x (obligatoire en doc)

Points à documenter explicitement :

1. **Lazy loading interdit** : tout `relationship()` doit être `lazy="raise"` par défaut, et chargé explicitement (`selectinload`, `joinedload`).
2. **Session scope** : une session par requête HTTP, fermée en fin de requête. Jamais de session globale.
3. `**AsyncSession` ≠ `Session`** : pas de `session.execute()` synchrone dans du code async.
4. **Alembic env.py async** : nécessite `run_async_migrations()` avec `AsyncEngine`. Documenté dans `alembic/env.py`.

### Unit of Work async

```python
# app/adapters/persistence/unit_of_work.py

class AsyncUnitOfWork:
    """
    Gère une transaction par use-case/commande.

    Usage :
        async with uow:
            user = await uow.users.get(user_id)
            user.activate()
            await uow.commit()
            # Les domain events sont dispatchés ici, post-commit
    """
    users: IUserRepository
    audit_logs: IAuditRepository

    async def __aenter__(self): ...
    async def __aexit__(self, *args): ...  # rollback si exception
    async def commit(self): ...            # commit + dispatch events
```

### Base model ORM

```python
# app/adapters/persistence/models/base.py

class BaseModel(Base):
    __abstract__ = True

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=lambda: str(ulid()))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
```

### Soft delete — pattern optionnel

> **Décision (ADR 005)** : le soft delete N'EST PAS activé par défaut. C'est un pattern avec des implications lourdes sur toutes les requêtes, les contraintes d'unicité, et les performances à long terme.

Si activé (`SOFT_DELETE_ENABLED=true`) :

- Ajout de `deleted_at: Optional[datetime]` sur les modèles concernés
- Filtre global `WHERE deleted_at IS NULL` dans le base repository
- Gestion de l'unicité (ex: email d'un user soft-deleted) via index partiel PostgreSQL :
  ```sql
  CREATE UNIQUE INDEX users_email_active_unique
  ON users (email)
  WHERE deleted_at IS NULL;
  ```

### Base repository générique

```python
# app/adapters/persistence/repositories/base.py

class BaseRepository(Generic[T, ID]):
    async def get(self, id: ID) -> Optional[T]: ...
    async def get_or_raise(self, id: ID) -> T: ...
    async def save(self, entity: T) -> T: ...
    async def delete(self, id: ID) -> None: ...
    async def list(self, params: PaginationParams) -> PaginatedResult[T]: ...
```

---

## 9. Phase 4 — Redis, Auth & Sécurité

### Objectif

Auth JWT complète avec refresh token, rate limiting, idempotency. Livrable : register + login + /users/me fonctionnels avec tous les contrôles de sécurité.

### Redis — architecture optionnelle

```python
# Pattern : interface unique, deux implémentations

class ICacheStore(Protocol):
    async def get(self, key: str) -> Optional[str]: ...
    async def set(self, key: str, value: str, ttl: int) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def incr(self, key: str, ttl: int) -> int: ...

class RedisCacheStore(ICacheStore): ...       # Utilisé si REDIS_ENABLED=true
class InMemoryCacheStore(ICacheStore): ...    # Fallback dev/test
```

### Auth JWT — spécification complète

**Access token** :

- Algorithme : HS256 (documenté dans ADR 007 — RS256 pour V2 multi-service)
- Durée : `ACCESS_TOKEN_EXPIRE_MINUTES` (défaut : 30)
- Claims : `sub` (user_id), `iat`, `exp`, `jti` (ULID unique, pour révocation)
- Type : `Bearer` dans header `Authorization`

**Refresh token** :

- Durée : `REFRESH_TOKEN_EXPIRE_DAYS` (défaut : 7)
- Stocké en DB (table `refresh_tokens`) : `jti`, `user_id`, `expires_at`, `revoked_at`
- Rotation automatique à chaque refresh (old token révoqué, nouveau émis)

**Révocation** (si Redis activé) :

- Blacklist Redis : `blacklist:jti:{jti}` avec TTL = durée restante du token
- Vérification à chaque requête authentifiée

**Endpoints** :


| Méthode | Route                   | Auth          | Description                         |
| ------- | ----------------------- | ------------- | ----------------------------------- |
| `POST`  | `/api/v1/auth/register` | Non           | Inscription                         |
| `POST`  | `/api/v1/auth/login`    | Non           | Connexion (access + refresh tokens) |
| `POST`  | `/api/v1/auth/refresh`  | Refresh token | Renouvellement access token         |
| `POST`  | `/api/v1/auth/logout`   | Bearer        | Révocation access + refresh         |
| `GET`   | `/api/v1/users/me`      | Bearer        | Profil utilisateur courant          |


### RBAC minimal extensible

```python
# app/domain/users/entity.py

class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"

class User(Entity):
    roles: list[Role]

    def has_permission(self, permission: str) -> bool:
        # V1 : rôles simples
        # V2 : permissions granulaires (Resource × Action)
        ...
```

### Sécurité renforcée

**Anti-énumération** : les réponses de `login` doivent être indiscernables entre "email inconnu" et "mauvais mot de passe". Même message d'erreur, même code `TECH.AUTH.INVALID_CREDENTIALS`, même temps de réponse (constant-time comparison).

**CORS — vérification au démarrage** :

```python
# app/core/config.py
@model_validator(mode="after")
def validate_cors(self):
    if self.APP_ENV == "prod" and "*" in self.CORS_ORIGINS:
        raise ValueError("CORS wildcard interdit en production")
    return self
```

### CORS_ORIGINS — format attendu

- **Format** : liste d’origins séparées par des virgules (CSV)
- **Exemple dev** : `CORS_ORIGINS=http://localhost:3000,http://localhost:5173`
- **Exemple prod** : `CORS_ORIGINS=https://app.example.com,https://admin.example.com`

**Rate limiting** :


| Route                 | Limite                                      | Fenêtre  |
| --------------------- | ------------------------------------------- | -------- |
| `POST /auth/login`    | `RATE_LIMIT_LOGIN_PER_MINUTE` (défaut: 5)   | 1 minute |
| `POST /auth/register` | `RATE_LIMIT_REGISTER_PER_HOUR` (défaut: 10) | 1 heure  |


Clé de rate limit : `ratelimit:{route}:{ip}` (ou `{user_id}` si authentifié).

### Domain Events V1

**Événements émis** :


| Événement        | Emis par                | Handler                          |
| ---------------- | ----------------------- | -------------------------------- |
| `UserRegistered` | `RegisterUser` use-case | `AuditHandler` → crée `AuditLog` |
| `UserLoggedIn`   | `LoginUser` use-case    | `AuditHandler` → crée `AuditLog` |


**Modèle AuditLog** :

```python
class AuditLog(Entity):
    user_id: Optional[ULID]
    action: str          # ex: "user.registered", "user.logged_in"
    resource: str        # ex: "user"
    resource_id: ULID
    metadata: dict       # données contextuelles JSON
    request_id: ULID
    ip_address: Optional[str]
    timestamp: datetime
```

---

## 10. Phase 5 — Tests, CI/CD & Docker

### Objectif

Infrastructure de tests fiable, CI complète, Docker prêt pour prod. Livrable : `make test` passe entièrement en CI sans dépendance externe.

### Stratégie de tests

#### Pyramide

```
          /\
         /  \  Tests de contrat (5%)
        /----\
       /      \  Tests d'intégration (25%)
      /--------\
     /          \  Tests unitaires (70%)
    /____________\
```

#### Tests unitaires (`tests/unit/`)

- **Scope** : `domain/` + `application/`
- **Pas de DB**, pas de Redis, pas de FastAPI
- **Ports mockés** via `unittest.mock` ou fixtures Pytest
- **Coverage cible** : ≥ 80% sur `domain/` et `application/`

```python
# Exemple : tests/unit/application/test_register_usecase.py

async def test_register_user_success(mock_user_repo, mock_event_bus, system_clock):
    usecase = RegisterUser(repo=mock_user_repo, bus=mock_event_bus, clock=system_clock)
    result = await usecase.execute(RegisterInput(email="test@example.com", password="secure123"))
    assert result.user_id is not None
    mock_event_bus.publish.assert_called_once_with(UserRegistered(...))
```

#### Tests d'intégration (`tests/integration/`)

- **Testcontainers** : Postgres + Redis démarrés par Pytest, pas de docker-compose externe
- **Isolation** : rollback après chaque test (transaction wrappée)
- **Client HTTP** : `httpx.AsyncClient` avec l'app FastAPI en mode test

```python
# tests/conftest.py

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16") as pg:
        yield pg

@pytest.fixture
async def db_session(postgres_container):
    # Session wrappée dans une transaction rollbackée après chaque test
    ...
```

#### Tests de contrat (`tests/contract/`)

```python
# Vérifie que TOUTES les routes respectent l'enveloppe

async def test_all_success_responses_have_envelope(client):
    response = await client.get("/api/v1/health/live")
    assert response.json()["success"] is True
    assert "data" in response.json()
    assert "meta" in response.json()
    assert "X-Request-Id" in response.headers

async def test_error_codes_are_stable(client):
    response = await client.post("/api/v1/auth/login", json={"email": "bad", "password": "bad"})
    errors = response.json()["errors"]
    assert all(e["code"].startswith(("TECH.", "DOMAIN.")) for e in errors)
```

### CI GitHub Actions

`**.github/workflows/ci.yml**` :

```yaml
# Déclencheurs : push main, PR vers main
# Jobs :

lint:
  - ruff check .
  - ruff format --check .

typecheck:             # optionnel, flag MYPY_ENABLED
  - mypy app/

test:
  - pytest tests/unit/ --cov=app/domain --cov=app/application --cov-fail-under=80
  - pytest tests/integration/ tests/contract/

security:
  - pip-audit                    # vulnérabilités dépendances Python
  - trivy image $IMAGE_NAME      # vulnérabilités image Docker
```

`**.github/workflows/docker.yml**` :

```yaml
# Déclencheurs : tags v*.*.* (semver)
# Build multi-arch : linux/amd64 + linux/arm64
# Push vers GitHub Container Registry (ghcr.io)
```

### Docker

`**Dockerfile**` multi-stage :

```dockerfile
# Stage 1 : builder (uv + dépendances)
FROM python:3.12-slim AS builder
RUN pip install uv
COPY pyproject.toml uv.lock .
RUN uv sync --frozen --no-dev

# Stage 2 : runtime
FROM python:3.12-slim AS runtime
COPY --from=builder /app/.venv /app/.venv
COPY app/ /app/app/
COPY alembic/ /app/alembic/
ENV PATH="/app/.venv/bin:$PATH"
HEALTHCHECK CMD curl -f http://localhost:8000/api/v1/health/live || exit 1
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

`**docker-compose.yml**` (base) :

- Services : `api`, `db` (postgres:16), `redis` (redis:7, profil optionnel)
- Healthchecks sur `db` et `redis`
- Volume nommé pour les données Postgres

`**docker-compose.override.yml**` (dev) :

- Hot-reload activé (`fastapi dev`)
- Port DB exposé en local (debug)
- Volume bind-mount du code source

---

## 11. Phase 6 — Documentation & évolutivité

### Objectif

La documentation est un livrable de première classe, pas une annexe. Livrable : un contributeur externe peut ajouter une entité complète (domain → endpoint → test) en suivant les guides, sans lire le code.

### `README.md` — structure obligatoire

```markdown
# FastAPI Boilerplate

[Badges : CI, coverage, licence, version]

> Une phrase qui résume ce que c'est et pour qui.

## Quickstart (< 5 minutes)
## Architecture
## Personas & niveaux de complexité
## Conventions
  ### Codes d'erreur (TECH.* / DOMAIN.*)
  ### request_id / correlation_id
  ### Idempotency
## Configuration (variables d'environnement)
## Commandes dev (Makefile)
## Tests
## Contribution
## Roadmap V2
## Licence
```

### Guides d'extension

Chaque guide suit la même structure : contexte → étapes numérotées → exemple complet → erreurs fréquentes.


| Guide                     | Ce qu'il couvre                                          |
| ------------------------- | -------------------------------------------------------- |
| `add-entity.md`           | Entity + ValueObject + Port + Migration + Seed           |
| `add-endpoint.md`         | UseCase + DTO + Router + Schema + Exception handler      |
| `add-migration.md`        | Alembic generate + review + upgrade + rollback           |
| `add-error-code.md`       | Nouvelle exception domain + code DOMAIN.* + mapping HTTP |
| `enable-redis.md`         | Passer de in-memory à Redis en prod                      |
| `enable-soft-delete.md`   | Activer le pattern sur une entité                        |
| `enable-opentelemetry.md` | Brancher OTel sans modifier le domaine                   |


### Seeds versionnés

```python
# scripts/seeds/v1/dev.py
"""
Seed de développement V1.
Idempotent : vérifie l'existence avant insertion.
"""

async def run(session: AsyncSession) -> None:
    await create_admin_user(session, email="admin@example.com")
    await create_sample_users(session, count=20)  # Pour tester la pagination
```

### Checklist mise en production

Avant chaque déploiement en production :

- `APP_ENV=prod` configuré
- `APP_SECRET_KEY` est un secret fort (≥ 32 chars, généré aléatoirement)
- `CORS_ORIGINS` ne contient pas `*`
- `DATABASE_URL` pointe vers la DB prod (pas localhost)
- Migrations Alembic jouées : `alembic upgrade head`
- Sauvegardes DB configurées et testées
- `pip-audit` passé sans vulnérabilités critiques
- `trivy` passé sur l'image Docker
- Healthchecks `/api/v1/health/ready` retournent `200 OK`
- `CHANGELOG.md` mis à jour avec la version

---

## 12. Variables d'environnement

> Toutes les variables sont dans `.env.example` avec valeurs par défaut et commentaires.

### Application


| Variable         | Défaut                | Description                                                 |
| ---------------- | --------------------- | ----------------------------------------------------------- |
| `APP_ENV`        | `dev`                 | Environnement : `dev`, `test`, `staging`, `preprod`, `prod` |
| `APP_NAME`       | `fastapi-boilerplate` | Nom du service (logs, traces)                               |
| `APP_VERSION`    | `0.1.0`               | Version (SemVer)                                            |
| `APP_LOG_LEVEL`  | `info`                | Niveau de log : `debug`, `info`, `warning`, `error`         |
| `CONFIG_VERSION` | `1`                   | Version de config pour les ops                              |


### Sécurité


| Variable                      | Défaut                  | Description                                       |
| ----------------------------- | ----------------------- | ------------------------------------------------- |
| `APP_SECRET_KEY`              | —                       | **Obligatoire en prod** — clé JWT (≥ 32 chars)    |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                    | Durée de vie access token                         |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | `7`                     | Durée de vie refresh token                        |
| `CORS_ORIGINS`                | `http://localhost:3000` | Liste d'origins autorisées (séparées par virgule) |


### Base de données


| Variable          | Défaut                                             | Description                                |
| ----------------- | -------------------------------------------------- | ------------------------------------------ |
| `DATABASE_URL`    | `postgresql+asyncpg://user:pass@localhost:5432/db` | URL complète                               |
| `DB_POOL_SIZE`    | `10`                                               | Taille du pool de connexions               |
| `DB_MAX_OVERFLOW` | `20`                                               | Connexions supplémentaires au-delà du pool |
| `DB_POOL_TIMEOUT` | `30`                                               | Timeout acquisition connexion (secondes)   |


### Redis (optionnel)


| Variable                 | Défaut                     | Description                                             |
| ------------------------ | -------------------------- | ------------------------------------------------------- |
| `REDIS_ENABLED`          | `false`                    | Activer Redis (rate limit, idempotency, révocation JWT) |
| `REDIS_URL`              | `redis://localhost:6379/0` | URL Redis                                               |
| `REDIS_RETRY_ATTEMPTS`   | `3`                        | Nombre de tentatives                                    |
| `REDIS_RETRY_BACKOFF_MS` | `100`                      | Backoff initial (ms)                                    |


### Rate limiting


| Variable                       | Défaut | Description                        |
| ------------------------------ | ------ | ---------------------------------- |
| `RATE_LIMIT_LOGIN_PER_MINUTE`  | `5`    | Max tentatives login / minute / IP |
| `RATE_LIMIT_REGISTER_PER_HOUR` | `10`   | Max inscriptions / heure / IP      |


### Idempotency


| Variable                  | Défaut | Description                         |
| ------------------------- | ------ | ----------------------------------- |
| `IDEMPOTENCY_TTL_SECONDS` | `900`  | TTL des clés d'idempotency (15 min) |


### Features flags


| Variable              | Défaut  | Description                   |
| --------------------- | ------- | ----------------------------- |
| `SOFT_DELETE_ENABLED` | `false` | Activer le soft delete global |
| `MYPY_STRICT`         | `false` | Mode strict mypy en CI        |


---

## Activer / désactiver les features optionnelles

### Redis (optionnel)

- **Désactivé (par défaut)** :
  - `REDIS_ENABLED=false`
  - Attendu : `/api/v1/health/ready` ne vérifie pas Redis.
- **Activé** :
  - `REDIS_ENABLED=true`
  - Configure `REDIS_URL`
  - Attendu : les fonctionnalités qui s’appuient sur Redis (rate limiting, idempotency, révocation JWT) sont actives, et `/api/v1/health/ready` vérifie Redis.

### mypy (optionnel)

- **Non bloquant par défaut** : l’objectif est de ne pas empêcher un clone/POC de tourner.
- **Activer strict en CI** : `MYPY_STRICT=true` (et/ou `MYPY_ENABLED` selon workflow CI).

### Soft delete (optionnel)

- **Désactivé (par défaut)** : `SOFT_DELETE_ENABLED=false`
- **Activer** : `SOFT_DELETE_ENABLED=true` (voir Phase 3 pour les contraintes d’index partiels et le filtrage global).

---

## 13. Roadmap V2

Exclus de V1 intentionnellement — complexité non justifiée avant product-market fit.


| Feature                          | Justification                                                  |
| -------------------------------- | -------------------------------------------------------------- |
| **OpenTelemetry complet**        | Tracing distribué — nécessite infra (Jaeger, Tempo)            |
| **Prometheus metrics**           | Métriques applicatives — nécessite infra (Prometheus, Grafana) |
| **Queue / workers**              | Celery ou RQ — pour jobs longs et retry async                  |
| **Bus d'événements externe**     | RabbitMQ, Kafka, ou Redis Streams — V1 bus local suffit        |
| **RS256 pour JWT**               | Utile multi-service — HS256 suffisant en service unique        |
| **RBAC granulaire**              | Permissions `resource:action` — V1 rôles simples suffisent     |
| **Filtering/sorting dynamiques** | Complexité requête — V1 pagination limit/offset suffit         |
| **Rate limiting distribué**      | Multi-instance — V1 Redis centralisé suffit                    |
| **Email / notifications**        | Sendgrid, SES, SMTP — hors scope boilerplate                   |
| **Multi-tenancy**                | Schémas Postgres par tenant — cas d'usage spécifique           |


---

## 14. Ordre d'implémentation

```
Phase 1   ──────────────────────────────────────────────────────────►  Repo clonable, Makefile, ADR
   │
Phase 2   ──────────────────────────────────────────────────────────►  FastAPI, Clean Arch, Health, Logs
   │
Phase 3   ──────────────────────────────────────────────────────────►  SQLAlchemy, Alembic, UoW, Repos
   │
Phase 4 ──────────── (peut démarrer dès fin Phase 3)
   │                                                                 ►  Auth, JWT, Redis, Events, Audit
Phase 5 ──────────── (peut démarrer dès fin Phase 2)
   │                                                                 ►  Tests unit, CI, Docker
   │
Phase 6   ──────────────────────────────────────────────────────────►  Doc, Guides, Seeds, Checklist prod
```

**Règle** : chaque phase livre quelque chose d'**exécutable** et de **testable indépendamment**. On ne passe pas à la phase N+1 si `make test` échoue.

**Commits** : convention [Conventional Commits](https://www.conventionalcommits.org/) dès le premier commit.

```
feat(phase-1): init pyproject.toml + uv + makefile
feat(phase-2): add fastapi skeleton + health endpoints
feat(phase-3): add sqlalchemy async + alembic migrations
feat(phase-4): add jwt auth + redis rate limiting
feat(phase-5): add testcontainers + ci pipeline
docs(phase-6): add readme + extension guides
```

---

## FAQ / Troubleshooting

### “`make` n’est pas reconnu” (Windows)

- Installe `make` (ex: via Chocolatey) ou lance les commandes manuellement (voir Quickstart : `uv sync`, `alembic upgrade head`, `fastapi dev ...`).

### “La DB ne démarre pas”

- Vérifie que Docker Desktop est lancé
- Vérifie les ports (ex: 5432 déjà utilisé)
- Relance : `docker compose down -v && docker compose up -d db`

### “`/api/v1/health/ready` retourne 503”

- Si Redis est activé : vérifie `REDIS_URL` et que le conteneur Redis est up
- Vérifie `DATABASE_URL` et que les migrations sont jouées : `alembic upgrade head`

---

*Plan rédigé le 2026-04-20 — version 1.0.0*
*Prochaine révision : après Phase 3 (retours d'implémentation)*