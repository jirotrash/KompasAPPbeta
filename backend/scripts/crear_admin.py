"""Da rol `admin` a un usuario (puede abrir el dashboard).

Uso (desde backend/, con el venv activo):
    python -m scripts.crear_admin correo@dominio.com
    python -m scripts.crear_admin correo@dominio.com --quitar   # lo regresa a rol `usuario`
"""

import argparse
import sys

from app.modulos.cuenta.repositorio import RepositorioCuenta
from app.nucleo.bd import get_bd


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("correo")
    parser.add_argument("--quitar", action="store_true", help="quita el rol admin")
    args = parser.parse_args()

    correo = args.correo.strip().lower()
    rol = "usuario" if args.quitar else "admin"
    if not RepositorioCuenta(get_bd()).poner_rol(correo, rol):
        sys.exit(f"No existe una cuenta activa con el correo {correo}.")
    print(f"{correo} ahora tiene rol `{rol}`.")


if __name__ == "__main__":
    main()
