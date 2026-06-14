from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    api_key: str
    anthropic_api_key: str

    zoho_client_id: str
    zoho_client_secret: str
    zoho_refresh_token: str
    zoho_account_id: str
    zoho_from_email: str

    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str

    motherduck_token: str

    backblaze_access_key_id: str
    backblaze_secret_access_key: str
    backblaze_bucket_name: str
    backblaze_endpoint_url: str

    tele_alert_email: str
    cors_origins: str = "*"  # comma-separated list or "*"
    redis_url: str = "redis://localhost:6379/0"
    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
