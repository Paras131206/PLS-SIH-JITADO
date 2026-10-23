from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "APAAR-SDMS Platform & Trust Layer"
    API_V1_STR: str = "/v1"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # Security
    SECRET_KEY: str = "super-secret-development-key-change-in-production-1234567890"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/apaar_sdms"
    SQLITE_FALLBACK_URL: str = "sqlite:///./apaar_sdms.db"

    # Redis / Queue
    REDIS_URL: str = "redis://localhost:6379/0"

    # AICTE Trust & DIDs
    AICTE_DID: str = "did:web:aicte.gov.in"
    TRUSTED_ISSUER_REGISTRY: str = "contracts/trusted_issuers.json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
