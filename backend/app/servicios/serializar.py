"""Filas de MySQL → diccionarios con la forma que espera la app (src/types/dominio.ts).

La base no tiene horario, costo, calificación ni foto de los lugares: van en null (no se inventan).
Estos mismos diccionarios son la entrada del sistema experto (ia/motor.py).
"""

import re
import unicodedata

from app import modelos
from app.servicios.geo import geo_punto

INTERESES = ("comer", "cafe", "cultura", "entretenimiento", "aire_libre")
MOVILIDADES = ("caminando", "transporte_publico", "taxi_app", "combinado")


def clave(nombre: str) -> str:
    """Nombre del catálogo → valor que usa la app: "Café" → "cafe", "Taxi/App" → "taxi_app"."""
    sin_acentos = unicodedata.normalize("NFD", nombre).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", sin_acentos.lower()).strip("_")


def interes_de(categoria: modelos.Categoria | None) -> str | None:
    if categoria is None:
        return None
    valor = clave(categoria.nombre)
    return valor if valor in INTERESES else None


def lugar(l: modelos.Lugar) -> dict:
    return {
        "_id": str(l.id_lugar),
        "id": l.id_lugar,
        "nombre": l.nombre,
        "lat": l.latitud,
        "lng": l.longitud,
        "ubicacion": geo_punto(l.latitud, l.longitud),
        "categoria": l.categoria.nombre if l.categoria else None,
        "interes": interes_de(l.categoria),
        # Campos que la app muestra y la base todavía no tiene
        "horario": None,
        "costo_promedio": None,
        "calificacion": None,
        "afluencia": None,
        "foto_url": None,
        "contextos": [],
    }


def ruta(r: modelos.Ruta) -> dict:
    return {"id": r.id_ruta, "_id": str(r.id_ruta), "trazo": r.ruta}


def residencia(r: modelos.Residencia) -> dict:
    campos = ("calle", "numero_interior", "numero_exterior", "municipio", "colonia", "estado")
    return {"id": r.id_residencia, **{c: getattr(r, c) for c in campos}}
