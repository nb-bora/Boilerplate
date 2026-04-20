## Contexte
Ajouter une migration Alembic compatible async.

## Étapes
1. Démarrer la DB (docker compose)
2. Générer une migration : `alembic revision -m "..."` (ou créer le fichier)
3. Revoir la migration (types, index, contraintes)
4. Appliquer : `alembic upgrade head`
5. (Option) rollback : `alembic downgrade -1`

## Erreurs fréquentes
- Oublier de copier `alembic/` dans l’image Docker
- Types PostgreSQL spécifiques non importés (`JSONB`, index partiels, etc.)

