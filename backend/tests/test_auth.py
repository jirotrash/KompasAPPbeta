from tests.conftest import encabezado, registrar


def test_registro_como_lo_manda_la_app(cliente):
    sesion = registrar(cliente, "ana@ejemplo.mx", "Ana")
    assert sesion["token"]
    usuario = sesion["usuario"]
    assert usuario["nombre"] == "Ana" and usuario["primer_apellido"] == "Pérez"
    assert usuario["segundo_apellido"] is None and usuario["fecha_nacimiento"] == "2004-05-10"
    assert usuario["email"] == usuario["correo"] == "ana@ejemplo.mx"
    assert "password" not in usuario


def test_registro_sin_apellido_o_con_fecha_futura_da_422(cliente):
    base = {"nombre": "Eva", "email": "eva@ejemplo.mx", "password": "secreta123"}
    sin_apellido = cliente.post("/api/auth/register", json=base)
    assert sin_apellido.status_code == 422 and "primer_apellido" in sin_apellido.json()["detail"]
    futura = cliente.post("/api/auth/register", json={**base, "primer_apellido": "Ruiz", "fecha_nacimiento": "2999-01-01"})
    assert futura.status_code == 422 and "fecha_nacimiento" in futura.json()["detail"]


def test_registro_con_campos_de_backend_md(cliente):
    datos = {
        "nombre": "Luis",
        "primer_apellido": "Pérez",
        "segundo_apellido": "Gómez",
        "correo": "LUIS@Ejemplo.mx",
        "password": "secreta123",
        "fecha_nacimiento": "2004-05-10",
    }
    respuesta = cliente.post("/api/auth/registro", json=datos)
    assert respuesta.status_code == 201
    usuario = respuesta.json()["usuario"]
    assert usuario["correo"] == "luis@ejemplo.mx"
    assert usuario["primer_apellido"] == "Pérez" and usuario["fecha_nacimiento"] == "2004-05-10"


def test_registro_con_correo_repetido_da_409(cliente):
    registrar(cliente, "repetido@ejemplo.mx")
    respuesta = cliente.post("/api/auth/registro", json={"nombre": "Otro", "primer_apellido": "Ruiz", "correo": "repetido@ejemplo.mx", "password": "secreta123"})
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "Ya existe una cuenta con ese correo."


def test_registro_invalido_da_422_con_mensaje_de_texto(cliente):
    respuesta = cliente.post("/api/auth/registro", json={"nombre": "X", "correo": "no-es-correo", "password": "123"})
    assert respuesta.status_code == 422
    assert isinstance(respuesta.json()["detail"], str)


def test_login_correcto_e_incorrecto(cliente):
    ok = cliente.post("/api/auth/login", json={"correo": "demo@kompas.mx", "password": "demo1234"})
    assert ok.status_code == 200
    assert ok.json()["usuario"]["correo"] == "demo@kompas.mx"

    # La app manda `email` en vez de `correo`
    assert cliente.post("/api/auth/login", json={"email": "demo@kompas.mx", "password": "demo1234"}).status_code == 200

    mal = cliente.post("/api/auth/login", json={"correo": "demo@kompas.mx", "password": "otra-cosa"})
    assert mal.status_code == 401
    assert mal.json()["detail"] == "Correo o contraseña incorrectos."


def test_el_administrador_no_puede_entrar_con_contrasena_adivinada(cliente):
    respuesta = cliente.post("/api/auth/login", json={"correo": "admin@kompas.mx", "password": "admin123"})
    assert respuesta.status_code == 401


def test_yo_requiere_token_valido(cliente, token_demo):
    assert cliente.get("/api/auth/yo").status_code == 401
    assert cliente.get("/api/auth/yo", headers=encabezado("token-falso")).status_code == 401
    respuesta = cliente.get("/api/auth/yo", headers=encabezado(token_demo))
    assert respuesta.status_code == 200
    assert respuesta.json()["correo"] == "demo@kompas.mx"


def test_residencia(cliente):
    h = encabezado(registrar(cliente, "casa@ejemplo.mx")["token"])
    assert cliente.get("/api/residencia").status_code == 401
    assert cliente.get("/api/residencia", headers=h).json() is None

    guardada = cliente.put("/api/residencia", json={"calle": "Hidalgo", "municipio": "Lerma"}, headers=h)
    assert guardada.status_code == 200
    assert guardada.json()["municipio"] == "Lerma" and guardada.json()["colonia"] is None

    # PUT otra vez actualiza la misma residencia en lugar de crear otra
    actualizada = cliente.put("/api/residencia", json={"municipio": "Toluca", "colonia": "Centro"}, headers=h).json()
    assert actualizada["id"] == guardada.json()["id"]
    assert cliente.get("/api/residencia", headers=h).json()["colonia"] == "Centro"
