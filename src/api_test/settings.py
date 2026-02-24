"""
Este arquivo centraliza as configurações da aplicação.
A ideia é carregar variáveis do ambiente e do .env em um único ponto,
facilitando importação e manutenção em todo o projeto.
"""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    proraf_api_base_url: str = os.getenv("PRORAF_API_BASE_URL") or os.getenv("API_BASE_URL") or "https://proraf.cloud/api"
    proraf_api_key: str = os.getenv("PRORAF_API_KEY") or os.getenv("API_KEY") or ""
    proraf_secret_key: str = os.getenv("PRORAF_SECRET_KEY") or os.getenv("SECRET_KEY") or "your-secret-key-here-change-in-production-32-chars-min"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
