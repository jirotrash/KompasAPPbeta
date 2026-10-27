"""Asistente con Ollama SIMULADO (mock de app/externos/ollama.py): no necesita Ollama ni Google."""

import pytest

from app.externos import google_places, ollama
from tests.conftest import encabezado, registrar
from tests.test_itinerarios import lugar_google

UBICACION = {"lat": 19.2926, "lng": -99.6557}


class OllamaFalso:
    """Responde con un guion: cada elemento es lo que regresa una llamada a ollama.chat()."""

    def __init__(self):
        self.guion: list = []
        self.recibidos: list[list[dict]] = []

    def __call__(self, mensajes, herramientas=None, **_):
        self.recibidos.append([dict(m) for m in mensajes])
        paso = self.guion.pop(0)
        if isinstance(paso, Exception):
            raise paso
        return paso


def texto(contenido: str) -> dict:
    return {"contenido": contenido, "llamadas": [], "mensaje": {"role": "assistant", "content": contenido}}


def herramienta(nombre: str, **argumentos) -> dict:
    llamada = {"function": {"name": nombre, "arguments": argumentos}}
    return {"contenido": "", "llamadas": [{"nombre": nombre, "argumentos": argumentos}], "mensaje": {"role": "assistant", "content": "", "tool_calls": [llamada]}}


@pytest.fixture
def llm(monkeypatch):
    falso = OllamaFalso()
    monkeypatch.setattr(ollama, "chat", falso)

    def sin_google(*_, **__):
        raise google_places.ErrorGooglePlaces("Sin llave en pruebas.")

    monkeypatch.setattr(google_places, "buscar_texto", sin_google)
    return falso


@pytest.fixture
def usuario(cliente) -> dict:
    """Un usuario nuevo por prueba."""
    usuario.n = getattr(usuario, "n", 0) + 1
    return encabezado(registrar(cliente, f"asistente{usuario.n}@ejemplo.mx")["token"])


def nueva(cliente, h) -> str:
    respuesta = cliente.post("/api/asistente/conversaciones", headers=h)
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["id"]


def test_requiere_sesion(cliente):
    assert cliente.get("/api/asistente/estado").status_code == 401
    assert cliente.post("/api/asistente/conversaciones").status_code == 401


def test_guarda_mensajes_y_rutas_consultadas(cliente, bd, llm, usuario):
    id_conv = nueva(cliente, usuario)
    llm.guion = [
        herramienta("como_llegar", origen="mi ubicación", destino="Museo de ejemplo"),
        texto("Puedes caminar unos minutos (tiempo estimado)."),
    ]
    cuerpo = {"texto": "¿Cómo llego al Museo de ejemplo desde aquí?", "ubicacion": UBICACION}
    respuesta = cliente.post(f"/api/asistente/conversaciones/{id_conv}/mensajes", json=cuerpo, headers=usuario)
    assert respuesta.status_code == 200, respuesta.text
    datos = respuesta.json()
    assert datos["mensaje"]["rol"] == "asistente" and "estimado" in datos["mensaje"]["contenido"]
    assert datos["herramientas_usadas"] == ["como_llegar"]
    tarjeta = datos["tarjetas"][0]
    assert tarjeta["tipo"] == "ruta" and tarjeta["destino"]["nombre"].startswith("Museo de ejemplo")
    assert tarjeta["alternativa"]["modo"] == "pie"

    # Al modelo le llegó el system prompt y el resultado de la herramienta en JSON
    segunda = llm.recibidos[1]
    assert segunda[0]["role"] == "system" and "Toluca, Lerma y San Mateo Atenco" in segunda[0]["content"]
    assert segunda[-1]["role"] == "tool" and "Museo de ejemplo" in segunda[-1]["content"]

    conversacion = cliente.get(f"/api/asistente/conversaciones/{id_conv}", headers=usuario).json()
    assert [m["rol"] for m in conversacion["mensajes"]] == ["usuario", "herramienta", "asistente"]
    assert conversacion["titulo"] == "¿Cómo llego al Museo de ejemplo…"
    assert conversacion["mensajes"][1]["resultado_ref"]["tipo"] == "ruta"
    assert conversacion["mensajes"][1]["tarjeta"]["titulo"] == "mi ubicación → Museo de ejemplo"
    assert conversacion["mensajes"][2]["duracion_ms"] >= 0
    assert conversacion["rutas_consultadas"][0]["destino"] == "Museo de ejemplo"

    # La misma consulta otra vez no repite la ruta consultada
    llm.guion = [herramienta("como_llegar", origen="mi ubicación", destino="Museo de ejemplo"), texto("Igual que antes.")]
    cliente.post(f"/api/asistente/conversaciones/{id_conv}/mensajes", json=cuerpo, headers=usuario)
    doc = cliente.get(f"/api/asistente/conversaciones/{id_conv}", headers=usuario).json()
    assert len(doc["rutas_consultadas"]) == 1 and len(doc["mensajes"]) == 6
    # No se guarda la ubicación del usuario
    guardado = bd.conversaciones.find_one({"titulo": conversacion["titulo"]})
    assert "19.2926" not in str(guardado)

    lista = cliente.get("/api/asistente/conversaciones", headers=usuario).json()
    assert lista[0]["id"] == id_conv and lista[0]["ultimo_mensaje"] == "Igual que antes." and lista[0]["total_mensajes"] == 6


