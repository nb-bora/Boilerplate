## Contexte
Ajouter un endpoint V1 en respectant Clean Architecture et le contrat d’enveloppe.

## Étapes
1. Créer le DTO `app/application/.../dto.py`
2. Implémenter le use-case `app/application/.../*.py`
3. Ajouter les schémas HTTP `app/adapters/http/schemas/*.py`
4. Ajouter la route dans `app/adapters/http/v1/*.py`
5. Ajouter/adapter les tests de contrat

## Exemple complet
Voir `app/adapters/http/v1/users.py` et `app/application/users/get_me.py`.

## Erreurs fréquentes
- Retourner un dict “nu” au lieu de `success(...)`
- Oublier `X-Request-Id` (middleware)

