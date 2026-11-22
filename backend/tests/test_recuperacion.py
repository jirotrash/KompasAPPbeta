"""Recuperación de contraseña: código por correo, verificación y cambio de contraseña."""

from datetime import timedelta

import pytest

from app.externos import correo
from app.nucleo.bd import ahora
from tests.conftest import registrar


@pytest.fixture
def buzon(monkeypatch) -> list[dict]:
    """Sustituye el envío SMTP: guarda los correos en una lista en lugar de mandarlos."""
    enviados: list[dict] = []
    monkeypatch.setattr(correo, "configurado", lambda: True)
    monkeypatch.setattr(
        correo,
        "enviar",
        lambda para, asunto, texto, html=None, imagenes=None: enviados.append(
            {"para": para, "asunto": asunto, "texto": texto, "html": html, "imagenes": imagenes}
        ),
    )
    return enviados


def _codigo(enviado: dict) -> str:
    return next(palabra for palabra in enviado["texto"].split() if palabra.isdigit() and len(palabra) == 6)


def test_flujo_completo_cambia_la_contrasena(cliente, buzon):
    registrar(cliente, "olvido@ejemplo.mx")
    respuesta = cliente.post("/api/auth/recuperar", json={"email": "Olvido@Ejemplo.mx"})
    assert respuesta.status_code == 200 and "código" in respuesta.json()["mensaje"]
    assert len(buzon) == 1 and buzon[0]["para"] == "olvido@ejemplo.mx"
    codigo = _codigo(buzon[0])
    # Versión HTML con el diseño de la app: el código, el logo incrustado y el azul primario
    assert codigo in buzon[0]["asunto"] and codigo in buzon[0]["html"]
    assert 'src="cid:logo"' in buzon[0]["html"] and "#1A62A5" in buzon[0]["html"]
    assert buzon[0]["imagenes"]["logo"].startswith(b"\x89PNG")

    verificado = cliente.post("/api/auth/recuperar/verificar", json={"email": "olvido@ejemplo.mx", "codigo": codigo})
    assert verificado.status_code == 200

    cambio = {"email": "olvido@ejemplo.mx", "codigo": codigo, "password": "nueva12345"}
    assert cliente.post("/api/auth/recuperar/restablecer", json=cambio).status_code == 200
    assert cliente.post("/api/auth/login", json={"email": "olvido@ejemplo.mx", "password": "nueva12345"}).status_code == 200
    assert cliente.post("/api/auth/login", json={"email": "olvido@ejemplo.mx", "password": "secreta123"}).status_code == 401
    # El código solo sirve una vez
    assert cliente.post("/api/auth/recuperar/restablecer", json=cambio).status_code == 400


def test_correo_no_registrado_responde_igual_y_no_envia(cliente, buzon):
    respuesta = cliente.post("/api/auth/recuperar", json={"email": "nadie@ejemplo.mx"})
    assert respuesta.status_code == 200 and "código" in respuesta.json()["mensaje"]
    assert buzon == []


def test_codigo_incorrecto_y_limite_de_intentos(cliente, buzon):
    registrar(cliente, "intentos@ejemplo.mx")
    cliente.post("/api/auth/recuperar", json={"email": "intentos@ejemplo.mx"})
    bueno = _codigo(buzon[0])
    malo = "000000" if bueno != "000000" else "111111"
    for _ in range(4):
        r = cliente.post("/api/auth/recuperar/verificar", json={"email": "intentos@ejemplo.mx", "codigo": malo})
        assert r.status_code == 400 and "no es válido" in r.json()["detail"]
    quinto = cliente.post("/api/auth/recuperar/verificar", json={"email": "intentos@ejemplo.mx", "codigo": malo})
    assert quinto.status_code == 400 and "Demasiados intentos" in quinto.json()["detail"]
    # Tras agotar los intentos, ni el código bueno sirve
    r = cliente.post("/api/auth/recuperar/verificar", json={"email": "intentos@ejemplo.mx", "codigo": bueno})
    assert r.status_code == 400


def test_codigo_vencido(cliente, buzon, bd):
    registrar(cliente, "vencido@ejemplo.mx")
    cliente.post("/api/auth/recuperar", json={"email": "vencido@ejemplo.mx"})
    bd.codigos_recuperacion.update_one({"_id": "vencido@ejemplo.mx"}, {"$set": {"expira": ahora() - timedelta(minutes=1)}})
    r = cliente.post("/api/auth/recuperar/verificar", json={"email": "vencido@ejemplo.mx", "codigo": _codigo(buzon[0])})
    assert r.status_code == 400 and "venció" in r.json()["detail"]


