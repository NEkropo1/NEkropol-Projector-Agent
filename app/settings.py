from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_log_level: str = Field(default="INFO", alias="APP_LOG_LEVEL")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")

    openai_model_gpt: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL_GPT")
    openai_model_cheap: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL_CHEAP")
    google_url: str = Field(default="https://www.google.com/search?q=", alias="GOOGLE_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
