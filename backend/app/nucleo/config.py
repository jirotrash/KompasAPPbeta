"""Configuración leída de variables de entorno o de backend/.env (ver .env.example)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/.env, sin importar desde qué carpeta se levante uvicorn
ARCHIVO_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ARCHIVO_ENV, env_file_encoding="utf-8", extra="ignore")

    # Dos bases con el mismo esquema: la local (MONGO_URI/MONGO_DB) y la de Atlas (MONGO_URI_ATLAS/MONGO_DB_ATLAS).
    # MONGO_DESTINO elige con cuál trabaja esta API. Para usar las dos a la vez se levantan dos APIs (README).
    mongo_destino: Literal["local", "atlas"] = "local"
    mongo_uri: str
    mongo_db: str = "kompas"
    mongo_uri_atlas: str | None = None
    mongo_db_atlas: str = "kompasbd"
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

    @model_validator(mode="after")
    def _atlas_configurado(self) -> "Settings":
        if self.mongo_destino == "atlas" and not self.mongo_uri_atlas:
            raise ValueError("MONGO_DESTINO=atlas necesita MONGO_URI_ATLAS en backend/.env")
        return self

    @property
    def uri_activa(self) -> str:
        return self.mongo_uri_atlas if self.mongo_destino == "atlas" else self.mongo_uri

    @property
    def bd_activa(self) -> str:
        return self.mongo_db_atlas if self.mongo_destino == "atlas" else self.mongo_db

    @property
    def lista_cors(self) -> list[str]:
        """"*" o una lista separada por comas: http://localhost:8081,http://192.168.1.50:8081"""
        return [origen.strip() for origen in self.cors_origins.split(",") if origen.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
