from pydantic_settings import BaseSettings
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: str = "*"

    # Email SMTP
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_SENDER: str
    SMTP_TLS: bool = True

    # OTP expiry
    OTP_EXPIRE_MINUTES: int = 10

    # Password reset token expiry (if using token after OTP)
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15

    # Super user key for super‑key login (bypasses normal auth)
    SUPER_USER_KEY: str
    SUPER_USER_EMAIL: str = "superadmin@icios.in"  # default, can be overridden in .env

    model_config = {
        "env_file": os.path.join(BASE_DIR, ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

settings = Settings()