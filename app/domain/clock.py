from __future__ import annotations

"""
Port `Clock` (abstraction du temps).

Rôle
----
Permettre d'injecter une source de temps dans la couche Application/Domaine pour tests déterministes.

Intervient dans
--------------
- Infrastructure : `app/infrastructure/clock.py` fournit `SystemClock`.

Scénario nominal
----------------
- `Clock.now()` retourne `datetime` (souvent timezone-aware UTC).
"""

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Port de temps (source injectable)."""
    def now(self) -> datetime: ...
