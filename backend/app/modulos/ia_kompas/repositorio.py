"""Lectura de `historial_rutas` para aprender hábitos. Solo lee; el esquema es el del módulo historial."""

from pymongo.database import Database

from app.nucleo.bd import ZONA_HORARIA

# Los hábitos recientes pesan más que los de hace meses; también acota el costo de la validación
LIMITE_VIAJES = 300


class RepositorioHabitos:
    def __init__(self, bd: Database):
        self.bd = bd

    def viajes_del_usuario(self, id_usuario: int, limite: int = LIMITE_VIAJES) -> list[dict]:
        """Recorridos del usuario, del más reciente al más antiguo: {id_ruta, transporte, momento}."""
        consulta = (
            self.bd.historial_rutas.find(
                {"id_usuario": id_usuario, "deleted_at": None, "created_at": {"$ne": None}},
                {"id_ruta": 1, "transporte": 1, "created_at": 1},
            )
            .sort("_id", -1)
            .limit(limite)
        )
        return [
            {
                "id_ruta": d["id_ruta"],
                "transporte": (d.get("transporte") or {}).get("nombre") or "Sin dato",
                "momento": d["created_at"].astimezone(ZONA_HORARIA),
            }
            for d in consulta
        ]
