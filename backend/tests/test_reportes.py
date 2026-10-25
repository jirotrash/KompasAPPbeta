from datetime import datetime, timedelta

from tests.conftest import encabezado, registrar

DENTRO_DE_ZONA = {"type": "Point", "coordinates": [-99.625, 19.279]}


def nuevo(tipo: str = "manifestacion", **extra) -> dict:
    return {"tipo": tipo, "ubicacion": DENTRO_DE_ZONA, "observado_en": datetime.now().astimezone().isoformat(), **extra}


def test_crear_reporte_requiere_sesion(cliente):
    assert cliente.post("/api/reportes", json=nuevo()).status_code == 401


def test_crea_reporte_con_vigencia_segun_el_tipo(cliente):
    h = encabezado(registrar(cliente, "reportero@ejemplo.mx")["token"])
    respuesta = cliente.post("/api/reportes", json=nuevo("cierre_total", ruta_id="7", comentario="  Calle cerrada  "), headers=h)
    assert respuesta.status_code == 201, respuesta.text
    reporte = respuesta.json()
    assert isinstance(reporte["_id"], str) and reporte["_id"]
    assert reporte["estado"] == "pendiente" and reporte["confirmaciones"] == 0
    assert reporte["comentario"] == "Calle cerrada" and reporte["ruta_id"] == "7"
    assert reporte["ubicacion"] == DENTRO_DE_ZONA
    vigencia = datetime.fromisoformat(reporte["vigente_hasta"]) - datetime.fromisoformat(reporte["observado_en"])
    assert vigencia == timedelta(hours=6)


def test_lista_solo_vigentes_y_filtra_por_ruta(cliente):
    h = encabezado(registrar(cliente, "vigentes@ejemplo.mx")["token"])
    vencido = nuevo("afluencia", ruta_id="vencida", nivel_afluencia="alta")
    vencido["observado_en"] = (datetime.now().astimezone() - timedelta(hours=2)).isoformat()
    assert cliente.post("/api/reportes", json=vencido, headers=h).status_code == 201
    assert cliente.post("/api/reportes", json=nuevo("accidente", ruta_id="9"), headers=h).status_code == 201

    de_la_ruta = cliente.get("/api/reportes", params={"ruta_id": "9"}).json()
    assert [r["tipo"] for r in de_la_ruta] == ["accidente"]
    assert cliente.get("/api/reportes", params={"ruta_id": "vencida"}).json() == []
    assert all(r["ruta_id"] != "vencida" for r in cliente.get("/api/reportes").json() if "ruta_id" in r)


def test_reporte_fuera_de_zona_o_invalido(cliente):
    h = encabezado(registrar(cliente, "lejos@ejemplo.mx")["token"])
    fuera = nuevo(ubicacion={"type": "Point", "coordinates": [-99.13, 19.43]})
    respuesta = cliente.post("/api/reportes", json=fuera, headers=h)
    assert respuesta.status_code == 422 and "zona piloto" in respuesta.json()["detail"]

    invalido = cliente.post("/api/reportes", json=nuevo("inundacion"), headers=h)
    assert invalido.status_code == 422 and isinstance(invalido.json()["detail"], str)
