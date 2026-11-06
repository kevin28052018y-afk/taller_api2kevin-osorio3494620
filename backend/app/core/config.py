from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Con valor por defecto la app arranca aunque falte la variable;
    # si Atlas no responde, lo verás en los logs y en /health.
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "tienda_db"

    # JWT (proyecto de estudio: clave simple)
    SECRET_KEY: str = "clave-de-estudio"
    TOKEN_MINUTOS: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
