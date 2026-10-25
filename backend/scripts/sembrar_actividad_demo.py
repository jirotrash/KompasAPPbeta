"""Genera actividad SINTÉTICA para probar el dashboard. Todo lo que crea lleva `demo: true`.

Uso (desde backend/, con el venv activo y la base ya preparada con scripts.preparar_bd):
    python -m scripts.sembrar_actividad_demo --dias 60 --usuarios 40 --planes 300   # genera
    python -m scripts.sembrar_actividad_demo --borrar                               # borra todo lo demo

- Usuarios demo+N@kompas.mx (contraseña aleatoria que nadie conoce).
- Planes con intereses, movilidad, contexto y presupuesto variados. Su `evaluacion` sale del motor REAL:
  se llama a app.ia.servicio.recomendar() con los lugares genéricos de ejemplo de la base y el horario de
  backend/ejemplos/entrada_hechos.json (no se eligen reglas a mano).
- Recorridos sobre rutas existentes; si la base no tiene rutas, crea unas rutas demo entre lugares de ejemplo.
- Reportes dentro de la zona piloto y consultas de DFS y distancias en bitacora_laboratorio.
- Semilla fija (random.seed(28)): la demo es reproducible.
"""

import argparse
import json
import random
import secrets
import sys
from datetime import datetime, timedelta
from pathlib import Path

from pymongo.database import Database

from app.compartido.geo import ZONA, distancia_euclidiana_km, distancia_manhattan_km, distancia_por_calles_km, esta_dentro_de_zona
from app.ia.busqueda_dfs import PARADAS_KOMPAS, planificar_rutas_dfs
from app.ia.servicio import recomendar
from app.modulos.itinerarios.servicio import ACOMPANANTES, evaluacion_de
from app.nucleo.bd import ZONA_HORARIA, ahora, get_bd, siguiente_id
from app.nucleo.seguridad import hash_password
from scripts.preparar_bd import ajustar_contadores

SEMILLA = 28
EJEMPLO = Path(__file__).resolve().parent.parent / "ejemplos" / "entrada_hechos.json"
COLECCIONES_DEMO = ("usuarios", "planes", "historial_rutas", "rutas", "reportes", "bitacora_laboratorio")

NOMBRES = ["Ana", "Luis", "María", "José", "Fernanda", "Diego", "Sofía", "Carlos", "Valeria", "Jorge", "Paola", "Iván"]
APELLIDOS = ["García", "Hernández", "López", "Martínez", "González", "Pérez", "Sánchez", "Ramírez", "Flores", "Cruz"]
CONTEXTOS = {"solo": 2, "pareja": 4, "amigos": 5, "familia": 3}
INTERESES = {"comer": 6, "cafe": 4, "cultura": 3, "entretenimiento": 4, "aire_libre": 3}
MOVILIDADES = {"caminando": 5, "transporte_publico": 4, "taxi_app": 3, "combinado": 2}
PRESUPUESTOS = [(0, 80), (50, 150), (100, 250), (150, 400), (200, 600), (300, 900), (500, 1500)]
HORAS = list(range(9, 23))
PESO_HORA = [1, 1, 2, 3, 4, 3, 3, 3, 4, 6, 7, 6, 4, 2]  # más salidas por la tarde-noche
TIPOS_REPORTE = {"manifestacion": 3, "accidente": 3, "afluencia": 5, "cierre_total": 2}
VIGENCIA_H = {"cierre_total": 6, "accidente": 2, "manifestacion": 3, "afluencia": 1}
MIN_POR_KM = {"Caminando": 12, "Transporte público": 5, "Taxi/App": 2.6, "Combinado": 4}


def elegir(pesos: dict) -> str:
    return random.choices(list(pesos), weights=list(pesos.values()))[0]


def varios(pesos: dict, maximo: int) -> list[str]:
    elegidos: list[str] = []
    for _ in range(random.randint(1, maximo)):
        opcion = elegir(pesos)
        if opcion not in elegidos:
            elegidos.append(opcion)
    return elegidos


def momento_aleatorio(inicio: datetime, fin: datetime) -> datetime:
    return inicio + timedelta(seconds=random.uniform(0, max(1.0, (fin - inicio).total_seconds())))


