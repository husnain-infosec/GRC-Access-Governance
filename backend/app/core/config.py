from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    CORS_ALLOWED_ORIGIN: str = "http://localhost:5173"

    class Config:
        env_file = str(ENV_PATH)

settings = Settings()