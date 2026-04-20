from __future__ import annotations

"""
Routes HTTP V1 : Users.

Rôle
----
Expose les endpoints utilisateur sous `/api/v1/users/*`.

Objectifs
---------
- Illustrer un endpoint protégé (`/me`) utilisant :
  - extraction utilisateur courant via JWT (`get_current_user_id`),
  - use-case applicatif (`GetCurrentUser`),
  - enveloppe de réponse uniforme.

Intervient dans
--------------
- Dépendances : `app/adapters/http/dependencies.py`
- Use-case : `app/application/users/get_me.py`
- Enveloppe : `app/adapters/http/response.py`

Cas alternatifs / exceptions
---------------------------
- 401 si token absent/invalide/blacklisted (dépendance).
- 404 si user introuvable (via `DomainError` mappée en enveloppe).
"""

from fastapi import APIRouter, Depends, Request

from app.adapters.http.dependencies import get_current_user_id, get_uow
from app.adapters.http.response import success
from app.application.users.get_me import GetCurrentUser

router = APIRouter(prefix="/users")


@router.get("/me")
async def me(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    uow=Depends(get_uow),  # noqa: ANN001
):
    """
    Retourne le profil de l'utilisateur courant.

    Scénario nominal
    - `get_current_user_id` fournit `user_id` depuis le JWT.
    - `GetCurrentUser` récupère le user via le repo.
    - La réponse est enveloppée via `success(...)`.
    """
    usecase = GetCurrentUser(uow=uow)
    out = await usecase.execute(user_id)
    return success(request, data=out.model_dump())