def punto_en_zona() -> dict:
    lim = ZONA["limites"]
    # Centrado en el corredor Toluca–Lerma, donde están los lugares de ejemplo
    return {"lat": round(random.uniform(lim["sur"] + 0.05, lim["norte"] - 0.08), 5), "lng": round(random.uniform(lim["oeste"] + 0.08, lim["este"] - 0.1), 5)}


def lugares_de_ejemplo(bd: Database) -> list[dict]:
    """Lugares genéricos de la base con el formato de Google que espera el planificador (sintéticos)."""
    horario = json.loads(EJEMPLO.read_text(encoding="utf-8"))["itinerario"]["visitas"][0]["horario"]
    interes = {"Comer": "comer", "Café": "cafe", "Cultura": "cultura", "Entretenimiento": "entretenimiento", "Aire libre": "aire_libre"}
    salida = []
    for doc in bd.lugares.find({"deleted_at": None}):
        lng, lat = doc["ubicacion"]["coordinates"]
        salida.append(
            {
                "place_id": f"demo-{doc['_id']}",
                "nombre": doc["nombre"],
                "lat": lat,
                "lng": lng,
                "categoria": interes.get(doc["categoria"]["nombre"], "comer"),
                "tipos": [],
                "horario": horario,
                "nivel_precio": None,
                "rango_precio": None,
                "calificacion": None,
                "total_resenas": None,
                "fuente": "Google",
            }
        )
    return salida


def con_precios(lugares: list[dict], consultado: datetime) -> list[dict]:
    """Cada plan ve precios distintos (a veces sin dato) para que la evaluación varíe."""
    variados = []
    for l in lugares:
        rango = None
        if random.random() < 0.92:
            minimo = random.choice([40, 60, 80, 100, 150, 200])
            rango = {"min": minimo, "max": minimo + random.choice([30, 50, 80, 150]), "moneda": "MXN"}
        variados.append({**l, "rango_precio": rango, "consultado_en": consultado.isoformat()})
    return variados


