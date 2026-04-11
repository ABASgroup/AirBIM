"""Database configuration."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# path to the env file
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / '.env'


class DatabaseConfig(BaseSettings):
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


database_config = DatabaseConfig()  # type: ignore
