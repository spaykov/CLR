from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="CLR_")

    ollama_base_url: str = "http://localhost:11434/v1"
    model: str = "mistral-nemo"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"

    # Bandwidth score thresholds (0–100)
    bandwidth_low_threshold: int = 30
    bandwidth_high_threshold: int = 70

    # Auto-decision confidence cutoff (0.0–1.0)
    auto_decision_confidence: float = 0.85

    # Gmail app-password auth (SMTP/POP3)
    gmail_address: str = ""
    gmail_app_password: str = ""


settings = Settings()