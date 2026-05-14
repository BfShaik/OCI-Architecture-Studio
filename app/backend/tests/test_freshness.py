from datetime import UTC, datetime

from oci_arch_studio_backend.services.freshness import is_stale_source


def test_stale_source_detection_flags_old_or_low_freshness_sources() -> None:
    now = datetime(2026, 5, 14, tzinfo=UTC)

    assert is_stale_source("2025-01-01T00:00:00+00:00", 0.9, now=now)
    assert is_stale_source("2026-05-01T00:00:00+00:00", 0.4, now=now)
    assert not is_stale_source("2026-05-01T00:00:00+00:00", 0.8, now=now)
