"""Acceso a la colección `conversaciones`. El _id es ObjectId; hacia afuera siempre se regresa como texto.

Los mensajes se agregan con $push; las rutas consultadas y los planes creados sin repetir.
"""

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.database import Database

from app.nucleo.bd import ahora


def _oid(id_conversacion: str) -> ObjectId | None:
    try:
        return ObjectId(id_conversacion)
    except (InvalidId, TypeError):
        return None


def _conversacion(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "id_usuario": doc["id_usuario"],
        "titulo": doc.get("titulo"),
        "modelo": doc.get("modelo", ""),
        "mensajes": doc.get("mensajes", []),
        "rutas_consultadas": doc.get("rutas_consultadas", []),
        "planes_creados": doc.get("planes_creados", []),
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


class RepositorioConversaciones:
    def __init__(self, bd: Database):
        self.bd = bd

    def _filtro(self, id_conversacion: str, id_usuario: int) -> dict | None:
        oid = _oid(id_conversacion)
        return {"_id": oid, "id_usuario": id_usuario, "deleted_at": None} if oid else None

    def crear(self, id_usuario: int, modelo: str) -> dict:
        momento = ahora()
        doc = {
            "id_usuario": id_usuario,
            "titulo": None,
            "modelo": modelo,
            "mensajes": [],
            "rutas_consultadas": [],
            "planes_creados": [],
            "created_at": momento,
            "updated_at": momento,
            "deleted_at": None,
        }
        doc["_id"] = self.bd.conversaciones.insert_one(doc).inserted_id
        return _conversacion(doc)

    def por_id(self, id_conversacion: str, id_usuario: int) -> dict | None:
        """Solo si es del usuario y no está borrada (la de otro usuario es None, igual que una inexistente)."""
        filtro = self._filtro(id_conversacion, id_usuario)
        doc = self.bd.conversaciones.find_one(filtro) if filtro else None
        return _conversacion(doc) if doc else None

    def listar(self, id_usuario: int) -> list[dict]:
        consulta = self.bd.conversaciones.find(
            {"id_usuario": id_usuario, "deleted_at": None},
            {"titulo": 1, "updated_at": 1, "total": {"$size": "$mensajes"}, "ultimos": {"$slice": ["$mensajes", -4]}},
        ).sort("updated_at", -1)
        salida = []
        for doc in consulta:
            visibles = [m for m in doc.get("ultimos", []) if m.get("rol") in ("usuario", "asistente") and m.get("contenido")]
            salida.append(
                {
                    "id": str(doc["_id"]),
                    "titulo": doc.get("titulo"),
                    "ultimo_mensaje": visibles[-1]["contenido"][:160] if visibles else None,
                    "fecha": doc["updated_at"],
                    "total_mensajes": doc.get("total", 0),
                }
            )
        return salida

    def agregar_mensaje(self, id_conversacion: str, mensaje: dict, titulo: str | None = None) -> None:
        cambios: dict = {"updated_at": ahora()}
        if titulo:
            cambios["titulo"] = titulo
        self.bd.conversaciones.update_one({"_id": _oid(id_conversacion)}, {"$push": {"mensajes": mensaje}, "$set": cambios})

    def agregar_ruta(self, id_conversacion: str, ruta: dict) -> None:
        """Sin repetir la misma ruta (mismo id, origen, destino y transporte); se conserva la primera consulta."""
        igual = {k: ruta[k] for k in ("id_ruta", "origen", "destino", "transporte")}
        self.bd.conversaciones.update_one(
            {"_id": _oid(id_conversacion), "rutas_consultadas": {"$not": {"$elemMatch": igual}}},
            {"$push": {"rutas_consultadas": ruta}},
        )

    def agregar_plan(self, id_conversacion: str, id_plan: int) -> None:
        self.bd.conversaciones.update_one({"_id": _oid(id_conversacion)}, {"$addToSet": {"planes_creados": id_plan}})

    def borrar(self, id_conversacion: str, id_usuario: int) -> bool:
        """Borrado lógico. False si no existe o es de otro usuario."""
        filtro = self._filtro(id_conversacion, id_usuario)
        if not filtro:
            return False
        momento = ahora()
        return self.bd.conversaciones.update_one(filtro, {"$set": {"deleted_at": momento, "updated_at": momento}}).modified_count == 1
