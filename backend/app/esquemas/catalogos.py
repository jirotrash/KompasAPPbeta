from pydantic import BaseModel, Field


class CategoriaSalida(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    clave: str = Field(description="Valor que usa la app: comer, cafe, cultura, entretenimiento, aire_libre")


class TransporteSalida(BaseModel):
    id: int
    nombre: str
    clave: str = Field(description="Valor que usa la app: caminando, transporte_publico, taxi_app, combinado")
