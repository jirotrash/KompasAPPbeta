"""Las pruebas usan la base `kompas_test` (mismo servidor que MONGO_URI), que se recrea en cada corrida.
Nunca tocan la base `kompas` ni Atlas. Si MongoDB no responde, las pruebas con BD se omiten."""

import os

import pytest

# Debe ir antes de importar app.nucleo.config / app.main (la configuración se lee una sola vez)
os.environ["MONGO_DB"] = "kompas_test"
os.environ["MONGO_DESTINO"] = "local"  # aunque backend/.env apunte a Atlas
if os.environ.get("TEST_MONGO_URI"):
    os.environ["MONGO_URI"] = os.environ["TEST_MONGO_URI"]

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def bd():
    from pymongo import MongoClient

    from app.nucleo.bd import get_bd
    from app.nucleo.config import get_settings
    from scripts.preparar_bd import preparar

    try:
        MongoClient(get_settings().mongo_uri, serverSelectionTimeoutMS=1500).admin.command("ping")
        preparar(recrear=True, silencioso=True)
    except Exception as error:  # noqa: BLE001
        pytest.skip(f"MongoDB no disponible para pruebas: {error}")
    return get_bd()


@pytest.fixture(scope="session")
def cliente(bd) -> TestClient:
    return TestClient(app)


def registrar(cliente: TestClient, correo: str, nombre: str = "Prueba") -> dict:
    """Registro con los mismos campos que manda la pantalla de registro de la app."""
    datos = {
        "nombre": nombre,
        "primer_apellido": "Pérez",
        "email": correo,
        "password": "secreta123",
        "fecha_nacimiento": "2004-05-10",
    }
    respuesta = cliente.post("/api/auth/register", json=datos)
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def encabezado(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def token_demo(cliente) -> str:
    respuesta = cliente.post("/api/auth/login", json={"email": "demo@kompas.mx", "password": "demo1234"})
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["token"]
