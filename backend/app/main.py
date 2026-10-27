"""API de Kompás. Levantar con:  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Arquitectura en capas por módulos (ARQUITECTURA.md): router → servicio → repositorio → MongoDB.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modulos.catalogos import router as catalogos
from app.modulos.cuenta import router as cuenta
from app.modulos.dashboard import router as dashboard
from app.modulos.historial import router as historial
from app.modulos.itinerarios import router as itinerarios
from app.modulos.laboratorio import router as laboratorio
from app.modulos.lugares import router as lugares
from app.modulos.reportes import router as reportes
from app.modulos.rutas import router as rutas
from app.nucleo.bd import bd_disponible
from app.nucleo.config import get_settings
from app.nucleo.errores import registrar_manejadores

app = FastAPI(
    title="Kompás API",
    description="Movilidad y planes de salida en Toluca, Lerma y San Mateo Atenco. "
    "Los tiempos son estimaciones calculadas por distancia.",
    version="0.5.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().lista_cors,
    # El token viaja en el encabezado Authorization, no en cookies
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

registrar_manejadores(app)


@app.get("/api/salud", tags=["Salud"])
def salud() -> dict:
    """Prueba de conexión para la app. `bd` indica si MongoDB responde."""
    return {"ok": True, "bd": bd_disponible()}


for router in (
    cuenta.router,
    cuenta.router_residencia,
    catalogos.router,
    lugares.router,
    rutas.router,
    itinerarios.router,
    historial.router,
    reportes.router,
    laboratorio.router_dfs,
    laboratorio.router_distancias,
    laboratorio.router_busqueda,
    laboratorio.router_genetico,
    dashboard.router,
):
    app.include_router(router)
