from typing import List

from pydantic import BaseSettings

__all__ = ["settings"]


class AppSettings(BaseSettings):
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


class Settings(AppSettings):
    ENVIRONMENT: str
    MONGO_URL: str
    ALLOW_ORIGINS: List[str] = ["http://0.0.0.0:3000"]
    TEST_MONGO_URL: str = "mongodb://test:test@0.0.0.0:27018"
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE = 60 * 5

    API_KEY: str
    API_KEY_NAME: str = "x-access-token"

    DOMAIN_SCORING: str = "0.0.0.0:8000"

    LOG_LEVEL: str = 'INFO'
    LOG_FORMAT: str = 'json'

    # S3_REGION: str = 'ru-central1'
    # S3_ENDPOINT: str = 'https://storage.yandexcloud.net'
    # S3_ACCESS_KEY: str
    # S3_SECRET_ACCESS_KEY: str
    # S3_BUCKET: str
    # MAX_FILE_SIZE: int = 52428800   # 50 Mb
    # ALLOW_FILE_EXTENSION: List[str] = [".doc", ".docx", ".pdf", ".txt", ".rtf"]


settings = Settings()
