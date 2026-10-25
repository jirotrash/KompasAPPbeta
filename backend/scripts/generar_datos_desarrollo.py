"""Genera database/datos_desarrollo.json (BACKEND.md §5): los mismos registros que tenía datos_desarrollo.sql.

Los hashes de bcrypt se calculan aquí, nunca a mano. Correr de nuevo solo si cambian estos datos:
    python -m scripts.generar_datos_desarrollo

- Usuario administrador (dueño de los lugares de prueba; contraseña aleatoria que nadie conoce).
- Usuario demo: demo@kompas.mx / demo1234, con rol `admin` para poder abrir el dashboard.
- Categorías y transportes con los nombres de la app.
- 10 lugares GENÉRICOS "de ejemplo" dentro de la zona piloto (no son negocios reales).
- Sin rutas: solo se cargan trazos que el equipo haya recorrido.

Los ids son los mismos que asignaba MySQL (AUTO_INCREMENT en el orden de los INSERT).
"""

import json
import secrets
from datetime import date
from pathlib import Path

from app.nucleo.seguridad import hash_password

ARCHIVO = Path(__file__).resolve().parent.parent / "database" / "datos_desarrollo.json"

ADMIN = ("Administrador", "Kompás", "admin@kompas.mx")
DEMO = ("Demo", "Kompás", "demo@kompas.mx", "demo1234")

CATEGORIAS = [
    ("Comer", "Restaurantes, fondas y lugares para comer"),
    ("Café", "Cafeterías"),
    ("Cultura", "Museos, galerías y centros culturales"),
    ("Entretenimiento", "Cines, plazas y lugares de diversión"),
    ("Aire libre", "Parques y jardines"),
]

TRANSPORTES = ["Caminando", "Transporte público", "Taxi/App", "Combinado"]

# nombre, categoría, latitud, longitud
LUGARES = [
    ("Cafetería de ejemplo · Centro de Toluca", "Café", 19.292, -99.656),
    ("Restaurante familiar de ejemplo · Toluca", "Comer", 19.287, -99.64),
    ("Parque de ejemplo · Toluca", "Aire libre", 19.296, -99.662),
    ("Museo de ejemplo · Toluca", "Cultura", 19.2935, -99.658),
    ("Cine de ejemplo · Toluca oriente", "Entretenimiento", 19.28, -99.61),
    ("Cafetería de ejemplo · Centro de Lerma", "Café", 19.285, -99.5115),
    ("Fonda de ejemplo · San Mateo Atenco", "Comer", 19.2675, -99.5335),
    ("Plaza de ejemplo · Lerma", "Entretenimiento", 19.28, -99.54),
    ("Jardín de ejemplo · Lerma", "Aire libre", 19.2875, -99.514),
    ("Galería de ejemplo · Lerma", "Cultura", 19.288, -99.515),
]


def usuario(id_usuario: int, nombre: str, apellido: str, correo: str, password: str) -> dict:
    return {
        "_id": id_usuario,
        "nombre": nombre,
        "primer_apellido": apellido,
        "segundo_apellido": None,
        "correo": correo,
        "password": hash_password(password),
        "fecha_nacimiento": None,
        "rol": "admin",
        "residencia": None,
    }


def generar() -> dict:
    categorias = [{"_id": i, "nombre": n, "descripcion": d} for i, (n, d) in enumerate(CATEGORIAS, start=1)]
    por_nombre = {c["nombre"]: c["_id"] for c in categorias}
    return {
        "_nota": f"Datos SOLO para desarrollo. Generado por scripts/generar_datos_desarrollo.py el "
        f"{date.today().isoformat()}. No editar a mano. Usuario de prueba: demo@kompas.mx / demo1234",
        "usuarios": [
            # Administrador: dueño de los lugares de prueba (su contraseña es aleatoria y nadie la conoce)
            usuario(1, *ADMIN, secrets.token_urlsafe(32)),
            usuario(2, *DEMO),
        ],
        "categorias": categorias,
        "transportes": [{"_id": i, "nombre": n} for i, n in enumerate(TRANSPORTES, start=1)],
        # Lugares GENÉRICOS de ejemplo (no son negocios reales); Sebas carga los reales
        "lugares": [
            {
                "_id": i,
                "nombre": nombre,
                "ubicacion": {"type": "Point", "coordinates": [lng, lat]},
                "categoria": {"id": por_nombre[categoria], "nombre": categoria},
                "id_usuario": 1,
            }
            for i, (nombre, categoria, lat, lng) in enumerate(LUGARES, start=1)
        ],
        "rutas": [],
    }


if __name__ == "__main__":
    ARCHIVO.write_text(json.dumps(generar(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generado {ARCHIVO}")
