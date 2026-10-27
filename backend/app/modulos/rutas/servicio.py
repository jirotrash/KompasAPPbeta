"""Rutas guardadas y alternativas de la pantalla Buscar (estimaciones por distancia).

Opciones en autobús (por dentro, sin mostrar el algoritmo):
- directa: una ruta de Kompás pasa a ≤ 400 m del origen y, más adelante en su trazo, del destino.
  Dónde subir y dónde bajar salen del árbol binario de paradas de la ruta (mas_cercano por km).
- combinada: si ninguna ruta sola conecta, A* busca una combinación con transbordo sobre los trazos.
  Si no hay combinación posible no se agrega nada (no se inventa una ruta).
"""

from app.compartido.geo import (
    ESPERA_TAXI_MIN,
    VELOCIDAD_AUTO_KMH,
    Coordenada,
    distancia_por_calles_km,
    esta_dentro_de_zona,
    geo_punto,
    minutos_caminando,
    redondear,
)
from app.compartido.traslados import minutos_en_autobus
from app.ia.arbol_binario import NodoParada
from app.ia.busqueda_informada import distancia_plano_km
from app.ia.transbordos import RADIO_TRANSBORDO_KM, buscar_transbordo
from app.ia.trazos import arbol_de_ruta, km_acumulados, proyectar, tramo_del_trazo
from app.modulos.laboratorio.servicio import ServicioLaboratorio
from app.modulos.rutas.repositorio import RepositorioRutas
from app.nucleo.errores import NoEncontrado

FUENTE_ESTIMACION = "Estimación por distancia"
FUENTE_TRAZO = "Trazo registrado por el equipo Kompás · tiempos estimados por distancia"
SIN_AUTOBUS = "No tenemos información suficiente de transporte público para esta ruta."
AVISOS_AUTO = ["El tiempo no considera el tráfico.", "La tarifa la define el proveedor; consúltala en su app o con el conductor."]
AVISO_SIN_HORARIO = "Sin horario ni tarifa verificados: el tiempo de espera no está incluido."
AVISO_PUNTOS = "Las paradas son puntos del trazo registrado; las paradas reales están pendientes de captura."


def nombre_ruta(ruta: dict) -> str:
    return ruta.get("nombre") or f"Ruta {ruta['id']}"


def _parada(nodo: NodoParada) -> dict:
    p = nodo.parada
    return {"nombre": p["nombre"], "lat": p["lat"], "lng": p["lng"], "km": round(nodo.clave, 3)}


def _a_parada_app(p: dict) -> dict:
    """{nombre, lat, lng} → Parada de la app ({nombre, ubicacion: GeoJSON})."""
    return {"nombre": p["nombre"], "ubicacion": geo_punto(p["lat"], p["lng"])}


