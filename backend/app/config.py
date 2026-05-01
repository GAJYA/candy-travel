from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = "dev"
    app_version: str = "0.1.0"

    database_url: str = "postgresql+asyncpg://candy:candy@localhost:5432/candy"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-in-prod"
    jwt_expire_days: int = 7

    wechat_appid: str = ""
    wechat_appsecret: str = ""


settings = Settings()
