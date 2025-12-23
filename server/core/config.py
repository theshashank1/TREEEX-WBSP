import os
from pathlib import Path
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def find_env_file() -> str:
    """Find . env file by checking multiple possible locations"""
    # Get the directory where this config file lives
    this_file_dir = Path(__file__).resolve().parent

    # Possible .env locations (in priority order)
    possible_paths = [
        Path.cwd() / ".env",  # Current working directory
        this_file_dir / ".env",  # Same dir as this file
        this_file_dir.parent / ".env",  # Parent dir (project root)
        this_file_dir.parent.parent / ". env",  # Two levels up
    ]

    for path in possible_paths:
        if path.exists():
            return str(path)

    return ".env"  # Fallback


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Server
    ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0. 0"
    PORT: int = 8000

    # Database
    DATABASE_URL: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[int] = None
    POSTGRES_DB: Optional[str] = None

    @model_validator(mode="after")
    def assemble_db_connection(self) -> "Settings":
        if self.DATABASE_URL is None and all(
            [
                self.POSTGRES_USER,
                self.POSTGRES_PASSWORD,
                self.POSTGRES_HOST,
                self.POSTGRES_PORT,
                self.POSTGRES_DB,
            ]
        ):
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self. POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return self

    # Redis
    REDIS_URL: Optional[str] = None

    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None

    # Backwards compatibility if you used these names in . env
    SUPABASE_PUBLISHABLE_KEY: Optional[str] = None
    SUPABASE_SECRET_KEY: Optional[str] = None

    @model_validator(mode="after")
    def consolidate_supabase_keys(self) -> "Settings":
        """Ensure SUPABASE_KEY is populated if alternate names are used"""
        if not self.SUPABASE_KEY:
            self.SUPABASE_KEY = (
                self.SUPABASE_PUBLISHABLE_KEY or self.SUPABASE_SECRET_KEY
            )
        return self

    # Meta WhatsApp
    META_API_VERSION: Optional[str] = None
    META_GRAPH_API_URL: Optional[str] = None
    META_WEBHOOK_VERIFY_TOKEN: Optional[str] = None
    META_APP_SECRET: Optional[str] = None
    META_ACCESS_TOKEN: Optional[str] = None

    # Azure Blob Storage
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    AZURE_STORAGE_CONTAINER_NAME: str = "whatsapp-media"
    AZURE_STORAGE_ACCOUNT_NAME: Optional[str] = None
    AZURE_STORAGE_ACCOUNT_KEY: Optional[str] = None

    # Security
    SECRET_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 1 week

    # Rate Limiting
    RATE_LIMIT_MESSAGES_PER_SECOND: int = 10

    # Ngrok (for development tunneling)
    NGROK_AUTHTOKEN: Optional[str] = None
    NGROK_DOMAIN: Optional[str] = None

    @model_validator(mode="after")
    def clean_ngrok_domain(self) -> "Settings":
        """Strip protocol from NGROK_DOMAIN if present"""
        if self.NGROK_DOMAIN:
            self.NGROK_DOMAIN = (
                self.NGROK_DOMAIN.replace("https://", "")
                .replace("http://", "")
                .split("/")[0]
            )
        return self

    # Monitoring
    APPLICATIONINSIGHTS_CONNECTION_STRING: Optional[str] = None
    LOG_DIR: Optional[str] = None
    SENTRY_DSN: Optional[str] = None


# Singleton instance
settings = Settings()


# Debug helper - run this file directly to check config loading
if __name__ == "__main__":
    print("=" * 50)
    print("CONFIG DEBUG INFO")
    print("=" * 50)
    print(f"Working directory: {os.getcwd()}")
    print(f"Config file location: {Path(__file__).resolve()}")
    print(f"Resolved . env path: {find_env_file()}")
    print("-" * 50)
    print(f"ENV: {settings.ENV}")
    print(f"DATABASE_URL loaded: {settings.DATABASE_URL is not None}")
    print(f"SUPABASE_URL: {settings.SUPABASE_URL}")
    print(f"SUPABASE_KEY loaded: {settings. SUPABASE_KEY is not None}")
    print(f"REDIS_URL: {settings.REDIS_URL}")
    print(f"META_ACCESS_TOKEN loaded: {settings.META_ACCESS_TOKEN is not None}")
    print("=" * 50)