def test_no_reenvia_antes_de_un_minuto_y_guarda_solo_el_hash(cliente, buzon, bd):
    registrar(cliente, "reenvio@ejemplo.mx")
    cliente.post("/api/auth/recuperar", json={"email": "reenvio@ejemplo.mx"})
    cliente.post("/api/auth/recuperar", json={"email": "reenvio@ejemplo.mx"})
    assert len(buzon) == 1
    guardado = bd.codigos_recuperacion.find_one({"_id": "reenvio@ejemplo.mx"})
    assert _codigo(buzon[0]) not in str(guardado)


def test_falla_del_servidor_de_correo_da_503(cliente, monkeypatch, bd):
    registrar(cliente, "smtpcaido@ejemplo.mx")
    monkeypatch.setattr(correo, "configurado", lambda: True)

    def caido(*_, **__):
        raise correo.ErrorCorreo("sin conexión")

    monkeypatch.setattr(correo, "enviar", caido)
    r = cliente.post("/api/auth/recuperar", json={"email": "smtpcaido@ejemplo.mx"})
    assert r.status_code == 503
    assert bd.codigos_recuperacion.find_one({"_id": "smtpcaido@ejemplo.mx"}) is None


def test_datos_mal_formados_dan_422(cliente):
    base = {"email": "x@ejemplo.mx"}
    assert cliente.post("/api/auth/recuperar/verificar", json={**base, "codigo": "12ab56"}).status_code == 422
    corta = {**base, "codigo": "123456", "password": "123"}
    assert cliente.post("/api/auth/recuperar/restablecer", json=corta).status_code == 422


def test_el_correo_saluda_con_el_nombre_registrado_en_la_base(cliente, buzon, bd):
    registrar(cliente, "mariana@ejemplo.mx", "Mariana")
    cliente.post("/api/auth/recuperar", json={"email": "mariana@ejemplo.mx"})
    nombre_en_bd = bd.usuarios.find_one({"correo": "mariana@ejemplo.mx"})["nombre"]
    assert nombre_en_bd == "Mariana"
    assert f"Hola, {nombre_en_bd}" in buzon[0]["texto"] and f"Hola, {nombre_en_bd}" in buzon[0]["html"]


def test_el_codigo_vence_a_los_15_minutos(cliente, buzon, bd):
    registrar(cliente, "quince@ejemplo.mx")
    cliente.post("/api/auth/recuperar", json={"email": "quince@ejemplo.mx"})
    guardado = bd.codigos_recuperacion.find_one({"_id": "quince@ejemplo.mx"})
    vigencia = guardado["expira"] - guardado["creado"]
    assert timedelta(minutes=14, seconds=59) <= vigencia <= timedelta(minutes=15, seconds=1)
    # Un segundo antes de vencer todavía sirve; un segundo después ya no
    codigo = {"email": "quince@ejemplo.mx", "codigo": _codigo(buzon[0])}
    bd.codigos_recuperacion.update_one({"_id": "quince@ejemplo.mx"}, {"$set": {"expira": ahora() + timedelta(seconds=1)}})
    assert cliente.post("/api/auth/recuperar/verificar", json=codigo).status_code == 200
    bd.codigos_recuperacion.update_one({"_id": "quince@ejemplo.mx"}, {"$set": {"expira": ahora() - timedelta(seconds=1)}})
    assert cliente.post("/api/auth/recuperar/verificar", json=codigo).status_code == 400


def test_pedir_un_codigo_nuevo_anula_el_anterior(cliente, buzon, bd):
    registrar(cliente, "dos@ejemplo.mx")
    cliente.post("/api/auth/recuperar", json={"email": "dos@ejemplo.mx"})
    # Simula que ya pasó el minuto de espera para pedir otro
    bd.codigos_recuperacion.update_one({"_id": "dos@ejemplo.mx"}, {"$set": {"creado": ahora() - timedelta(minutes=2)}})
    cliente.post("/api/auth/recuperar", json={"email": "dos@ejemplo.mx"})
    viejo, nuevo = _codigo(buzon[0]), _codigo(buzon[1])
    if viejo != nuevo:
        assert cliente.post("/api/auth/recuperar/verificar", json={"email": "dos@ejemplo.mx", "codigo": viejo}).status_code == 400
    assert cliente.post("/api/auth/recuperar/verificar", json={"email": "dos@ejemplo.mx", "codigo": nuevo}).status_code == 200
