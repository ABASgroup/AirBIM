"""Celery configuration."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# path to the env file
BASE_DIR = Path(__file__).resolve().parents[3]
ENV_PATH = BASE_DIR / '.env'


class CeleryConfig(BaseSettings):
    """Celery configuration parameters."""
    NAME: str = "celery"

    BROKER_URL: str
    BROKER_PASSWORD: str

    BACKEND_URL: str
    BACKEND_PASSWORD: str

    SERIALIZER: str = "json"

    # 1 hour
    RESULT_EXPIRES: int = 3600

    TIMEZONE: str = "UTC"

    model_config = SettingsConfigDict(env_file=ENV_PATH,
                                      env_file_encoding='utf-8',
                                      extra='ignore')


celery_config = CeleryConfig()  # type: ignore
