from pydantic import Field

from app.esquemas.comun import GeoPunto, Salida


class LugarSalida(Salida):
    id: int
    id_texto: str = Field(alias="_id", description="El mismo id como texto (lo usa la app)")
    nombre: str
    lat: float
    lng: float
    ubicacion: GeoPunto
    categoria: str | None = Field(description="Nombre de la categoría (tabla categorias)")
    interes: str | None = Field(description="Valor de la app: comer, cafe, cultura, entretenimiento, aire_libre")
    distancia_km: float | None = Field(default=None, description="En línea recta desde lat/lng o `cerca`")
    minutos_caminando: int | None = Field(default=None, description="Estimación: ≈ 12 min por km")
    horario: None = Field(default=None, description="Sin dato: la base aún no lo tiene")
    costo_promedio: None = Field(default=None, description="Sin dato: la base aún no lo tiene")
    calificacion: None = Field(default=None, description="Sin dato: la base aún no lo tiene")
    afluencia: None = None
    foto_url: None = Field(default=None, description="Sin dato: la base aún no lo tiene")
    contextos: list[str] = []
