import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    DATABASE_URL: str = "postgresql+asyncpg://postgres:123456@localhost:5432/animation_analysis"
    SECRET_KEY: str = "change_me"
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = ["*"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Render provides postgres:// but SQLAlchemy async needs postgresql+asyncpg://
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace(
                "postgres://", "postgresql+asyncpg://", 1
            )
        elif self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )


settings = Settings()
