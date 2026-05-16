from collections.abc import Iterator

import pytest

from oci_arch_studio_backend.core.config import get_settings


@pytest.fixture(autouse=True)
def isolated_review_history_path(tmp_path) -> Iterator[None]:
    settings = get_settings()
    original_path = settings.review_history_path
    settings.review_history_path = tmp_path / "review_history.json"
    try:
        yield
    finally:
        settings.review_history_path = original_path
