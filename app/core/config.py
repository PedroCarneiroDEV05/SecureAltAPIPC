from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "Sistema de Autenticação"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None
    FRONTEND_URL: str = "http://localhost:3000"

    ADMIN_EMAIL: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def apply_environment_defaults(self):
        if str(self.ENVIRONMENT).lower() == "development":
            if not self.ADMIN_EMAIL or not str(self.ADMIN_EMAIL).strip():
                self.ADMIN_EMAIL = "pedrocarneiro.dev@gmail.com"
        return self


settings = Settings()
