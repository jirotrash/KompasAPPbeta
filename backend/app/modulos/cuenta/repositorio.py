"""Acceso a la colección `usuarios` (la residencia va embebida en el usuario)."""

from datetime import date, datetime, time

from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.nucleo.bd import ZONA_HORARIA, ahora, siguiente_id

CAMPOS_RESIDENCIA = ("calle", "numero_interior", "numero_exterior", "municipio", "colonia", "estado")


def _a_fecha(valor: datetime | None) -> date | None:
    """fecha_nacimiento se guarda como datetime a las 00:00 (hora de Toluca) y se regresa como date."""
    return valor.astimezone(ZONA_HORARIA).date() if valor is not None else None


def _de_fecha(valor: date | None) -> datetime | None:
    return datetime.combine(valor, time.min, tzinfo=ZONA_HORARIA) if valor is not None else None


def _usuario(doc: dict) -> dict:
    return {
        "id": doc["_id"],
        "nombre": doc["nombre"],
        "primer_apellido": doc["primer_apellido"],
        "segundo_apellido": doc.get("segundo_apellido"),
        "correo": doc["correo"],
        "password": doc["password"],
        "fecha_nacimiento": _a_fecha(doc.get("fecha_nacimiento")),
        "rol": doc.get("rol") or "usuario",
    }


def _residencia(r: dict) -> dict:
    return {"id": r["id"], **{c: r.get(c) for c in CAMPOS_RESIDENCIA}}


class RepositorioCuenta:
    def __init__(self, bd: Database):
        self.bd = bd

    def por_id(self, id_usuario: int) -> dict | None:
        doc = self.bd.usuarios.find_one({"_id": id_usuario, "deleted_at": None})
        return _usuario(doc) if doc else None

    def por_correo(self, correo: str) -> dict | None:
        doc = self.bd.usuarios.find_one({"correo": correo, "deleted_at": None})
        return _usuario(doc) if doc else None

    def existe_correo(self, correo: str) -> bool:
        """Incluye cuentas borradas: el índice único de `correo` no permite repetirlo."""
        return self.bd.usuarios.count_documents({"correo": correo}, limit=1) > 0

    def crear(self, datos: dict) -> dict | None:
        """Inserta el usuario con rol `usuario`. None si el correo ya existe (dos registros simultáneos)."""
        momento = ahora()
        doc = {
            "_id": siguiente_id(self.bd, "usuarios"),
            "nombre": datos["nombre"],
            "primer_apellido": datos["primer_apellido"],
            "segundo_apellido": datos.get("segundo_apellido"),
            "correo": datos["correo"],
            "password": datos["password"],
            "fecha_nacimiento": _de_fecha(datos.get("fecha_nacimiento")),
            "rol": "usuario",
            "residencia": None,
            "created_at": momento,
            "updated_at": momento,
            "deleted_at": None,
        }
        try:
            self.bd.usuarios.insert_one(doc)
        except DuplicateKeyError:
            return None
        return _usuario(doc)

    def residencia(self, id_usuario: int) -> dict | None:
        doc = self.bd.usuarios.find_one({"_id": id_usuario, "deleted_at": None}, {"residencia": 1})
        r = (doc or {}).get("residencia")
        return _residencia(r) if r else None

    def guardar_residencia(self, id_usuario: int, campos: dict) -> dict:
        """Actualiza la residencia embebida; si no existe, la crea con un id nuevo."""
        actual = self.residencia(id_usuario)
        id_residencia = actual["id"] if actual else siguiente_id(self.bd, "residencia")
        residencia = {"id": id_residencia, **{c: campos.get(c) for c in CAMPOS_RESIDENCIA}}
        self.bd.usuarios.update_one({"_id": id_usuario}, {"$set": {"residencia": residencia, "updated_at": ahora()}})
        return _residencia(residencia)

    def poner_rol(self, correo: str, rol: str) -> bool:
        resultado = self.bd.usuarios.update_one(
            {"correo": correo, "deleted_at": None}, {"$set": {"rol": rol, "updated_at": ahora()}}
        )
        return resultado.matched_count > 0

    def contar(self) -> int:
        return self.bd.usuarios.count_documents({"deleted_at": None})
