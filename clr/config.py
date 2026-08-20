from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="CLR_")

    ollama_base_url: str = "http://localhost:11434/v1"
    model: str = "mistral-nemo"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "info"

    # Optional shared-secret auth for /api/v1/*, checked via the X-API-Key
    # header (for scripts/curl). Empty string (default) means header auth is
    # off, same optional-config pattern as gmail_app_password.
    api_key: str = ""

    # Optional login password for the browser UI, checked via POST
    # /api/v1/auth/login and exchanged for a session cookie. Deliberately a
    # separate secret from api_key: this one gets typed by hand on other
    # devices, so it's a memorable passphrase rather than a random token.
    login_password: str = ""

    # Bandwidth score thresholds (0–100)
    bandwidth_low_threshold: int = 30
    bandwidth_high_threshold: int = 70

    # Auto-decision confidence cutoff (0.0–1.0)
    auto_decision_confidence: float = 0.85

    # Gmail app-password auth (IMAP)
    gmail_address: str = ""
    gmail_app_password: str = ""


settings = Settings()