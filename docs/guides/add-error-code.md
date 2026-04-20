## Contexte

Les erreurs exposées par l’API sont **stables** et **testables** via des codes :

- `TECH.*` : erreurs techniques (validation, auth, rate limit, interne…)
- `DOMAIN.*` : erreurs métier (invariants, règles de gestion)

Ce guide explique comment ajouter un nouveau code et garantir :

- une enveloppe d’erreur uniforme (`ErrorEnvelope`),
- un mapping HTTP cohérent (status + message),
- un test de contrat qui verrouille le comportement.

---

## Où ça vit ?

- Codes: `app/common/constants.py`
- Exceptions domaine: `app/domain/<feature>/exceptions.py`
- Mapping HTTP: `app/adapters/http/exception_handlers.py`
- Tests: `tests/contract/`

---

## Étapes détaillées

### 1) Ajouter (ou choisir) le code

Dans `app/common/constants.py` :

- ajouter un code `TECH.*` si c’est purement technique (ex: conflit idempotency),
- ajouter un code `DOMAIN.*` si c’est une règle métier (ex: `PROJECT.ARCHIVED`).

Règle :

- un code doit être **stable** (modif = breaking change côté client).

### 2) Créer/étendre une exception domaine

Dans `app/domain/<feature>/exceptions.py` :

- créer une exception explicite (ex: `ProjectArchived`)
- lui associer le code `DOMAIN.*`

Objectif :

- la couche Application/Domain lève l’exception,
- l’Adapter HTTP la transforme en erreur HTTP enveloppée.

### 3) Mapper en HTTP

Dans `app/adapters/http/exception_handlers.py` :

- décider du status HTTP (souvent 400/401/403/404/409)
- renvoyer `ErrorEnvelope` via `error(...)`

### 4) Ajouter un test de contrat

Dans `tests/contract/` :

- provoquer le cas d’erreur,
- vérifier:
  - `success == false`
  - `errors[0].code == "DOMAIN...."` (ou `TECH....`)
  - `meta.request_id` présent

### 5) Vérifier

```bash
python -m ruff check .
python -m pytest
```

---

## Erreurs fréquentes

- **Réutiliser un code existant “par défaut”** :
  - mieux vaut un code précis, sinon les clients ne peuvent pas réagir correctement.
- **Mettre de la logique HTTP dans le domaine** :
  - le domaine ne doit jamais connaître status codes.

