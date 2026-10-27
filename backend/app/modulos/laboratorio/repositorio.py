"""Escribe en `bitacora_laboratorio`: un documento por consulta a las demostraciones (campo `tipo`)."""

from pymongo.database import Database

from app.nucleo.bd import ahora


class RepositorioBitacora:
    def __init__(self, bd: Database):
        self.bd = bd

    def registrar(self, tipo: str, datos: dict) -> None:
        self.bd.bitacora_laboratorio.insert_one({"tipo": tipo, "creado_en": ahora(), **datos})
