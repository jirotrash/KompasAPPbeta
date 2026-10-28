"""Panel de administración (/api/admin/...), búsquedas guardadas y solicitudes de rutas.

Las otras pruebas cuentan rutas, lugares y categorías exactos: cada prueba de aquí borra lo que crea.
"""

from datetime import datetime

import pytest

from tests.conftest import encabezado, registrar

TRAZO = [[-99.60, 19.30], [-99.62, 19.295], [-99.6557, 19.2926]]
PARADAS = [
    {"nombre": "Inicio", "ubicacion": {"type": "Point", "coordinates": [-99.60, 19.30]}},
    {"nombre": "Centro", "ubicacion": {"type": "Point", "coordinates": [-99.6557, 19.2926]}},
]
DENTRO = {"type": "Point", "coordinates": [-99.625, 19.279]}
FUERA = {"type": "Point", "coordinates": [-99.13, 19.43]}


@pytest.fixture(scope="module")
def admin(token_demo) -> dict:
    return encabezado(token_demo)


@pytest.fixture(scope="module")
def usuario(cliente) -> dict:
    return encabezado(registrar(cliente, "panel@ejemplo.mx")["token"])


def test_el_panel_es_solo_para_admin(cliente, usuario):
    assert cliente.get("/api/admin/rutas").status_code == 401
    for ruta in ("rutas", "lugares", "categorias", "transportes", "reportes", "busquedas", "solicitudes-rutas"):
        assert cliente.get(f"/api/admin/{ruta}", headers=usuario).status_code == 403, ruta


def test_crud_de_rutas(cliente, admin):
    nueva = {"nombre": "  Ruta de prueba  ", "trazo": TRAZO, "paradas": PARADAS}
    respuesta = cliente.post("/api/admin/rutas", json=nueva, headers=admin)
    assert respuesta.status_code == 201, respuesta.text
    ruta = respuesta.json()
    assert ruta["nombre"] == "Ruta de prueba" and ruta["trazo"] == TRAZO and len(ruta["paradas"]) == 2
    try:
        # La app ya la ve y el árbol usa las paradas reales
        assert ruta["id"] in [r["id"] for r in cliente.get("/api/rutas").json()]
        assert cliente.get(f"/api/rutas/{ruta['id']}/arbol", headers=admin).json()["paradas_reales"] is True

        editada = cliente.put(f"/api/admin/rutas/{ruta['id']}", json={**nueva, "nombre": "Ruta editada", "paradas": []}, headers=admin)
        assert editada.status_code == 200 and editada.json()["nombre"] == "Ruta editada" and "paradas" not in editada.json()

        fuera = cliente.post("/api/admin/rutas", json={**nueva, "trazo": [[-99.13, 19.43], [-99.6, 19.3]]}, headers=admin)
        assert fuera.status_code == 422 and "zona piloto" in fuera.json()["detail"]
        assert cliente.post("/api/admin/rutas", json={**nueva, "trazo": TRAZO[:1]}, headers=admin).status_code == 422
        assert cliente.put("/api/admin/rutas/99999", json=nueva, headers=admin).status_code == 404
    finally:
        assert cliente.delete(f"/api/admin/rutas/{ruta['id']}", headers=admin).status_code == 204
    assert cliente.get(f"/api/rutas/{ruta['id']}").status_code == 404
    assert cliente.delete(f"/api/admin/rutas/{ruta['id']}", headers=admin).status_code == 404


def test_crud_de_lugares(cliente, admin):
    cafe = next(c for c in cliente.get("/api/categorias").json() if c["clave"] == "cafe")
    respuesta = cliente.post("/api/admin/lugares", json={"nombre": "Café de prueba", "id_categoria": cafe["id"], "ubicacion": DENTRO}, headers=admin)
    assert respuesta.status_code == 201, respuesta.text
    lugar = respuesta.json()
    assert lugar["categoria"] == cafe["nombre"] and lugar["id_categoria"] == cafe["id"] and lugar["interes"] == "cafe"
    try:
        comer = next(c for c in cliente.get("/api/categorias").json() if c["clave"] == "comer")
        editado = cliente.put(f"/api/admin/lugares/{lugar['id']}", json={"nombre": "Fonda", "id_categoria": comer["id"], "ubicacion": DENTRO}, headers=admin)
        assert editado.json()["interes"] == "comer"

        sin_categoria = {"nombre": "X", "id_categoria": 999, "ubicacion": DENTRO}
        assert cliente.post("/api/admin/lugares", json=sin_categoria, headers=admin).status_code == 404
        fuera = {"nombre": "X", "id_categoria": cafe["id"], "ubicacion": FUERA}
        assert cliente.post("/api/admin/lugares", json=fuera, headers=admin).status_code == 422
    finally:
        assert cliente.delete(f"/api/admin/lugares/{lugar['id']}", headers=admin).status_code == 204
    assert cliente.get(f"/api/lugares/{lugar['id']}").status_code == 404


