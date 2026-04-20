from __future__ import annotations

from pydantic import BaseModel, Field


class RegisterInput(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=256)


class LoginInput(BaseModel):
    email: str
    password: str


class TokenOutput(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
