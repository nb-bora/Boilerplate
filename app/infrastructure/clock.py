from __future__ import annotations

"""
Implémentation infrastructure du port `Clock`.

Rôle
----
Fournir une horloge système (UTC) implémentant `app/domain/clock.py::Clock`.

Intervient dans
--------------
- Injectée dans les use-cases si/Quand on rend le temps injectable (tests déterministes).

Scénario nominal
----------------
- `now()` retourne `datetime` timezone-aware en UTC.
"""

from datetime import datetime, timezone

from app.domain.clock import Clock


class SystemClock(Clock):
    """Horloge système UTC."""
    def now(self) -> datetime:
        """Retourne l'heure courante UTC (timezone-aware)."""
        return datetime.now(timezone.utc)
