from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"))

    groq_api_key: str
    groq_model: str = "openai/gpt-oss-120b"
    port: int = 7860


settings = Settings()
