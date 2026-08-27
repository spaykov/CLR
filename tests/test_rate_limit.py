from clr.core import rate_limit


def test_allows_up_to_the_limit():
    assert rate_limit.allow("k", 3, 60) is True
    assert rate_limit.allow("k", 3, 60) is True
    assert rate_limit.allow("k", 3, 60) is True


def test_blocks_once_limit_is_exceeded():
    for _ in range(3):
        rate_limit.allow("k", 3, 60)
    assert rate_limit.allow("k", 3, 60) is False


def test_different_keys_have_independent_budgets():
    for _ in range(3):
        rate_limit.allow("a", 3, 60)
    assert rate_limit.allow("a", 3, 60) is False
    assert rate_limit.allow("b", 3, 60) is True


def test_old_hits_expire_out_of_the_window(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(rate_limit.time, "monotonic", lambda: now[0])

    for _ in range(3):
        rate_limit.allow("k", 3, 60)
    assert rate_limit.allow("k", 3, 60) is False

    now[0] += 61  # past the window
    assert rate_limit.allow("k", 3, 60) is True
