from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DomainError(Exception):
    code: str
    message: str


class UserAlreadyExists(DomainError):
    def __init__(self) -> None:
        super().__init__(code="DOMAIN.USER.ALREADY_EXISTS", message="Email already registered")


class InvalidCredentials(DomainError):
    def __init__(self) -> None:
        super().__init__(code="TECH.AUTH.INVALID_CREDENTIALS", message="Invalid credentials")


class UserNotFound(DomainError):
    def __init__(self) -> None:
        super().__init__(code="DOMAIN.USER.NOT_FOUND", message="User not found")


class UserInactive(DomainError):
    def __init__(self) -> None:
        super().__init__(code="DOMAIN.USER.INACTIVE", message="User inactive")
