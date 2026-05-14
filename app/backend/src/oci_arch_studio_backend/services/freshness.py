from __future__ import annotations

from datetime import UTC, datetime


STALE_AFTER_DAYS = 120


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def age_days(timestamp: str | None, now: datetime | None = None) -> int | None:
    parsed = parse_timestamp(timestamp)
    if parsed is None:
        return None
    reference = now or datetime.now(UTC)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return max((reference - parsed).days, 0)


def is_stale_source(
    fetched_timestamp: str | None,
    freshness_score: float | None,
    now: datetime | None = None,
) -> bool:
    if freshness_score is not None and freshness_score < 0.5:
        return True
    days = age_days(fetched_timestamp, now=now)
    return days is None or days > STALE_AFTER_DAYS
