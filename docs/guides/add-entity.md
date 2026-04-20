## Contexte

Ce guide explique comment ajouter une **nouvelle entité métier** (un “model” au sens produit) de manière complète
et cohérente avec la Clean Architecture du repo.

Objectif : partir d’une idée (ex: `Project`) et arriver à :

- une **entité domaine** + invariants,
- une **persistance** (ORM + migration),
- des **use-cases**,
- des **routes HTTP**,
- des **tests de contrat**.

> Si tu cherches uniquement à ajouter une route sans nouveau modèle, voir `docs/guides/add-endpoint.md`.

---

## Répertoires / fichiers à utiliser

### Domaine (source de vérité)

- `app/domain/<feature>/entity.py`
- `app/domain/<feature>/value_objects.py`
- `app/domain/<feature>/exceptions.py`
- `app/domain/<feature>/repository.py`
- (optionnel) `app/domain/<feature>/events.py`

### Application (orchestration)

- `app/application/<feature>/dto.py`
- `app/application/<feature>/<use_case>.py`

### Adapters (implémentations)

- ORM:
  - `app/adapters/persistence/models/<feature>.py`
  - `app/adapters/persistence/mappers/<feature>.py`
  - `app/adapters/persistence/repositories/<feature>.py`
  - `app/adapters/persistence/unit_of_work.py` (câblage repo)
- HTTP:
  - `app/adapters/http/schemas/<feature>.py`
  - `app/adapters/http/v1/<feature>.py`
  - `app/adapters/http/v1/router.py`

### DB (migrations)

- `alembic/versions/<revision>_<message>.py`

### Tests (V1: contrat)

- `tests/contract/test_<feature>.py` (si besoin)

---

## Étapes détaillées

### 1) Créer le package domaine

Créer `app/domain/<feature>/` avec `__init__.py`.

### 2) Écrire l’entité domaine

Dans `app/domain/<feature>/entity.py` :

- définir les champs (id ULID string, timestamps si besoin),
- définir les invariants sous forme de méthodes (ex: `archive()`, `rename()`),
- éviter toute dépendance à SQLAlchemy/FastAPI.

### 3) Écrire le port repository

Dans `app/domain/<feature>/repository.py` :

- définir l’interface minimale utilisée par l’application (CRUD ciblé),
- privilégier des méthodes explicites (ex: `get_by_slug`, `list_for_user`).

### 4) DTO + use-cases Application

Dans `app/application/<feature>/dto.py` :

- `CreateXInput`, `XOutput`, etc.

Dans `app/application/<feature>/create.py` :

- utiliser `uow.<repo>` pour persister,
- lever des exceptions domaine pour les cas métier.

### 5) Matérialiser la persistance (ORM + repository)

1. Modèle ORM dans `app/adapters/persistence/models/<feature>.py`
2. Mapper dans `app/adapters/persistence/mappers/<feature>.py`
3. Repository concret dans `app/adapters/persistence/repositories/<feature>.py`
4. Ajouter le repo au Unit of Work (`app/adapters/persistence/unit_of_work.py`)

### 6) Migration Alembic

```bash
python -m alembic revision --autogenerate -m "add <feature>"
python -m alembic upgrade head
```

Relire la migration (FK/index/unique).

### 7) Exposer via HTTP

1. Schémas HTTP: `app/adapters/http/schemas/<feature>.py`
2. Routes: `app/adapters/http/v1/<feature>.py`
3. Publier le router: `app/adapters/http/v1/router.py`

### 8) Tester (V1)

```bash
python -m pytest
```

Ajouter un test de contrat si tu ajoutes un endpoint public important.

---

## Relations entre modèles (important)

### Niveau domaine

Recommandation V1 :

- stocker une relation par **identifiant** :
  - `child.parent_id: str`
- éviter d’avoir des graphes d’objets (“ORM-style”) dans le domaine.

### Niveau DB/ORM

- ajouter la FK (`parent_id`) dans la table.
- ajouter `relationship()` si utile pour les requêtes, mais charger explicitement en repo.

Cas courants :

- **1-N** : FK dans la table enfant + index
- **N-N** : table d’association + méthodes repo dédiées

---

## Erreurs fréquentes

- Ajouter une `relationship()` et compter sur le lazy-loading en async.
- Mettre des types SQLAlchemy dans le domaine.
- Exposer directement le modèle ORM en HTTP (couplage fort).
