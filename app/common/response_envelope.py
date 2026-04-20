from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None


class EnvelopeMeta(BaseModel):
    request_id: str


class SuccessEnvelope(BaseModel):
    success: Literal[True] = True
    data: Any
    message: Optional[str] = None
    errors: None = None
    meta: EnvelopeMeta


class ErrorEnvelope(BaseModel):
    success: Literal[False] = False
    data: None = None
    message: str
    errors: list[ErrorDetail]
    meta: EnvelopeMeta

