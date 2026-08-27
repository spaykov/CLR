import pytest

from main import validate_startup_config


def test_localhost_allows_any_config():
    validate_startup_config("127.0.0.1", "", "")
    validate_startup_config("localhost", "short", "x")


def test_lan_exposure_requires_a_secret():
    with pytest.raises(SystemExit, match="neither"):
        validate_startup_config("0.0.0.0", "", "")


def test_lan_exposure_rejects_a_short_api_key():
    with pytest.raises(SystemExit, match="CLR_API_KEY"):
        validate_startup_config("0.0.0.0", "too-short", "")


def test_lan_exposure_rejects_a_short_login_password():
    with pytest.raises(SystemExit, match="CLR_LOGIN_PASSWORD"):
        validate_startup_config("0.0.0.0", "", "short")


def test_lan_exposure_accepts_strong_secrets():
    validate_startup_config("0.0.0.0", "a" * 32, "correct-horse-battery-staple-42")


def test_lan_exposure_accepts_strong_api_key_alone():
    validate_startup_config("0.0.0.0", "a" * 32, "")
