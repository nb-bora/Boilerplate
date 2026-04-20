## Contexte
Ajouter un nouveau code d’erreur stable (`TECH.*` ou `DOMAIN.*`).

## Étapes
1. Ajouter le code dans `app/common/constants.py`
2. Créer/étendre une exception métier (ex: `app/domain/users/exceptions.py`)
3. Mapper en HTTP dans `app/adapters/http/exception_handlers.py`
4. Ajouter un test de contrat dans `tests/contract/` (à créer si absent)

