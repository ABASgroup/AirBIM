"""S3 Storage configuration."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# path to the env file
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / '.env'


class StorageConfig(BaseSettings):
    """S3 Storage configuration parameters."""
    # username
    STORAGE_ACCESS_KEY_ID: str
    # password
    STORAGE_SECRET_KEY: str
    STORAGE_PORT_INTERNAL: int
    STORAGE_BUCKET: str = "airbim"
    STORAGE_INTERNAL_ENDPOINT: str
    STORAGE_EXTERNAL_ENDPOINT: str

    # for presigned urls
    STORAGE_URL_EXP_TIME: int = 60

    model_config = SettingsConfigDict(env_file=ENV_PATH,
                                      env_file_encoding='utf-8',
                                      extra='ignore')


storage_config = StorageConfig()  # type: ignore
