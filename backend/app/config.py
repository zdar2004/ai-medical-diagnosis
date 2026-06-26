from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "MediSys AI"
    app_version: str = "1.0.0"
    debug: bool = True
    environment: str = "development"

    # MongoDB
    mongodb_url: str
    mongodb_db_name: str = "medisys_db"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # CORS
    allowed_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000"
    ]

    bcrypt_rounds: int = 12


    @property
    def is_production(self):
        return self.environment == "production"


    @property
    def is_development(self):
        return self.environment == "development"



@lru_cache()
def get_settings():

    return Settings()



settings = get_settings()