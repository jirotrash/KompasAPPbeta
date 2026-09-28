"""API de Kompás. Levantar con:  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import bd_disponible
from app.routers import auth, catalogos, historial, itinerarios, lugares, rutas

app = FastAPI(
    title="Kompás API",
    description="Movilidad y planes de salida en Toluca, Lerma y San Mateo Atenco. "
    "Los tiempos son estimaciones calculadas por distancia.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().lista_cors,
    # El token viaja en el encabezado Authorization, no en cookies
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def error_de_validacion(_: Request, exc: RequestValidationError) -> JSONResponse:
    """La app solo muestra `detail` si es texto, así que se resume la lista de errores de Pydantic."""
    mensajes = []
    for error in exc.errors():
        campo = ".".join(str(parte) for parte in error["loc"] if parte != "body")
        mensajes.append(f"{campo}: {error['msg']}" if campo else error["msg"])
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": "Revisa los datos enviados. " + "; ".join(mensajes)},
    )


@app.get("/api/salud", tags=["Salud"])
def salud() -> dict:
    """Prueba de conexión para la app. `bd` indica si MySQL responde."""
    return {"ok": True, "bd": bd_disponible()}


for router in (auth.router, auth.router_residencia, catalogos.router, lugares.router, rutas.router, itinerarios.router, historial.router):
    app.include_router(router)