def test_categorias_protegidas_y_nuevas(cliente, admin):
    categorias = cliente.get("/api/admin/categorias", headers=admin).json()
    comer = next(c for c in categorias if c["clave"] == "comer")
    assert comer["protegida"] is True
    # Protegida: no se borra ni cambia de clave, pero sí de descripción
    assert cliente.delete(f"/api/admin/categorias/{comer['id']}", headers=admin).status_code == 409
    assert cliente.put(f"/api/admin/categorias/{comer['id']}", json={"nombre": "Comida"}, headers=admin).status_code == 409
    misma = cliente.put(f"/api/admin/categorias/{comer['id']}", json={"nombre": comer["nombre"], "descripcion": "Nueva"}, headers=admin)
    assert misma.status_code == 200 and misma.json()["descripcion"] == "Nueva"
    cliente.put(f"/api/admin/categorias/{comer['id']}", json={"nombre": comer["nombre"], "descripcion": comer["descripcion"]}, headers=admin)

    nueva = cliente.post("/api/admin/categorias", json={"nombre": "Museos"}, headers=admin)
    assert nueva.status_code == 201 and nueva.json()["protegida"] is False and nueva.json()["clave"] == "museos"
    id_museos = nueva.json()["id"]
    assert cliente.post("/api/admin/categorias", json={"nombre": "MUSEOS"}, headers=admin).status_code == 409

    # Con lugares no se puede borrar; renombrarla también renombra la copia en los lugares
    lugar = cliente.post("/api/admin/lugares", json={"nombre": "Museo X", "id_categoria": id_museos, "ubicacion": DENTRO}, headers=admin).json()
    assert cliente.delete(f"/api/admin/categorias/{id_museos}", headers=admin).status_code == 409
    cliente.put(f"/api/admin/categorias/{id_museos}", json={"nombre": "Museos y galerías"}, headers=admin)
    assert cliente.get(f"/api/lugares/{lugar['id']}").json()["categoria"] == "Museos y galerías"
    cliente.delete(f"/api/admin/lugares/{lugar['id']}", headers=admin)
    assert cliente.delete(f"/api/admin/categorias/{id_museos}", headers=admin).status_code == 204
    assert "museos_y_galerias" not in {c["clave"] for c in cliente.get("/api/categorias").json()}

    # Volver a crear una borrada la restaura (el nombre es único en la colección)
    otra = cliente.post("/api/admin/categorias", json={"nombre": "Museos y galerías"}, headers=admin)
    assert otra.status_code == 201 and otra.json()["id"] == id_museos
    cliente.delete(f"/api/admin/categorias/{id_museos}", headers=admin)


def test_transportes_protegidos_y_nuevos(cliente, admin):
    transportes = cliente.get("/api/admin/transportes", headers=admin).json()
    assert all(t["protegida"] for t in transportes)
    assert cliente.delete(f"/api/admin/transportes/{transportes[0]['id']}", headers=admin).status_code == 409

    bici = cliente.post("/api/admin/transportes", json={"nombre": "Bicicleta"}, headers=admin)
    assert bici.status_code == 201 and bici.json()["clave"] == "bicicleta"
    assert cliente.put(f"/api/admin/transportes/{bici.json()['id']}", json={"nombre": "Bici"}, headers=admin).json()["nombre"] == "Bici"
    assert cliente.delete(f"/api/admin/transportes/{bici.json()['id']}", headers=admin).status_code == 204


