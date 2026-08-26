from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Online Cinema API"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str
    ALEMBIC_DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TASK_ALWAYS_EAGER: bool = False
    CELERY_DELETE_EXPIRED_TOKENS_INTERVAL_SECONDS: int = 3600
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    EMAIL_FROM: str = "no-reply@online-cinema.local"
    FRONTEND_BASE_URL: str = "http://localhost:8000"
    EMAIL_ENABLED: bool = True
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "online_cinema_minio"
    S3_SECRET_KEY: str = "online_cinema_minio_password"
    S3_BUCKET_NAME: str = "online-cinema-media"
    S3_PUBLIC_BASE_URL: str = "http://localhost:9000/online-cinema-media"
    AVATAR_MAX_SIZE_BYTES: int = 2_000_000
    MOCK_PAYMENT_BASE_URL: str = "http://localhost:8000/mock-payments"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
