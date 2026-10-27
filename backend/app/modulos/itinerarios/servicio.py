"""Botón **Crear mi plan**: zona → catálogos → Google Places → sistema experto → orden de paradas → guardar.

La IA (`app.ia.servicio.recomendar`) no se toca: aquí solo se le pasan los datos y se guarda lo que regresa.
Después, el algoritmo genético (`app.ia.orden_optimizado`) pone las paradas de cada plan en el orden más
corto sin cambiar lo que decidió el sistema experto.
"""

from datetime import datetime

from app.compartido.geo import ZONA, ahora_mexico, esta_dentro_de_zona
from app.compartido.traslados import radio_km
from app.externos import google_places
from app.ia.orden_optimizado import optimizar_orden
from app.ia.servicio import recomendar
from app.modulos.catalogos.servicio import ServicioCatalogos
from app.modulos.laboratorio.servicio import ServicioLaboratorio
from app.modulos.itinerarios.repositorio import RepositorioPlanes
from app.nucleo.errores import DatosInvalidos, ErrorDeDatos, ServicioExterno

# BACKEND.md §4: contexto → no_acompanantes
ACOMPANANTES = {"solo": 0, "pareja": 1, "amigos": 3, "familia": 3}


def evaluacion_de(respuesta: dict) -> dict:
    """Resumen de lo que ya regresó `recomendar()` para guardarlo en el plan (no se recalcula nada)."""
    candidatos = [
        {
            "tipo": p["tipo"],
            "estado": p["estado"],
            "puntuacion": p["puntuacion"],
            "reglas": [r["id"] for r in p["reglas_cumplidas"]],
        }
        for p in respuesta["planes"]
    ] + [
        {"tipo": d["tipo"], "estado": d["estado"], "puntuacion": None, "reglas": [r["id"] for r in d["reglas"]]}
        for d in respuesta["descartados"]
    ]
    return {
        "version_reglas": respuesta.get("version_reglas"),
        "datos_suficientes": respuesta["datos_suficientes"],
        "candidatos": candidatos,
    }


class ServicioItinerarios:
    def __init__(self, repo: RepositorioPlanes, catalogos: ServicioCatalogos, bitacora: ServicioLaboratorio | None = None):
        self.repo = repo
        self.catalogos = catalogos
        self.bitacora = bitacora

    def crear(self, usuario: dict, peticion: dict) -> dict:
        return self.crear_y_guardar(usuario, peticion)[0]

    def crear_y_guardar(self, usuario: dict, peticion: dict, origen_solicitud: str = "planificador") -> tuple[dict, int]:
        """(respuesta para la app, id del plan guardado). `origen_solicitud`: planificador | asistente."""
        origen = peticion["origen"]
        if not esta_dentro_de_zona(origen):
            raise DatosInvalidos(f"El punto de partida está fuera de la zona piloto ({ZONA['nombre']}).")

        # Se busca antes de llamar al motor: si faltan en la BD, es un error de datos y no se debe responder a medias
        categoria = self.catalogos.categoria_por_clave(peticion["intereses"][0])
        transporte = self.catalogos.transporte_por_clave(peticion["movilidad"][0])
        if categoria is None or transporte is None:
            raise ErrorDeDatos("Faltan categorías o transportes en la base de datos. Carga database/datos_desarrollo.sql.")

        try:
            lugares = google_places.buscar_para_plan(origen, peticion["intereses"], radio_km(peticion["movilidad"]))
        except google_places.ErrorGooglePlaces as error:
            raise ServicioExterno(str(error)) from error
        momento = ahora_mexico()
        respuesta = recomendar(peticion, lugares, momento)
        for ejecucion in optimizar_orden(respuesta, peticion, lugares, momento):
            if self.bitacora:
                self.bitacora.registrar("genetico", ejecucion)

        hora, minuto = (int(x) for x in peticion["hora_salida"].split(":"))
        hoy = ahora_mexico()
        id_plan = self.repo.guardar(
            {
                "id_usuario": usuario["id"],
                "contexto": peticion["contexto"],
                "no_acompanantes": ACOMPANANTES[peticion["contexto"]],
                "presupuesto": {"min": peticion["presupuesto"]["min"], "max": peticion["presupuesto"]["max"]},
                "tiempo_disponible": round(peticion["tiempo_horas"] * 60),
                "intereses": list(peticion["intereses"]),
                "movilidad": list(peticion["movilidad"]),
                "categoria": {"id": categoria["id"], "nombre": categoria["nombre"]},
                "transporte": {"id": transporte["id"], "nombre": transporte["nombre"]},
                "hora_salida": peticion["hora_salida"],
                "fecha_plan": datetime.combine(hoy.date(), datetime.min.time(), hoy.tzinfo).replace(hour=hora, minute=minuto),
                "evaluacion": evaluacion_de(respuesta),
                "origen_solicitud": origen_solicitud,
                # No se guarda el origen exacto del usuario (privacidad)
            }
        )
        return respuesta, id_plan

    def del_usuario(self, usuario: dict) -> list[dict]:
        return self.repo.del_usuario(usuario["id"])
