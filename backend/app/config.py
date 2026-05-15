from pydantic import AliasChoices, Field
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

    tencent_map_key: str = Field(default="", validation_alias="TENCENT_MAP_KEY")

    ai_base_url: str = Field(
        default="",
        validation_alias=AliasChoices("AI_BASE_URL", "baseURL"),
    )
    ai_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("AI_API_KEY", "apiKey"),
    )
    ai_model: str = Field(default="gpt-5.5", validation_alias="AI_MODEL")
    ai_reasoning_effort: str = Field(default="low", validation_alias="AI_REASONING_EFFORT")
    ai_timeout_seconds: int = Field(default=60, validation_alias="AI_TIMEOUT_SECONDS")
    ai_max_images: int = Field(default=6, validation_alias="AI_MAX_IMAGES")
    ai_max_image_mb: int = Field(default=8, validation_alias="AI_MAX_IMAGE_MB")
    ai_max_total_image_mb: int = Field(default=24, validation_alias="AI_MAX_TOTAL_IMAGE_MB")


settings = Settings()
