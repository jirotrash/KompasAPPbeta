"""Configuración leída de variables de entorno o de backend/.env (ver .env.example)."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/.env, sin importar desde qué carpeta se levante uvicorn
ARCHIVO_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ARCHIVO_ENV, env_file_encoding="utf-8", extra="ignore")

    # MongoDB local (mongodb://localhost:27017) o Atlas (mongodb+srv://...): solo cambia esta variable
    mongo_uri: str
    mongo_db: str = "kompas"
    jwt_secret: str
    jwt_expira_minutos: int = 60 * 24 * 7
    cors_origins: str = "*"
    # Google Places API (New). Sin llave, POST /api/itinerarios responde 503 (no se inventan lugares)
    google_maps_api_key: str | None = None
    google_idioma: str = "es"
    google_region: str = "mx"
    # Asistente con LLM local (Ollama corre en la misma PC que la API). El modelo debe soportar tools
    ollama_url: str = "http://localhost:11434"
    ollama_modelo: str = "llama3.2:3b"

    @property
    def lista_cors(self) -> list[str]:
        """"*" o una lista separada por comas: http://localhost:8081,http://192.168.1.50:8081"""
        return [origen.strip() for origen in self.cors_origins.split(",") if origen.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
