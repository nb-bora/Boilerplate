## Contexte

Ce boilerplate utilise **Alembic** avec **SQLAlchemy async 2.x**.
Ce guide explique comment ajouter une migration **de manière sûre**, reproductible et compatible avec l’exécution
async (cf. `alembic/env.py`).

---

## Pré-requis

- Postgres en local (ex: via `docker compose up -d db`)
- `DATABASE_URL` correctement configurée (dans `.env` ou variables d’environnement)

Commandes utiles :

```bash
python -m alembic current
python -m alembic history
```

---

## Étapes détaillées

### 1) Démarrer la DB

```bash
docker compose up -d db
```

### 2) Vérifier que l’app “voit” la DB

```bash
python -m alembic current
```

Si ça échoue, corriger `DATABASE_URL`.

### 3) Créer une migration

#### Option A (classique) : autogenerate

Après avoir modifié tes modèles ORM (`app/adapters/persistence/models/*`) :

```bash
python -m alembic revision --autogenerate -m "add <feature>"
```

#### Option B : migration manuelle

```bash
python -m alembic revision -m "add <feature>"
```

Puis éditer `upgrade()` / `downgrade()`.

### 4) Relire (obligatoire)

Points à vérifier systématiquement :

- **FK** (ondelete ? nullable ?)
- **Index** sur les colonnes de lookup
- **Contraintes d’unicité** (email, slug, etc.)
- **Types** (Postgres: `JSONB`, `UUID` si utilisé, `TIMESTAMP WITH TIME ZONE`)
- **Downgrade** : cohérent et exécutable

### 5) Appliquer

```bash
python -m alembic upgrade head
```

### 6) (Option) Rollback local

```bash
python -m alembic downgrade -1
```

---

## Pièges / erreurs fréquentes

- **Env async mal configuré** :
  - si `alembic upgrade` plante avec des erreurs de loop / run_sync, vérifier `alembic/env.py`
- **Autogenerate incomplet** :
  - Alembic peut rater certains indexes/contraintes (surtout partial indexes).
  - Toujours relire et compléter à la main.
- **Imports Postgres manquants** :
  - ex: `from sqlalchemy.dialects.postgresql import JSONB`
- **Image Docker** :
  - l’image runtime doit embarquer `alembic/` + `alembic.ini` si tu veux migrer depuis le conteneur.