def sembrar(bd: Database, dias: int, usuarios: int, planes: int) -> dict:
    random.seed(SEMILLA)
    fin = ahora()
    inicio = fin - timedelta(days=dias)
    password = hash_password(secrets.token_urlsafe(24))
    conteo = dict.fromkeys(COLECCIONES_DEMO, 0)

    # ── Usuarios ──
    ids_usuarios = []
    base_n = bd.usuarios.count_documents({"demo": True})
    for n in range(base_n + 1, base_n + usuarios + 1):
        creado = momento_aleatorio(inicio, fin - timedelta(days=1))
        doc = {
            "_id": siguiente_id(bd, "usuarios"),
            "nombre": random.choice(NOMBRES),
            "primer_apellido": random.choice(APELLIDOS),
            "segundo_apellido": random.choice(APELLIDOS + [None]),
            "correo": f"demo+{n}@kompas.mx",
            "password": password,
            "fecha_nacimiento": datetime(random.randint(1975, 2007), random.randint(1, 12), random.randint(1, 28), tzinfo=ZONA_HORARIA),
            "rol": "usuario",
            "residencia": None,
            "demo": True,
            "created_at": creado,
            "updated_at": creado,
            "deleted_at": None,
        }
        bd.usuarios.insert_one(doc)
        ids_usuarios.append((doc["_id"], creado))
        conteo["usuarios"] += 1

    # ── Planes evaluados por el motor real ──
    lugares = lugares_de_ejemplo(bd)
    categorias = {c["nombre"]: c for c in bd.categorias.find({"deleted_at": None})}
    transportes = {t["nombre"]: t for t in bd.transportes.find({"deleted_at": None})}
    nombre_interes = {"comer": "Comer", "cafe": "Café", "cultura": "Cultura", "entretenimiento": "Entretenimiento", "aire_libre": "Aire libre"}
    nombre_movilidad = {"caminando": "Caminando", "transporte_publico": "Transporte público", "taxi_app": "Taxi/App", "combinado": "Combinado"}
    for _ in range(planes):
        id_usuario, alta = random.choice(ids_usuarios)
        creado = momento_aleatorio(alta, fin)
        hora = random.choices(HORAS, weights=PESO_HORA)[0]
        hora_salida = f"{hora:02d}:{random.choice([0, 15, 30, 45]):02d}"
        minimo, maximo = random.choice(PRESUPUESTOS)
        contexto = elegir(CONTEXTOS)
        cerca = random.choice(lugares)
        peticion = {
            "contexto": contexto,
            "presupuesto": {"min": float(minimo), "max": float(maximo)},
            "tiempo_horas": random.choice([1, 1.5, 2, 3, 3, 4, 4, 5, 6, 8]),
            "intereses": varios(INTERESES, 3),
            "movilidad": varios(MOVILIDADES, 2),
            "origen": {"lat": cerca["lat"] + random.uniform(-0.004, 0.004), "lng": cerca["lng"] + random.uniform(-0.004, 0.004)},
            "hora_salida": hora_salida,
        }
        reloj = creado.replace(hour=max(0, hora - 1), minute=random.randint(0, 59))
        respuesta = recomendar(peticion, con_precios(lugares, reloj), reloj)

        categoria = categorias.get(nombre_interes[peticion["intereses"][0]])
        transporte = transportes.get(nombre_movilidad[peticion["movilidad"][0]])
        if categoria is None or transporte is None:
            sys.exit("Faltan categorías o transportes: corre primero python -m scripts.preparar_bd")
        h, m = (int(x) for x in hora_salida.split(":"))
        bd.planes.insert_one(
            {
                "_id": siguiente_id(bd, "planes"),
                "id_usuario": id_usuario,
                "contexto": contexto,
                "no_acompanantes": ACOMPANANTES[contexto],
                "presupuesto": peticion["presupuesto"],
                "tiempo_disponible": round(peticion["tiempo_horas"] * 60),
                "intereses": peticion["intereses"],
                "movilidad": peticion["movilidad"],
                "categoria": {"id": categoria["_id"], "nombre": categoria["nombre"]},
                "transporte": {"id": transporte["_id"], "nombre": transporte["nombre"]},
                "hora_salida": hora_salida,
                "fecha_plan": creado.astimezone(ZONA_HORARIA).replace(hour=h, minute=m, second=0, microsecond=0),
                "evaluacion": evaluacion_de(respuesta),
                "demo": True,
                "created_at": creado,
                "updated_at": creado,
                "deleted_at": None,
            }
        )
        conteo["planes"] += 1

    # ── Rutas (solo si no hay) y recorridos ──
    rutas = list(bd.rutas.find({"deleted_at": None}))
    if not rutas:
        for a, b in [(0, 5), (1, 6), (2, 7), (3, 8), (4, 9), (0, 4)]:
            if b >= len(lugares):
                continue
            puntos = [[lugares[a]["lng"], lugares[a]["lat"]], [lugares[b]["lng"], lugares[a]["lat"]], [lugares[b]["lng"], lugares[b]["lat"]]]
            doc = {"_id": siguiente_id(bd, "rutas"), "trazo": {"type": "LineString", "coordinates": puntos}, "demo": True, "created_at": fin, "updated_at": fin, "deleted_at": None}
            bd.rutas.insert_one(doc)
            rutas.append(doc)
            conteo["rutas"] += 1
    pesos_ruta = [random.randint(1, 8) for _ in rutas]
    for _ in range(round(planes * 0.8)):
        id_usuario, alta = random.choice(ids_usuarios)
        ruta = random.choices(rutas, weights=pesos_ruta)[0]
        coords = ruta["trazo"]["coordinates"]
        km = distancia_por_calles_km({"lat": coords[0][1], "lng": coords[0][0]}, {"lat": coords[-1][1], "lng": coords[-1][0]})
        transporte = transportes[random.choices(list(MIN_POR_KM), weights=[4, 5, 3, 2])[0]]
        minutos = max(3, round(km * MIN_POR_KM[transporte["nombre"]] * random.uniform(0.8, 1.35)))
        creado = momento_aleatorio(alta, fin)
        bd.historial_rutas.insert_one(
            {
                "_id": siguiente_id(bd, "historial_rutas"),
                "id_usuario": id_usuario,
                "id_ruta": ruta["_id"],
                "transporte": {"id": transporte["_id"], "nombre": transporte["nombre"]},
                "tiempo_estimado": min(minutos, 24 * 60),
                "demo": True,
                "created_at": creado,
                "updated_at": creado,
                "deleted_at": None,
            }
        )
        conteo["historial_rutas"] += 1

    # ── Reportes dentro de la zona piloto ──
    for i in range(round(planes * 0.4)):
        tipo = elegir(TIPOS_REPORTE)
        # Algunos de las últimas horas para que haya reportes vigentes
        observado = fin - timedelta(minutes=random.randint(5, 150)) if i % 8 == 0 else momento_aleatorio(inicio, fin)
        p = punto_en_zona()
        doc = {
            "tipo": tipo,
            "ubicacion": {"type": "Point", "coordinates": [p["lng"], p["lat"]]},
            "observado_en": observado,
            "vigente_hasta": observado + timedelta(hours=VIGENCIA_H[tipo]),
            "confirmaciones": random.choice([0, 0, 0, 1, 1, 2, 3, 5]),
            "estado": random.choices(["pendiente", "verificado", "descartado"], weights=[6, 3, 1])[0],
            "id_usuario": random.choice(ids_usuarios)[0],
            "demo": True,
            "created_at": observado,
        }
        if tipo == "afluencia":
            doc["nivel_afluencia"] = random.choice(["baja", "media", "alta"])
        if rutas and random.random() < 0.4:
            doc["ruta_id"] = str(random.choice(rutas)["_id"])
        bd.reportes.insert_one(doc)
        conteo["reportes"] += 1

    # ── Bitácora del laboratorio (resultados reales de DFS y de las métricas) ──
    paradas = list(PARADAS_KOMPAS)
    pares = [(random.choice(paradas), random.choice(paradas)) for _ in range(8)]
    for _ in range(round(planes * 0.3)):
        origen, destino = random.choice(pares) if random.random() < 0.7 else random.sample(paradas, 2)
        if origen == destino:
            continue
        limite = random.randint(2, 8)
        r = planificar_rutas_dfs(origen, destino, limite)
        bd.bitacora_laboratorio.insert_one(
            {
                "tipo": "dfs",
                "creado_en": momento_aleatorio(inicio, fin),
                "origen": origen,
                "destino": destino,
                "limite_profundidad": limite,
                "exito": r["exito"],
                "total_nodos_explorados": r.get("total_nodos_explorados", 0),
                "total_rutas": r.get("total_rutas_encontradas", 0),
                "profundidad_maxima": max((p["profundidad"] for p in r.get("traza", [])), default=0),
                "demo": True,
            }
        )
        conteo["bitacora_laboratorio"] += 1
    for _ in range(round(planes * 0.3)):
        a, b = punto_en_zona(), punto_en_zona()
        if not (esta_dentro_de_zona(a) and esta_dentro_de_zona(b)):
            continue
        bd.bitacora_laboratorio.insert_one(
            {
                "tipo": "distancia",
                "creado_en": momento_aleatorio(inicio, fin),
                "modo": "geo",
                "euclidiana": round(distancia_euclidiana_km(a, b), 3),
                "manhattan": round(distancia_manhattan_km(a, b), 3),
                "demo": True,
            }
        )
        conteo["bitacora_laboratorio"] += 1

    ajustar_contadores(bd)
    return conteo


def borrar(bd: Database) -> dict:
    return {c: bd[c].delete_many({"demo": True}).deleted_count for c in COLECCIONES_DEMO}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dias", type=int, default=60, help="días hacia atrás (por defecto 60)")
    parser.add_argument("--usuarios", type=int, default=40)
    parser.add_argument("--planes", type=int, default=300)
    parser.add_argument("--borrar", action="store_true", help="borra todo lo que tenga demo: true")
    args = parser.parse_args()
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    bd = get_bd()
    if args.borrar:
        conteo = borrar(bd)
        print(f"Datos demo borrados de `{bd.name}`:")
    else:
        if args.dias < 1 or args.usuarios < 1 or args.planes < 1:
            sys.exit("--dias, --usuarios y --planes deben ser mayores que 0.")
        if bd.lugares.count_documents({"deleted_at": None}) == 0:
            sys.exit("La base no tiene lugares: corre primero python -m scripts.preparar_bd")
        conteo = sembrar(bd, args.dias, args.usuarios, args.planes)
        print(f"Actividad demo generada en `{bd.name}` (demo: true):")
    for coleccion, total in conteo.items():
        print(f"  {coleccion:<22}{total:>6}")


if __name__ == "__main__":
    main()
