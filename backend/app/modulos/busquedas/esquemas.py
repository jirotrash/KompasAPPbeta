from datetime import datetime

from pydantic import BaseModel, Field

from app.nucleo.esquemas_comunes import GeoPunto


class BusquedaSalida(BaseModel):
    """Una consulta de "¿Cómo llego?" que hizo alguien en la app (GET /api/rutas?origen=&destino=)."""

    id: str = Field(description="ObjectId como texto")
    id_usuario: int | None = Field(description="null si se buscó sin sesión")
    origen: GeoPunto
    destino: GeoPunto
    datos_suficientes: bool = Field(description="false: ninguna ruta de Kompás conectaba origen y destino")
    opciones_autobus: int
    rutas: list[int] = Field(description="Ids de las rutas que se sugirieron")
    distancia_km: float | None = Field(description="Estimación por calles entre origen y destino")
    creado_en: datetime
