from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:secret@localhost:5432/appdb"
    authentik_issuer: str = "http://localhost:9000/application/o/taskmanager/"
    authentik_jwks_url: str = "http://localhost:9000/application/o/taskmanager/jwks/"
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
