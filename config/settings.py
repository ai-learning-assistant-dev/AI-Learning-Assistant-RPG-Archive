"""
Application configuration settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # FastAPI Configuration
    app_name: str = Field(default="AI Learning Assistant RPG")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=3000)

    # Logging
    log_level: str = Field(default="INFO")

    # pgsql
    pg_host: str = Field(default="localhost")
    pg_port: int = Field(default=5432)
    pg_user: str = Field(default="user")
    pg_password: str = Field(default="123456")
    pg_database: str = Field(default="ai_rpg")

    class Config:
        env_file = ".env"
        env_nested_delimiter = "_"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Global settings instance
settings = get_settings()
