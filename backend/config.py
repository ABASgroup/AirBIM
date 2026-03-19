"""App configurations for backend."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# path to the env file
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / '.env'


class APIConfig(BaseSettings):
    """API configuration parameters."""
    API_HOST: str = Field(default='0.0.0.0')
    API_PORT: int = Field(default=8000)

    JWT_SECRET_KEY: str
    JWT_EXPIRE_MINUTES: int = 60
    JWT_ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(env_file=ENV_PATH,
                                      env_file_encoding='utf-8',
                                      extra='ignore')


class StorageConfig(BaseSettings):
    """S3 Storage configuration parameters."""
    # username
    STORAGE_ACCESS_KEY: str
    # password
    STORAGE_SECRET_KEY: str
    STORAGE_PORT: int
    BUCKET_NAME: str = "airbim"

    model_config = SettingsConfigDict(env_file=ENV_PATH,
                                      env_file_encoding='utf-8',
                                      extra='ignore')

    @property
    def endpoint(self) -> str:
        """Endpoint for connection."""
        return (f"http://localhost:{self.STORAGE_PORT}")


class DBConfig(BaseSettings):
    """Database configuration parameters."""
    DB_HOST: str
    DB_NAME: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str

    model_config = SettingsConfigDict(env_file=ENV_PATH,
                                      env_file_encoding='utf-8',
                                      extra='ignore')

    @property
    def db_url(self) -> str:
        """Database URL."""
        return (f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")


# import these to get the configurations
api_config = APIConfig()  # type: ignore
db_config = DBConfig()  # type: ignore
storage_config = StorageConfig()  # type: ignore
