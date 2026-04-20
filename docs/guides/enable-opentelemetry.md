## Contexte

Ce boilerplate est **OTel-ready** :

- un `request_id` est généré et propagé (`X-Request-Id`),
- le header `traceparent` est parsé (logs enrichis `trace_id` / `span_id`),
- la logique est centralisée dans un middleware (point d’extension propre).

Ce guide décrit comment brancher OpenTelemetry **sans casser** :

- le domaine (aucune dépendance OTel dans `domain/`),
- le contrat de logs (champs existants conservés),
- la corrélation (request_id ↔ trace).

---

## Où brancher OTel dans ce repo

- Middleware log/trace: `app/core/middleware/logging.py`
- Context: `app/core/context.py` (request-scoped)
- Entrée API: `app/main.py` (ordre middlewares)

---

## Étapes détaillées (proposition V2)

### 1) Ajouter les dépendances

Ajouter dans les dépendances (dev ou prod selon usage) :

- `opentelemetry-api`
- `opentelemetry-sdk`
- exporter (OTLP, Jaeger, etc.)
- instrumentation ASGI/FastAPI

### 2) Initialiser le tracer provider au boot

Dans le “composition root” (`app/main.py`) ou un module `app/infrastructure/otel.py` :

- configurer `TracerProvider`
- configurer exporter(s)
- configurer resource (`service.name`, version, env)

### 3) Créer des spans autour des requêtes

Option recommandée :

- ajouter `OpenTelemetryMiddleware` (ASGI) **avant** le middleware logging,
- ou étendre `LoggingMiddleware` pour créer des spans (moins standard).

### 4) Garder la compat logs

La règle de non-régression :

- `trace_id` / `span_id` doivent rester présents dans les logs,
- `request_id` reste la clé “humaine” de corrélation.

### 5) Vérifier

- un `traceparent` entrant doit être corrélé dans les logs
- l’exporteur reçoit des traces

---

## Pièges fréquents

- Doubler l’instrumentation (middleware OTel + instrumentation automatique) → spans dupliqués.
- Perdre `request_id` dans les logs → dashboards cassés (régression).