def test_la_herramienta_crea_un_plan(cliente, bd, llm, usuario, monkeypatch):
    monkeypatch.setattr(
        google_places,
        "buscar_para_plan",
        lambda *_: [
            lugar_google("cafe", "Café de prueba", "cafe", 19.2935, -99.6570),
            lugar_google("restaurante", "Restaurante de prueba", "comer", 19.2905, -99.6530),
            lugar_google("museo", "Museo de prueba", "cultura", 19.2950, -99.6590),
        ],
    )
    id_conv = nueva(cliente, usuario)
    llm.guion = [
        herramienta("armar_salida", contexto="pareja", presupuesto="1500", tiempo=4, intereses=["comer", "café", "cultura"], hora_salida="18:00"),
        texto("Te armé un plan."),
    ]
    respuesta = cliente.post(f"/api/asistente/conversaciones/{id_conv}/mensajes", json={"texto": "Un plan en pareja", "ubicacion": UBICACION}, headers=usuario)
    assert respuesta.status_code == 200, respuesta.text
    tarjeta = respuesta.json()["tarjetas"][0]
    assert tarjeta["tipo"] == "plan" and tarjeta["plan"]["paradas"]

    plan = bd.planes.find_one({"_id": tarjeta["id_plan"]})
    assert plan["origen_solicitud"] == "asistente" and plan["contexto"] == "pareja"
    assert plan["intereses"] == ["comer", "cafe", "cultura"]
    conversacion = cliente.get(f"/api/asistente/conversaciones/{id_conv}", headers=usuario).json()
    assert conversacion["planes_creados"] == [tarjeta["id_plan"]]
    # Aparece en Mis planes como cualquier plan
    assert cliente.get("/api/planes", headers=usuario).json()[0]["id"] == tarjeta["id_plan"]


def test_maximo_tres_herramientas_por_mensaje(cliente, llm, usuario):
    id_conv = nueva(cliente, usuario)
    llm.guion = [herramienta("mis_planes")] * 4 + [texto("Listo.")]
    datos = cliente.post(f"/api/asistente/conversaciones/{id_conv}/mensajes", json={"texto": "mis planes"}, headers=usuario).json()
    assert datos["herramientas_usadas"] == ["mis_planes"] * 3


def test_modelo_sin_tools_responde_solo_con_texto(cliente, llm, usuario):
    id_conv = nueva(cliente, usuario)
    llm.guion = [ollama.SinHerramientas("does not support tools"), texto("Hola, ¿a dónde quieres ir?")]
    datos = cliente.post(f"/api/asistente/conversaciones/{id_conv}/mensajes", json={"texto": "hola"}, headers=usuario).json()
    assert datos["mensaje"]["contenido"] == "Hola, ¿a dónde quieres ir?" and datos["herramientas_usadas"] == []


def test_503_si_ollama_no_responde_y_el_mensaje_se_guarda(cliente, llm, usuario):
    id_conv = nueva(cliente, usuario)
    llm.guion = [ollama.ErrorOllama("Connection refused")]
    respuesta = cliente.post(f"/api/asistente/conversaciones/{id_conv}/mensajes", json={"texto": "hola"}, headers=usuario)
    assert respuesta.status_code == 503
    assert respuesta.json()["detail"] == "El asistente no está disponible en este momento."
    mensajes = cliente.get(f"/api/asistente/conversaciones/{id_conv}", headers=usuario).json()["mensajes"]
    assert [m["rol"] for m in mensajes] == ["usuario", "error"] and mensajes[0]["contenido"] == "hola"


def test_404_con_la_conversacion_de_otro_usuario(cliente, llm, usuario, token_demo):
    id_conv = nueva(cliente, usuario)
    otro = encabezado(token_demo)
    assert cliente.get(f"/api/asistente/conversaciones/{id_conv}", headers=otro).status_code == 404
    assert cliente.post(f"/api/asistente/conversaciones/{id_conv}/mensajes", json={"texto": "hola"}, headers=otro).status_code == 404
    assert cliente.delete(f"/api/asistente/conversaciones/{id_conv}", headers=otro).status_code == 404
    assert cliente.get("/api/asistente/conversaciones/no-es-un-id", headers=usuario).status_code == 404
    assert all(c["id"] != id_conv for c in cliente.get("/api/asistente/conversaciones", headers=otro).json())


def test_limite_de_2000_caracteres_y_borrado_logico(cliente, bd, llm, usuario):
    id_conv = nueva(cliente, usuario)
    largo = cliente.post(f"/api/asistente/conversaciones/{id_conv}/mensajes", json={"texto": "a" * 2001}, headers=usuario)
    assert largo.status_code == 422
    assert cliente.delete(f"/api/asistente/conversaciones/{id_conv}", headers=usuario).status_code == 204
    assert cliente.get(f"/api/asistente/conversaciones/{id_conv}", headers=usuario).status_code == 404
    from bson import ObjectId

    assert bd.conversaciones.find_one({"_id": ObjectId(id_conv)})["deleted_at"] is not None


def test_estado(cliente, usuario, monkeypatch):
    monkeypatch.setattr(ollama, "estado", lambda: {"disponible": False, "modelo": "llama3.2:3b", "modelo_instalado": False})
    assert cliente.get("/api/asistente/estado", headers=usuario).json() == {"disponible": False, "modelo": "llama3.2:3b", "modelo_instalado": False}


def test_llamada_escrita_como_json_en_el_texto():
    nombres = {"buscar_lugares", "como_llegar"}
    texto_modelo = '```\n{"name": "buscar_lugares", "parameters": {"texto": "Cancun", "categoria": "null"}}\n```'
    assert ollama.llamada_en_texto(texto_modelo, nombres) == {"nombre": "buscar_lugares", "argumentos": {"texto": "Cancun"}}
    assert ollama.llamada_en_texto('{"name": "borrar_todo", "parameters": {}}', nombres) is None
    assert ollama.llamada_en_texto("Hola, ¿a dónde vas?", nombres) is None
