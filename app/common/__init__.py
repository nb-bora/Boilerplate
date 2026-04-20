from __future__ import annotations

"""
Package `app.common`.

Rôle
----
Héberge des types/constantes transverses partagés entre plusieurs couches :
- contrat d'enveloppe HTTP (utilisé par l'adapter HTTP),
- codes d'erreur stables (`TECH.*` / `DOMAIN.*`).

Objectifs
---------
- Centraliser les conventions globales et éviter la duplication.
- Garantir la stabilité des contrats (surtout côté API).

Intervient dans
--------------
- Enveloppes : `app/adapters/http/response.py`, `app/adapters/http/exception_handlers.py`
- Codes : exceptions domaine + mapping HTTP
"""
