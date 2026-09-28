"""Crea el esquema desde cero: dump de Sebas (tal cual) + datos_desarrollo.sql.

Uso (desde backend/, con el venv activo):
    python -m scripts.preparar_bd              # crea el esquema de DATABASE_URL si no existe
    python -m scripts.preparar_bd --recrear    # BORRA el esquema y lo vuelve a crear
    python -m scripts.preparar_bd --sin-datos  # solo tablas, sin datos de desarrollo

Funciona con MySQL 8 y con MariaDB. Toma el nombre del esquema de DATABASE_URL, así que
sirve también para el esquema de pruebas.
"""

import argparse
import re
import sys
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import URL, create_engine, make_url, text

CARPETA_BD = Path(__file__).resolve().parent.parent / "database"
DUMP = "Dump20260927.sql"
DATOS = "datos_desarrollo.sql"


def sentencias(archivo: Path) -> Iterator[str]:
    """Separa un script en sentencias (terminan en ';' al final de la línea).
    Omite CREATE DATABASE / USE: el esquema destino lo decide DATABASE_URL."""
    pendiente: list[str] = []
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        if not pendiente and (not linea.strip() or linea.lstrip().startswith("--")):
            continue
        pendiente.append(linea)
        if linea.rstrip().endswith(";"):
            sentencia = "\n".join(pendiente).strip()
            pendiente = []
            if not re.match(r"(CREATE\s+DATABASE|USE\s)", sentencia, re.IGNORECASE):
                yield sentencia


def preparar(url: str | URL, recrear: bool = False, con_datos: bool = True, silencioso: bool = False) -> None:
    def avisar(mensaje: str) -> None:
        if not silencioso:
            print(mensaje)

    url = make_url(url)
    esquema = url.database
    if not esquema or not re.fullmatch(r"\w+", esquema):
        raise SystemExit(f"Nombre de esquema no válido en DATABASE_URL: {esquema!r}")

    servidor = create_engine(url.set(database=""))
    with servidor.connect() as conexion:
        tablas = conexion.scalar(
            text("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = :e"), {"e": esquema}
        )
        if tablas and not recrear:
            raise SystemExit(f"El esquema `{esquema}` ya tiene {tablas} tablas. Usa --recrear para borrarlo y crearlo de nuevo.")
        conexion.exec_driver_sql(f"DROP DATABASE IF EXISTS `{esquema}`")
        conexion.exec_driver_sql(f"CREATE DATABASE `{esquema}` CHARACTER SET utf8mb4")
    servidor.dispose()
    avisar(f"Esquema `{esquema}` creado.")

    archivos = [DUMP, DATOS] if con_datos else [DUMP]
    motor = create_engine(url)
    with motor.begin() as conexion:
        for nombre in archivos:
            for sentencia in sentencias(CARPETA_BD / nombre):
                conexion.exec_driver_sql(sentencia)
            avisar(f"  ✓ {nombre}")
    if con_datos:
        avisar("Usuario de prueba: demo@kompas.mx / demo1234")
    motor.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--recrear", action="store_true", help="borra el esquema si ya existe")
    parser.add_argument("--sin-datos", action="store_true", help="no carga los datos de desarrollo")
    args = parser.parse_args()

    from app.config import get_settings

    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    preparar(get_settings().database_url, recrear=args.recrear, con_datos=not args.sin_datos)


if __name__ == "__main__":
    main()
