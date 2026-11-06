"""Destinos probables con el historial real (`historial_rutas`): lógica pura y endpoints /api/ia 🔒."""

from datetime import datetime, timedelta

from app.modulos.ia_kompas.habitos import MIN_VIAJES, UMBRAL_KNN, caracteristicas, franja_horaria, predecir_destinos, resumir_habitos
from app.modulos.rutas.repositorio import RepositorioRutas
from app.nucleo.bd import ZONA_HORARIA, siguiente_id
from tests.conftest import encabezado, registrar

LUNES = datetime(2026, 10, 5, tzinfo=ZONA_HORARIA)
RUTA_ESCUELA, RUTA_CENTRO, RUTA_PASEO = 101, 102, 103


def _viaje(id_ruta: int, dia: int, hora: int, minuto: int = 0, transporte: str = "Transporte público") -> dict:
    return {"id_ruta": id_ruta, "transporte": transporte, "momento": LUNES + timedelta(days=dia, hours=hora, minutes=minuto)}


def _semanas(n: int) -> list[dict]:
    """Rutina: entre semana a la escuela a las 7 y al centro a las 15; sábado de paseo a las 19."""
    viajes = []
    for s in range(n):
        for d in range(5):
            viajes.append(_viaje(RUTA_ESCUELA, s * 7 + d, 7, 10 * (d % 3)))
            viajes.append(_viaje(RUTA_CENTRO, s * 7 + d, 15, 15))
        viajes.append(_viaje(RUTA_PASEO, s * 7 + 5, 19, 30, "Taxi/App"))
    return viajes


def test_franjas_y_caracteristicas_circulares():
    assert franja_horaria(7) == "manana" and franja_horaria(15) == "tarde" and franja_horaria(23) == "noche"
    # 23:30 y 00:30 quedan cerca en el círculo de la hora
    a, b = caracteristicas(23.5, 0), caracteristicas(0.5, 0)
    assert abs(a[0] - b[0]) < 0.3 and abs(a[1] - b[1]) < 0.05


def test_sin_suficientes_viajes_no_inventa_destino():
    r = predecir_destinos(_semanas(1)[: MIN_VIAJES - 1], 7, 0)
    assert r["estado"] == "datos_insuficientes"
    assert r["destinos"] == [] and r["metodo"] is None


def test_frecuencia_por_franja_con_pocos_datos():
    viajes = _semanas(1)
    assert MIN_VIAJES <= len(viajes) < UMBRAL_KNN
    manana = predecir_destinos(viajes, 7, 1)
    assert manana["metodo"] == "frecuencia_franja"
    assert manana["destinos"][0]["id_ruta"] == RUTA_ESCUELA
    assert predecir_destinos(viajes, 15, 2)["destinos"][0]["id_ruta"] == RUTA_CENTRO
    assert sum(d["probabilidad"] for d in manana["destinos"]) <= 1.0001


def test_knn_aprende_la_rutina_y_supera_al_baseline():
    viajes = _semanas(4)
    assert len(viajes) >= UMBRAL_KNN
    manana = predecir_destinos(viajes, 7, 3)
    assert manana["metodo"] == "knn"
    assert manana["destinos"][0]["id_ruta"] == RUTA_ESCUELA
    assert manana["destinos"][0]["hora_habitual"].startswith("07:")
    assert predecir_destinos(viajes, 15, 0)["destinos"][0]["id_ruta"] == RUTA_CENTRO
    assert predecir_destinos(viajes, 19, 5)["destinos"][0]["id_ruta"] == RUTA_PASEO
    assert manana["exactitud_validacion"] > manana["exactitud_baseline"]


def test_resumen_de_habitos_solo_cuenta():
    r = resumir_habitos(_semanas(1))
    assert r["total_viajes"] == 11
    assert r["rutas_frecuentes"][0]["viajes"] == 5
    assert r["transportes"] == {"Transporte público": 10, "Taxi/App": 1}
    assert r["por_dia"]["sábado"] == 1
    assert resumir_habitos([])["total_viajes"] == 0


# ─────────────────────────── Endpoints con la base de pruebas ───────────────────────────


def test_destinos_probables_requiere_sesion(cliente):
    assert cliente.get("/api/ia/destinos-probables").status_code == 401


def test_destinos_probables_desde_historial_real(cliente, bd):
    sesion = registrar(cliente, "habitos@kompas.mx")
    id_usuario, cabeza = sesion["usuario"]["id"], encabezado(sesion["token"])

    vacio = cliente.get("/api/ia/destinos-probables", params={"hora": 7, "dia": 0}, headers=cabeza).json()
    assert vacio["estado"] == "datos_insuficientes" and vacio["viajes_analizados"] == 0

    rutas = RepositorioRutas(bd)
    trazo = [[-99.66, 19.29], [-99.65, 19.28]]
    escuela = rutas.crear(trazo, "Ruta Escuela", [{"nombre": "UTVT", "ubicacion": {"type": "Point", "coordinates": trazo[-1]}}])
    centro = rutas.crear(trazo, "Ruta Centro")
    transporte = bd.transportes.find_one({"nombre": "Transporte público"})
    ids = {RUTA_ESCUELA: escuela["id"], RUTA_CENTRO: centro["id"], RUTA_PASEO: centro["id"]}
    try:
        for v in _semanas(3):
            bd.historial_rutas.insert_one(
                {
                    "_id": siguiente_id(bd, "historial_rutas"),
                    "id_usuario": id_usuario,
                    "id_ruta": ids[v["id_ruta"]],
                    "transporte": {"id": transporte["_id"], "nombre": transporte["nombre"]},
                    "tiempo_estimado": 20,
                    "created_at": v["momento"],
                    "updated_at": v["momento"],
                    "deleted_at": None,
                }
            )

        r = cliente.get("/api/ia/destinos-probables", params={"hora": 7, "dia": 2}, headers=cabeza)
        assert r.status_code == 200, r.text
        datos = r.json()
        assert datos["estado"] == "ok" and datos["metodo"] == "knn"
        assert datos["destinos"][0]["nombre"] == "Ruta Escuela"
        assert datos["destinos"][0]["ultima_parada"] == "UTVT"

        habitos = cliente.get("/api/ia/mis-habitos", headers=cabeza).json()
        assert habitos["total_viajes"] == 33
        assert {r["nombre"] for r in habitos["rutas_frecuentes"]} == {"Ruta Escuela", "Ruta Centro"}
    finally:
        # La base de pruebas es de toda la sesión: otras pruebas cuentan las rutas
        bd.historial_rutas.delete_many({"id_usuario": id_usuario})
        bd.rutas.delete_many({"_id": {"$in": [escuela["id"], centro["id"]]}})
