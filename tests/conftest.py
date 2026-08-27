import pytest

from clr.core import rate_limit


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    # rate_limit's hit-tracking dict is process-global; without this, tests
    # across different files that hit the same route path would share a
    # budget and start tripping 429s once the suite issues more than the
    # per-route limit within one wall-clock window (the whole suite runs in
    # well under a minute).
    rate_limit.reset()
    yield
