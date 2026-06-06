from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8"
  )
  db_user: str
  db_password: str
  db_host: str
  db_port: str
  db_name: str
  # SECRET_KEY
  secret_key: SecretStr
  algorithm: str = "HS256"
  access_token_expire_minutes: int = 30

settings = Settings() #loaded from the .env file