def test_moderacion_de_reportes(cliente, admin, usuario):
    nuevo = {"tipo": "accidente", "ubicacion": DENTRO, "observado_en": datetime.now().astimezone().isoformat()}
    reporte = cliente.post("/api/reportes", json=nuevo, headers=usuario).json()

    todos = cliente.get("/api/admin/reportes", headers=admin).json()
    mio = next(r for r in todos if r["_id"] == reporte["_id"])
    assert mio["vigente"] is True and mio["id_usuario"] is not None

    verificado = cliente.patch(f"/api/admin/reportes/{reporte['_id']}", json={"estado": "verificado"}, headers=admin)
    assert verificado.status_code == 200 and verificado.json()["estado"] == "verificado"
    assert cliente.patch(f"/api/admin/reportes/{reporte['_id']}", json={"estado": "otro"}, headers=admin).status_code == 422
    assert all(r["estado"] == "verificado" for r in cliente.get("/api/admin/reportes", params={"estado": "verificado"}, headers=admin).json())

    assert cliente.delete(f"/api/admin/reportes/{reporte['_id']}", headers=admin).status_code == 204
    assert cliente.delete(f"/api/admin/reportes/{reporte['_id']}", headers=admin).status_code == 404
    assert cliente.delete("/api/admin/reportes/no-es-un-id", headers=admin).status_code == 404


def test_las_busquedas_se_guardan_con_el_usuario(cliente, admin, usuario, bd):
    antes = bd.busquedas.count_documents({})
    params = {"origen": "19.33,-99.60", "destino": "19.2926,-99.6557"}
    cliente.get("/api/rutas", params=params, headers=usuario)
    cliente.get("/api/rutas", params=params)  # sin sesión también se guarda
    cliente.get("/api/rutas", params=params, headers=encabezado("token-vencido"))  # un token malo no da 401
    cliente.get("/api/rutas", params={"origen": "19.43,-99.13", "destino": "19.2926,-99.6557"})  # fuera de zona: no
    assert bd.busquedas.count_documents({}) == antes + 3

    ultimas = cliente.get("/api/admin/busquedas", params={"sin_autobus": True, "limite": 3}, headers=admin).json()
    assert len(ultimas) == 3 and all(not b["datos_suficientes"] and b["opciones_autobus"] == 0 for b in ultimas)
    assert ultimas[0]["origen"] == {"type": "Point", "coordinates": [-99.60, 19.33]}
    assert {b["id_usuario"] is None for b in ultimas} == {True, False}


def test_solicitudes_de_rutas(cliente, admin, usuario):
    assert cliente.post("/api/solicitudes-rutas", json={"origen": DENTRO, "destino": DENTRO}).status_code == 401
    fuera = cliente.post("/api/solicitudes-rutas", json={"origen": DENTRO, "destino": FUERA}, headers=usuario)
    assert fuera.status_code == 422

    respuesta = cliente.post("/api/solicitudes-rutas", json={"origen": DENTRO, "destino": PARADAS[1]["ubicacion"], "comentario": "  Pasa una combi  "}, headers=usuario)
    assert respuesta.status_code == 201, respuesta.text
    solicitud = respuesta.json()
    assert solicitud["estado"] == "pendiente" and solicitud["comentario"] == "Pasa una combi"
    assert [s["id"] for s in cliente.get("/api/solicitudes-rutas", headers=usuario).json()] == [solicitud["id"]]

    pendientes = cliente.get("/api/admin/solicitudes-rutas", params={"estado": "pendiente"}, headers=admin).json()
    assert solicitud["id"] in [s["id"] for s in pendientes]
    atendida = cliente.patch(f"/api/admin/solicitudes-rutas/{solicitud['id']}", json={"estado": "atendida", "nota_admin": "Ya está"}, headers=admin)
    assert atendida.json()["estado"] == "atendida" and atendida.json()["nota_admin"] == "Ya está"
    assert cliente.get("/api/solicitudes-rutas", headers=usuario).json()[0]["estado"] == "atendida"

    assert cliente.delete(f"/api/admin/solicitudes-rutas/{solicitud['id']}", headers=admin).status_code == 204
    assert cliente.patch(f"/api/admin/solicitudes-rutas/{solicitud['id']}", json={"estado": "atendida"}, headers=admin).status_code == 404
