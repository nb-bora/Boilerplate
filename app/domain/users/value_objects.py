from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        v = self.value.strip().lower()
        object.__setattr__(self, "value", v)
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")


@dataclass(frozen=True, slots=True)
class HashedPassword:
    value: str
