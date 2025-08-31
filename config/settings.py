"""
Application configuration settings.
"""

from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class LLMConfig(BaseModel):
    url: str = Field(default="http://localhost:1234/v1")
    api_key: str = Field(default="")
    model_name: str = Field(default="")


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # FastAPI Configuration
    app_name: str = Field(default="AI Learning Assistant RPG")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=3000)
    base_llm: LLMConfig = Field(default=LLMConfig())

    # Logging
    log_level: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        env_nested_delimiter = "_"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Global settings instance
settings = get_settings()
