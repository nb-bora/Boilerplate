from __future__ import annotations

from pydantic import BaseModel


class UserOutput(BaseModel):
    id: str
    email: str
    roles: list[str]
    is_active: bool
