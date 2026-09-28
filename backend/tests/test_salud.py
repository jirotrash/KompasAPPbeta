from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_salud_responde_ok():
    respuesta = cliente.get("/api/salud")
    assert respuesta.status_code == 200
    assert respuesta.json()["ok"] is True


def test_docs_disponibles():
    assert cliente.get("/docs").status_code == 200
    assert cliente.get("/openapi.json").json()["info"]["title"] == "Kompás API"


def test_cors_abierto_en_desarrollo():
    respuesta = cliente.get("/api/salud", headers={"Origin": "http://localhost:8081"})
    assert respuesta.headers["access-control-allow-origin"] == "*"