class ServicioRutas:
    def __init__(self, repo: RepositorioRutas, bitacora: ServicioLaboratorio | None = None):
        self.repo = repo
        self.bitacora = bitacora

    def listar(self) -> list[dict]:
        return self.repo.listar()

    def detalle(self, id_ruta: int) -> dict:
        ruta = self.repo.por_id(id_ruta)
        if ruta is None:
            raise NoEncontrado("No encontramos esa ruta.")
        return ruta

    def existe(self, id_ruta: int) -> bool:
        return self.repo.por_id(id_ruta) is not None

    def arbol(self, id_ruta: int) -> dict:
        """Árbol binario de paradas de la ruta (endpoint de apoyo para pruebas y el manual técnico)."""
        ruta = self.detalle(id_ruta)
        arbol, reales = arbol_de_ruta(ruta)
        return {"id_ruta": id_ruta, "nombre": nombre_ruta(ruta), "paradas_reales": reales, **arbol.resumen()}

    # ─────────────────────────────── ¿Cómo llego? ───────────────────────────────

    def _tramo_en_ruta(self, ruta: dict, sube: NodoParada, baja: NodoParada) -> dict:
        """Tramo en autobús entre dos paradas de la ruta (puntos y paradas intermedias del árbol, en inorden)."""
        arbol, reales = arbol_de_ruta(ruta)
        intermedias = [n for n in arbol.rango(sube.clave, baja.clave) if n is not sube and n is not baja]
        if reales:
            puntos = tramo_del_trazo(ruta["trazo"], sube.clave, baja.clave)
        else:
            puntos = [[n.parada["lng"], n.parada["lat"]] for n in arbol.rango(sube.clave, baja.clave)]
        km = baja.clave - sube.clave
        return {
            "modo": "autobus",
            "id_ruta": ruta["id"],
            "linea": nombre_ruta(ruta),
            "parada_subida": _parada(sube),
            "parada_bajada": _parada(baja),
            "tramo_en_ruta": puntos,
            "paradas_intermedias": [_parada(n) for n in intermedias],
            "trazo_ruta": ruta["trazo"],
            "distancia_km": round(km, 2),
            "duracion_min": minutos_en_autobus(km),
            "paradas_reales": reales,
        }

    @staticmethod
    def _caminata(desde: Coordenada, hasta: Coordenada) -> dict:
        km = distancia_por_calles_km(desde, hasta)
        return {"modo": "pie", "desde": desde, "hasta": hasta, "distancia_km": round(km, 2), "duracion_min": minutos_caminando(km)}

    def _directa(self, ruta: dict, a: Coordenada, b: Coordenada) -> dict | None:
        """Una sola ruta, o None si no pasa cerca del origen y luego del destino."""
        trazo = ruta["trazo"]
        if len(trazo) < 2:
            return None
        acumulado = km_acumulados(trazo)
        pa, pb = proyectar(a, trazo, acumulado), proyectar(b, trazo, acumulado)
        if pa["distancia_km"] > RADIO_TRANSBORDO_KM or pb["distancia_km"] > RADIO_TRANSBORDO_KM:
            return None
        arbol, _ = arbol_de_ruta(ruta)
        sube, _ = arbol.mas_cercano(pa["km"])
        baja, _ = arbol.mas_cercano(pb["km"])
        # Mismo sentido que el trazo y paradas a distancia caminable
        if sube is None or baja is None or sube.clave >= baja.clave:
            return None
        if distancia_plano_km(a, sube.parada) > RADIO_TRANSBORDO_KM or distancia_plano_km(baja.parada, b) > RADIO_TRANSBORDO_KM:
            return None
        bus = self._tramo_en_ruta(ruta, sube, baja)
        return self._opcion([self._caminata(a, sube.parada), bus, self._caminata(baja.parada, b)], "directo")

    def _combinada(self, rutas: list[dict], a: Coordenada, b: Coordenada) -> dict | None:
        resultado = buscar_transbordo(rutas, a, b)
        if self.bitacora:
            self.bitacora.registrar(
                "transbordo",
                {
                    "encontrado": resultado["encontrado"],
                    "rutas_usadas": resultado["rutas_usadas"],
                    "nodos_explorados": resultado["nodos_explorados"],
                    "total_nodos": resultado["total_nodos"],
                    "ms": resultado["ms"],
                },
            )
        if not resultado["encontrado"]:
            return None
        por_id = {r["id"]: r for r in rutas}
        tramos = []
        for t in resultado["tramos"]:
            if t["modo"] == "pie":
                tramos.append(self._caminata(t["desde"], t["hasta"]))
                continue
            ruta = por_id[t["id_ruta"]]
            arbol, _ = arbol_de_ruta(ruta)
            sube, _ = arbol.mas_cercano(t["km_subida"])
            baja, _ = arbol.mas_cercano(t["km_bajada"])
            tramos.append(self._tramo_en_ruta(ruta, sube, baja))
        # Las caminatas de transbordo van desde la bajada de una ruta hasta la subida de la otra
        return self._opcion(tramos, "combinado" if len(resultado["rutas_usadas"]) > 1 else "directo")

    def _opcion(self, tramos: list[dict], tipo: str) -> dict:
        """Alternativa en autobús con la forma de la app (abordaje/descenso) más los campos nuevos."""
        buses = [t for t in tramos if t["modo"] == "autobus"]
        primero, ultimo = buses[0], buses[-1]
        caminata = sum(t["duracion_min"] for t in tramos if t["modo"] == "pie")
        trayecto = sum(t["duracion_min"] for t in buses)
        ids = [t["id_ruta"] for t in buses]
        avisos = [AVISO_SIN_HORARIO]
        if not all(t["paradas_reales"] for t in buses):
            avisos.append(AVISO_PUNTOS)
        transbordos = [_a_parada_app(t["parada_subida"]) | {"linea": t["linea"]} for t in buses[1:]]
        return {
            "id": f"bus_{'_'.join(str(i) for i in ids)}",
            "modo": "autobus",
            "tipo": tipo,
            "id_ruta": primero["id_ruta"],
            "ruta_id": str(primero["id_ruta"]),
            "rutas": ids,
            "linea": " + ".join(t["linea"] for t in buses),
            "tarifa": None,
            "parada_subida": primero["parada_subida"],
            "parada_bajada": ultimo["parada_bajada"],
            "abordaje": _a_parada_app(primero["parada_subida"]),
            "descenso": _a_parada_app(ultimo["parada_bajada"]),
            "transbordos": transbordos,
            "numero_transbordos": len(buses) - 1,
            "tramo_en_ruta": [p for t in buses for p in t["tramo_en_ruta"]],
            "paradas_intermedias": [p for t in buses for p in t["paradas_intermedias"]],
            "trazo": {"type": "LineString", "coordinates": [p for t in buses for p in t["tramo_en_ruta"]]},
            "tramos": [{k: v for k, v in t.items() if k != "paradas_reales"} for t in tramos],
            "tiempos": {"caminata": caminata, "espera": None, "trayecto": trayecto},
            "distancia_km": round(sum(t["distancia_km"] for t in tramos), 2),
            "fuente": FUENTE_TRAZO,
            "fecha_verificacion": None,
            "avisos": avisos,
        }

    def _autobuses(self, a: Coordenada, b: Coordenada) -> list[dict]:
        rutas = [r for r in self.repo.listar() if len(r["trazo"]) >= 2]
        if not rutas:
            return []
        opciones = [o for o in (self._directa(r, a, b) for r in rutas) if o]
        if not opciones and (combinada := self._combinada(rutas, a, b)):
            opciones.append(combinada)
        opciones.sort(key=lambda o: o["tiempos"]["caminata"] + o["tiempos"]["trayecto"])
        if self.bitacora:
            for o in opciones:
                for t in (t for t in o["tramos"] if t["modo"] == "autobus"):
                    self.bitacora.registrar(
                        "abordaje",
                        {"tipo_opcion": o["tipo"], "id_ruta": t["id_ruta"], "subida": t["parada_subida"], "bajada": t["parada_bajada"]},
                    )
        return opciones

    def alternativas(self, a: Coordenada, b: Coordenada) -> dict:
        """En autobús (si hay rutas que conecten), a pie y en taxi/app estimadas por distancia."""
        if not (esta_dentro_de_zona(a) and esta_dentro_de_zona(b)):
            return {
                "datos_suficientes": False,
                "mensaje": "El origen o el destino está fuera de la zona piloto (Toluca, Lerma y San Mateo Atenco).",
                "alternativas": [],
            }

        km = round(distancia_por_calles_km(a, b), 2)
        pie = {
            "id": "pie",
            "modo": "pie",
            "distancia_km": km,
            "tiempos": {"caminata": minutos_caminando(km), "espera": None, "trayecto": None},
            "fuente": FUENTE_ESTIMACION,
            "avisos": ["Trayecto largo para hacerlo a pie."] if km > 4 else [],
        }

        def auto(modo: str) -> dict:
            return {
                "id": modo,
                "modo": modo,
                "distancia_km": km,
                "tiempos": {"caminata": None, "espera": ESPERA_TAXI_MIN, "trayecto": redondear(km / VELOCIDAD_AUTO_KMH * 60)},
                "fuente": FUENTE_ESTIMACION,
                "avisos": AVISOS_AUTO,
            }

        buses = self._autobuses(a, b)
        return {
            "datos_suficientes": bool(buses),
            "mensaje": None if buses else SIN_AUTOBUS,
            "alternativas": [*buses, pie, auto("taxi"), auto("app")],
        }
