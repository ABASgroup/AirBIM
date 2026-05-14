"""API configuration."""
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


# import these to get the configurations
api_config = APIConfig()  # type: ignore
