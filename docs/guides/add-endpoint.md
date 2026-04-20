## Contexte

Ce guide explique comment **ajouter un endpoint V1** (route HTTP) en respectant :

- la **Clean Architecture** du repo (Domain → Application → Adapters),
- le **contrat d’enveloppe** (`SuccessEnvelope` / `ErrorEnvelope`),
- les conventions transverses (headers de traçage, rate limiting, idempotency quand pertinent).

> À lire en parallèle :
>
> - `docs/architecture.md`
> - `docs/WORKFLOWS.md`
> - `docs/guides/add-error-code.md` (si tu ajoutes une nouvelle erreur métier)

---

## Checklist “je sais ce que je veux exposer”

Avant d’écrire :

- **Route** : méthode + path (ex: `POST /api/v1/projects`)
- **Auth** : public / bearer / refresh
- **Validation** : champs requis + formats
- **Effets** : écritures DB ? events ? cache ?
- **Erreurs métier** attendues (`DOMAIN.*`)
- **Erreurs techniques** possibles (`TECH.*` : validation, auth, rate limit, conflit, etc.)
- **Contrat de réponse** : payload `data` + `meta` (request_id)

---

## Emplacements (répertoires/fichiers)

Dans ce repo, un endpoint “complet” touche généralement :

- **Application (use-case)** :
  - `app/application/<feature>/dto.py`
  - `app/application/<feature>/<use_case>.py`
- **HTTP (schemas + route)** :
  - `app/adapters/http/schemas/<feature>.py`
  - `app/adapters/http/v1/<feature>.py`
  - `app/adapters/http/v1/router.py` (inclure le router)
- **Wiring (dépendances)** :
  - `app/adapters/http/dependencies.py` (réutiliser `get_uow`, `get_current_user_id`, etc.)
- **Tests** :
  - `tests/contract/test_*.py` (contract)
  - `tests/test_health.py` (exemple simple de contrat/headers)

---

## Étapes détaillées

### 1) Définir le DTO Application (input/output)

Créer (ou compléter) `app/application/<feature>/dto.py` :

- **Input DTO** : ce que le use-case reçoit (types simples, validables)
- **Output DTO** : ce que l’API renvoie via l’enveloppe

Bonnes pratiques :

- DTO = “contrat interne” de l’application, **pas** le schéma HTTP.
- Garder les champs sérialisables et stables.

### 2) Implémenter le use-case

Créer `app/application/<feature>/<use_case>.py` :

- injecter le **Unit of Work** (port côté Application, impl côté adapters)
- lever des **DomainError** (ex: `UserAlreadyExists`) pour les cas métier

### 3) Définir les schemas HTTP (Pydantic)

Dans `app/adapters/http/schemas/<feature>.py` :

- schéma request (input HTTP)
- schéma response (si besoin) ou s’appuyer sur l’output DTO `.model_dump()`

Bonnes pratiques :

- Le schema HTTP peut être **plus strict** que le domaine (ex: regex email),
  mais doit rester cohérent.

### 4) Ajouter la route V1

Dans `app/adapters/http/v1/<feature>.py` :

- utiliser `APIRouter(prefix="/<feature>")`
- utiliser `Depends(...)` pour l’UoW, cache store, user_id, etc.
- envelopper la réponse avec `success(request, data=...)`
- pour les cas d’erreur **attendus**, lever les exceptions domaine (mappées globalement)

### 5) Publier le router

Dans `app/adapters/http/v1/router.py` :

- `include_router(<feature>.router)`

### 6) Ajouter les tests de contrat

Ajouter un test `tests/contract/test_<feature>.py` si nécessaire :

- vérifier `success`/`data`/`meta.request_id`
- vérifier `X-Request-Id` / `X-Correlation-Id`
- vérifier les codes d’erreur `TECH.*` / `DOMAIN.*` sur les cas négatifs

---

## Exemple (référence dans le repo)

- Endpoint auth : `app/adapters/http/v1/auth.py`
- Endpoint user courant : `app/adapters/http/v1/users.py`
- Use-case : `app/application/users/get_me.py`

---

## Erreurs fréquentes (et comment les éviter)

- **Retourner un dict nu** :
  - attendu : `return success(request, data=...)` (ou `JSONResponse` si réponse “rejouée” idempotency)
- **Oublier d’inclure le router** dans `app/adapters/http/v1/router.py`
- **Mélanger validation HTTP et métier** :
  - 422 = validation schema HTTP
  - 4xx DOMAIN.* = invariants métier
- **Couper à travers les couches** :
  - une route ne doit pas manipuler directement l’ORM (ça passe par use-case + UoW/repo)
- **Tests de contrat incomplets** :
  - toujours vérifier `meta.request_id` + `X-Request-Id`

