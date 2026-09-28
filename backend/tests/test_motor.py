"""Pruebas del sistema experto SIN API ni BD: solo diccionarios (para Einar)."""

from app.ia.motor import recomendar
from app.ia.reglas import REGLAS_LUGAR, encadenar

TOLUCA = {"lat": 19.2926, "lng": -99.6557}


def lugar(id_: str, interes: str, lat: float, lng: float, **cambios) -> dict:
    base = {"_id": id_, "id": int(id_) if id_.isdigit() else 0, "nombre": f"Lugar {id_}", "lat": lat, "lng": lng,
            "categoria": interes.title(), "interes": interes}
    return {**base, **cambios}


SOLICITUD = {
    "contexto": "pareja",
    "presupuesto": {"min": 0, "max": 500},
    "tiempo_horas": 4,
    "intereses": ["cafe", "comer", "cultura"],
    "movilidad": ["caminando"],
    "origen": TOLUCA,
    "hora_salida": "12:00",
}


def descartes(respuesta: dict) -> dict[str, list[str]]:
    return {d["lugar_id"]: [r["id"] for r in d["reglas"]] for d in respuesta["descartados"]}


def test_encadenamiento_hacia_adelante():
    hechos = {"datos_suficientes": True, "coincide_intereses": True, "cerca": True, "apto_contexto": True, "cabe_en_tiempo": True}
    disparadas = [r.id for r in encadenar(hechos, REGLAS_LUGAR)]
    assert disparadas == ["R1", "R2", "R3"]
    assert hechos["incluir_en_plan"] is True


def test_recomienda_y_explica():
    lugares = [lugar("cafe", "cafe", 19.292, -99.656), lugar("comida", "comer", 19.293, -99.657), lugar("museo", "cultura", 19.2935, -99.658)]
    r = recomendar({**SOLICITUD, "tiempo_horas": 5}, lugares)  # 60 + 90 + 90 min de estancia + traslados
    assert r["datos_suficientes"] is True
    mejor = r["planes"][0]
    assert mejor["mejor_opcion"] and mejor["tipo"] == "equilibrado"
    assert {p["lugar_id"] for p in mejor["paradas"]} == {"cafe", "comida", "museo"}
    assert mejor["costo"] is None
    ids = [x["id"] for x in mejor["reglas_cumplidas"]]
    assert {"R1", "R2", "R3", "R11"} <= set(ids)
    assert all(t["modo"] == "pie" for t in mejor["tramos"])
    assert mejor["tramos"][0]["desde"] == "Tu ubicación"


def test_descarta_con_la_regla_que_corresponde():
    lugares = [
        lugar("1", "cafe", 19.292, -99.656),
        lugar("2", "comer", 19.2921, -99.6561),
        lugar("sin_datos", "cafe", 19.292, -99.656, categoria=None),
        lugar("lejos", "cafe", 19.285, -99.5115),  # Lerma, ~15 km
        lugar("interes", "aire_libre", 19.292, -99.656),
        lugar("contexto", "cafe", 19.292, -99.656),
    ]
    r = recomendar({**SOLICITUD, "contexto": "familia", "intereses": ["cafe", "comer"]}, lugares)
    d = descartes(r)
    assert d["sin_datos"] == ["R5"]
    assert d["lejos"] == ["R7"]  # solo caminando y a más de 2 km
    assert d["interes"] == ["R8"]
    assert d["contexto"] == ["R9"] and d["1"] == ["R9"]  # café no es típico para familia (tabla temporal)


def test_con_taxi_lo_lejano_ya_no_se_descarta_por_distancia():
    lugares = [lugar("a", "cafe", 19.28, -99.61), lugar("b", "comer", 19.281, -99.611)]  # ~5 km
    a_pie = recomendar(SOLICITUD, lugares)
    assert descartes(a_pie) == {"a": ["R7"], "b": ["R7"]}
    en_taxi = recomendar({**SOLICITUD, "movilidad": ["taxi_app"]}, lugares)
    assert len(en_taxi["planes"]) >= 1
    assert en_taxi["planes"][0]["tramos"][0]["modo"] == "taxi"
    assert "R12" in [x["id"] for x in en_taxi["planes"][0]["reglas_cumplidas"]]


def test_no_cabe_en_tiempo():
    lugares = [lugar("a", "cultura", 19.292, -99.656), lugar("b", "comer", 19.2921, -99.6561)]
    r = recomendar({**SOLICITUD, "tiempo_horas": 1}, lugares)  # 90 min de estancia > 60
    assert descartes(r) == {"a": ["R10"], "b": ["R10"]}
    assert r["planes"] == []


def test_sin_candidatos_avisa_y_no_inventa():
    r = recomendar(SOLICITUD, [lugar("solo_uno", "cafe", 19.292, -99.656)])
    assert r["planes"] == [] and r["datos_suficientes"] is False
    assert r["aviso"].startswith("No tenemos información suficiente")
