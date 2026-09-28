"""Genera database/datos_desarrollo.sql (BACKEND.md §5): solo INSERTs, sin tocar la estructura.

Los hashes de bcrypt se calculan aquí, nunca a mano. Correr de nuevo solo si cambian estos datos:
    python -m scripts.generar_datos_desarrollo

- Usuario administrador (dueño de los lugares de prueba; contraseña aleatoria que nadie conoce).
- Usuario demo: demo@kompas.mx / demo1234.
- Categorías y transportes con los nombres de la app.
- 10 lugares GENÉRICOS "de ejemplo" dentro de la zona piloto (no son negocios reales).
- Sin rutas: solo se cargan trazos que el equipo haya recorrido.
"""

import secrets
from datetime import date
from pathlib import Path

from app.seguridad import hash_password

ARCHIVO = Path(__file__).resolve().parent.parent / "database" / "datos_desarrollo.sql"

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


def texto(valor: str) -> str:
    return "'" + valor.replace("\\", "\\\\").replace("'", "''") + "'"


def generar() -> str:
    lineas = [
        "-- Datos SOLO para desarrollo (BACKEND.md §5). Solo INSERTs: no modifica la estructura.",
        f"-- Generado por scripts/generar_datos_desarrollo.py el {date.today().isoformat()}. No editar a mano.",
        "-- Se puede ejecutar varias veces: no duplica registros.",
        "-- Usuario de prueba: demo@kompas.mx / demo1234",
        "",
        "INSERT IGNORE INTO categorias (nombre, descripcion) VALUES",
        ",\n".join(f"  ({texto(n)}, {texto(d)})" for n, d in CATEGORIAS) + ";",
        "",
        "INSERT IGNORE INTO transportes (nombre) VALUES",
        ",\n".join(f"  ({texto(n)})" for n in TRANSPORTES) + ";",
        "",
        "-- Administrador: dueño de los lugares de prueba (su contraseña es aleatoria y nadie la conoce)",
        "INSERT IGNORE INTO usuarios (nombre, primer_apellido, correo, password) VALUES",
        f"  ({texto(ADMIN[0])}, {texto(ADMIN[1])}, {texto(ADMIN[2])}, {texto(hash_password(secrets.token_urlsafe(32)))}),",
        f"  ({texto(DEMO[0])}, {texto(DEMO[1])}, {texto(DEMO[2])}, {texto(hash_password(DEMO[3]))});",
        "",
        "-- Lugares GENÉRICOS de ejemplo (no son negocios reales); Sebas carga los reales",
    ]
    for nombre, categoria, lat, lng in LUGARES:
        lineas += [
            "INSERT INTO lugares_de_interes (nombre, latitud, longitud, id_usuario, id_cat)",
            f"SELECT {texto(nombre)}, {lat}, {lng}, u.id_usuario, c.id_categoria",
            f"FROM usuarios u JOIN categorias c ON c.nombre = {texto(categoria)}",
            f"WHERE u.correo = {texto(ADMIN[2])}",
            f"  AND NOT EXISTS (SELECT 1 FROM lugares_de_interes l WHERE l.nombre = {texto(nombre)});",
            "",
        ]
    return "\n".join(lineas)


if __name__ == "__main__":
    ARCHIVO.write_text(generar(), encoding="utf-8")
    print(f"Generado {ARCHIVO}")
