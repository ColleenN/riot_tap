from datetime import datetime, timezone

import pytest

from tap_riotapi import rate_limiting

FROZEN_NOW = datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)


class _FrozenDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return FROZEN_NOW.astimezone(tz) if tz else FROZEN_NOW.replace(tzinfo=None)


@pytest.fixture
def frozen_now(monkeypatch):
    """Fix the clock rate_limiting reads, and return that instant."""
    monkeypatch.setattr(rate_limiting, "datetime", _FrozenDatetime)
    return FROZEN_NOW
