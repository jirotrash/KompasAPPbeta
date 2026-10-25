"""Claves de texto que usa la app: nombre de catálogo → valor (comer, cafe, taxi_app…)."""

import re
import unicodedata

INTERESES = ("comer", "cafe", "cultura", "entretenimiento", "aire_libre")
MOVILIDADES = ("caminando", "transporte_publico", "taxi_app", "combinado")


def clave(nombre: str) -> str:
    """Nombre del catálogo → valor que usa la app: "Café" → "cafe", "Taxi/App" → "taxi_app"."""
    sin_acentos = unicodedata.normalize("NFD", nombre).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", sin_acentos.lower()).strip("_")


def interes_de(nombre_categoria: str | None) -> str | None:
    """Nombre de la categoría → interés de la app, o None si no es uno de los cinco."""
    if nombre_categoria is None:
        return None
    valor = clave(nombre_categoria)
    return valor if valor in INTERESES else None
