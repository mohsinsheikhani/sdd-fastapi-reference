from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql://user:password@localhost:5432/taskapi"
    secret_key: str = "your-super-secret-key-min-32-chars-long"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7


settings = Settings()
