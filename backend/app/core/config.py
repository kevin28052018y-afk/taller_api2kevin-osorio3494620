from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MONGODB_URL: str
    MONGODB_DB_NAME: str = "tienda_db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
