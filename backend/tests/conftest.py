"""Las pruebas usan el esquema `kompas_test` (mismo servidor que DATABASE_URL), que se recrea en
cada corrida. Nunca tocan el esquema `kompas`. Si MySQL no responde, las pruebas con BD se omiten."""

import os

import pytest
from sqlalchemy import make_url

from app.config import Settings

# Debe ir antes de importar app.db / app.main (el engine se crea al importarlos)
_url = make_url(os.environ.get("TEST_DATABASE_URL") or Settings().database_url).set(database="kompas_test")
os.environ["DATABASE_URL"] = _url.render_as_string(hide_password=False)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def bd():
    from scripts.preparar_bd import preparar

    try:
        preparar(_url, recrear=True, silencioso=True)
    except Exception as error:  # noqa: BLE001
        pytest.skip(f"MySQL no disponible para pruebas: {error}")


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
