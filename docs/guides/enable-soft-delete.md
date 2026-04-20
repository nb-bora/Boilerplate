## Contexte

Le soft delete est **optionnel** dans ce boilerplate (voir `SOFT_DELETE_ENABLED`).

Pourquoi optionnel ?

- il impacte **toutes** les requêtes (filtrage global),
- il complique les contraintes d’unicité (index partiels),
- il a des effets de bord sur les relations (FK, “restore”, cascade).

Ce guide explique comment l’activer proprement si ton produit en a réellement besoin.

---

## Stratégie recommandée (Postgres)

Pattern :

- Ajouter `deleted_at TIMESTAMPTZ NULL` sur les tables concernées.
- Filtrer “actifs seulement” par défaut.
- Adapter les contraintes d’unicité via **index partiels** :
  - l’unicité ne s’applique que quand `deleted_at IS NULL`.

---

## Étapes détaillées

### 1) Activer le flag

Dans `.env` :

```bash
SOFT_DELETE_ENABLED=true
```

### 2) Étendre le modèle ORM

Dans `app/adapters/persistence/models/<feature>.py` :

- ajouter `deleted_at` nullable

### 3) Migration Alembic

```bash
python -m alembic revision --autogenerate -m "add soft delete to <feature>"
python -m alembic upgrade head
```

### 4) Unicité (si nécessaire)

Exemple conceptuel (à transposer en Alembic) :

- unique sur `email` pour les users actifs seulement:
  - unique index partiel `(email) WHERE deleted_at IS NULL`

### 5) Repositories

Décider de la convention :

- `get_by_id()` retourne uniquement les actifs
- `get_by_id_including_deleted()` si besoin
- `soft_delete(id)` met `deleted_at=now()`

### 6) Relations / FK

Points à décider :

- un parent soft-deleted peut-il avoir des enfants actifs ?
- cascade soft delete ?
- “restore” : faut-il restaurer les enfants ?

Dans beaucoup de cas, il faut gérer la cascade au niveau Application (use-cases).

---

## Pièges fréquents

- Oublier l’index partiel → collisions d’unicité lors d’un “recreate”.
- Appliquer soft delete sur tout “par défaut” → perf et complexité.
- Exposer des objets soft-deleted dans l’API sans le vouloir.
