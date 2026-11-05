"""Acceso a la colección `planes`: lo que eligió el usuario y la evaluación del sistema experto."""

from pymongo import ReturnDocument
from pymongo.database import Database

from app.nucleo.bd import ahora, hora_local, siguiente_id


def _plan_guardado(doc: dict) -> dict:
    """Ficha sin datos internos; completa con valores seguros los registros anteriores."""
    return {
        "id": doc["_id"],
        "no_acompanantes": doc["no_acompanantes"],
        "tiempo_disponible": doc["tiempo_disponible"],
        "categoria": doc["categoria"]["nombre"],
        "transporte": doc["transporte"]["nombre"],
        "fecha_plan": hora_local(doc.get("fecha_plan")),
        "creado_en": hora_local(doc.get("created_at")),
        "titulo": doc.get("titulo") or "Plan de salida",
        "estado_usuario": doc.get("estado_usuario", "borrador"),
        "tipo_seleccionado": doc.get("tipo_seleccionado"),
        "tiene_detalle": bool(doc.get("opciones_guardadas")),
        "alternativas": [
            {"tipo": opcion["tipo"], "numero_paradas": len(opcion["paradas"])}
            for opcion in doc.get("opciones_guardadas", [])
        ],
        "actualizado_en": hora_local(doc.get("updated_at")),
    }


class RepositorioPlanes:
    def __init__(self, bd: Database):
        self.bd = bd

    def guardar(self, plan: dict) -> int:
        """`plan` trae los campos de MIGRACION_MONGODB.md §3.4; aquí se agregan id y fechas."""
        momento = ahora()
        doc = {
            "_id": siguiente_id(self.bd, "planes"),
            **plan,
            "created_at": momento,
            "updated_at": momento,
            "deleted_at": None,
        }
        self.bd.planes.insert_one(doc)
        return doc["_id"]

    def del_usuario(self, id_usuario: int, limite: int = 50, antes_de: int | None = None) -> list[dict]:
        """Del más reciente al más antiguo."""
        filtro = {"id_usuario": id_usuario, "deleted_at": None}
        if antes_de is not None:
            filtro["_id"] = {"$lt": antes_de}
        consulta = self.bd.planes.find(filtro).sort("_id", -1).limit(limite)
        return [_plan_guardado(d) for d in consulta]

    def por_id(self, id_plan: int, id_usuario: int) -> dict | None:
        doc = self.bd.planes.find_one({"_id": id_plan, "id_usuario": id_usuario, "deleted_at": None})
        if doc is None:
            return None
        # Modelo de dominio; no se filtra el documento Mongo a la API.
        return {
            **_plan_guardado(doc),
            "contexto": doc.get("contexto"),
            "presupuesto": doc.get("presupuesto"),
            "intereses": doc.get("intereses", []),
            "movilidad": doc.get("movilidad", []),
            "opciones_guardadas": doc.get("opciones_guardadas", []),
        }

    def actualizar(self, id_plan: int, id_usuario: int, cambios: dict) -> dict | None:
        doc = self.bd.planes.find_one_and_update(
            {"_id": id_plan, "id_usuario": id_usuario, "deleted_at": None},
            {"$set": {**cambios, "updated_at": ahora()}},
            return_document=ReturnDocument.AFTER,
        )
        return _plan_guardado(doc) if doc else None

    def borrar(self, id_plan: int, id_usuario: int) -> bool:
        momento = ahora()
        resultado = self.bd.planes.update_one(
            {"_id": id_plan, "id_usuario": id_usuario, "deleted_at": None},
            {"$set": {"deleted_at": momento, "updated_at": momento}},
        )
        return resultado.matched_count == 1
