from __future__ import annotations

"""
Use-case Application : GetCurrentUser.

Rôle
----
Retourner le profil de l'utilisateur courant (par `user_id`), typiquement pour `/users/me`.

Objectifs
---------
- Isoler le workflow "lecture profil" dans la couche Application.
- Déclencher une erreur métier stable si l'utilisateur est introuvable.

Intervient dans
--------------
- Adapter HTTP : `app/adapters/http/v1/users.py::me`
- UoW : `app/adapters/persistence/unit_of_work.py`
- Repo : `app/adapters/persistence/repositories/user.py`

Scénario nominal
----------------
1) Ouvre le UoW.
2) Cherche l'utilisateur par id.
3) Si trouvé, construit et retourne `UserOutput`.

Exceptions attendues
--------------------
- `UserNotFound` si aucun utilisateur (HTTP 404 via exception handler).
"""

from app.application.users.dto import UserOutput
from app.domain.users.exceptions import UserNotFound


class GetCurrentUser:
    """Use-case de récupération du user courant."""
    def __init__(self, *, uow) -> None:  # noqa: ANN001
        self.uow = uow

    async def execute(self, user_id: str) -> UserOutput:
        """Exécute le use-case et retourne `UserOutput`."""
        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if user is None:
                raise UserNotFound()
            return UserOutput(
                id=user.id,
                email=user.email.value,
                roles=[r.value for r in user.roles],
                is_active=user.is_active,
            )
