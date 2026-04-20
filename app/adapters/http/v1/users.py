from __future__ import annotations

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
    usecase = GetCurrentUser(uow=uow)
    out = await usecase.execute(user_id)
    return success(request, data=out.model_dump())
