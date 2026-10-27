"""Modelos de salida del dashboard (todo viene agregado desde MongoDB)."""

from datetime import date

from pydantic import BaseModel, Field


class Periodo(BaseModel):
    desde: date
    hasta: date = Field(description="Incluye el día completo")
    incluir_demo: bool


class SalidaDashboard(BaseModel):
    periodo: Periodo
    incluye_demo: bool = Field(description="True si en el periodo hay datos de demostración (demo: true)")


class Kpis(SalidaDashboard):
    usuarios_totales: int = Field(description="Usuarios registrados hasta el fin del periodo")
    usuarios_nuevos: int
    planes: int
    planes_evaluados: int = Field(description="Planes que guardaron la evaluación del sistema experto")
    porcentaje_con_recomendacion: float = Field(description="% de planes evaluados con al menos un candidato recomendable")
    recorridos: int
    tiempo_promedio_recorrido_min: float | None
    reportes_vigentes: int = Field(description="Vigentes en este momento")
    lugares: int


class PuntoSerie(BaseModel):
    fecha: date = Field(description="Inicio del día, semana (lunes) o mes")
    usuarios: int
    planes: int
    recorridos: int


class InteresesSerie(BaseModel):
    fecha: date
    comer: int
    cafe: int
    cultura: int
    entretenimiento: int
    aire_libre: int


class Series(SalidaDashboard):
    agrupar: str
    serie: list[PuntoSerie]
    planes_por_interes: list[InteresesSerie]


class ConteoInteres(BaseModel):
    interes: str
    total: int


class ConteoMovilidad(BaseModel):
    movilidad: str
    total: int


class ConteoContexto(BaseModel):
    contexto: str
    total: int


class BarraPresupuesto(BaseModel):
    rango: str
    desde: int = Field(description="Pesos por persona (límite inferior)")
    total: int


class BarraTiempo(BaseModel):
    rango: str
    desde_min: int
    total: int


class CeldaDiaHora(BaseModel):
    dia: int = Field(ge=1, le=7, description="1 = lunes … 7 = domingo (ISO)")
    hora: int = Field(ge=0, le=23)
    total: int


class PerfilInteres(BaseModel):
    interes: str
    solo: int
    pareja: int
    amigos: int
    familia: int


class Planes(SalidaDashboard):
    total: int
    por_interes: list[ConteoInteres]
    por_movilidad: list[ConteoMovilidad]
    por_contexto: list[ConteoContexto]
    presupuesto: list[BarraPresupuesto]
    tiempo_disponible: list[BarraTiempo]
    dia_hora: list[CeldaDiaHora]
    interes_por_contexto: list[PerfilInteres]


class ConteoEstado(BaseModel):
    estado: str
    total: int


class ReglaActivada(BaseModel):
    id: str
    descripcion: str | None
    total: int


class PuntuacionTipo(BaseModel):
    tipo: str
    promedio: float | None
    minimo: float | None
    maximo: float | None
    total: int


class ConteoVersion(BaseModel):
    version: str
    total: int


class SistemaExperto(SalidaDashboard):
    por_estado: list[ConteoEstado]
    reglas_top: list[ReglaActivada]
    puntuacion_por_tipo: list[PuntuacionTipo]
    sin_datos_suficientes: int = Field(description="Planes en los que el motor no tuvo datos para recomendar")
    por_version: list[ConteoVersion]


class ParadaUso(BaseModel):
    id_ruta: int | None
    nombre: str
    lat: float
    lng: float
    subidas: int
    bajadas: int
    total: int



class TiemposTransporte(BaseModel):
    transporte: str
    clave: str
    total: int
    promedio: float | None
    minimo: int | None
    maximo: int | None


class RutaUsada(BaseModel):
    id_ruta: int
    ruta: str
    total: int
    promedio: float | None


class Movilidad(SalidaDashboard):
    por_transporte: list[TiemposTransporte]
    rutas_top: list[RutaUsada]
    paradas_uso: list[ParadaUso] = Field(default=[], description="Paradas donde más se sube y se baja (mapa de calor)")


class ReportesTipo(BaseModel):
    tipo: str
    pendiente: int
    verificado: int
    descartado: int


class VigentesVencidos(BaseModel):
    vigentes: int
    vencidos: int


class PuntoReporte(BaseModel):
    lat: float
    lng: float
    tipo: str
    estado: str | None = None
    vigente: bool


class Reportes(SalidaDashboard):
    por_tipo_estado: list[ReportesTipo]
    vigentes_vs_vencidos: VigentesVencidos
    puntos: list[PuntoReporte] = Field(description="Máximo 500, los más recientes")


class ConteoCategoria(BaseModel):
    categoria: str
    total: int


class PuntoLugar(BaseModel):
    id: int
    nombre: str
    lat: float
    lng: float
    categoria: str | None


class Lugares(SalidaDashboard):
    por_categoria: list[ConteoCategoria]
    puntos: list[PuntoLugar]


class AlgoritmoBusqueda(BaseModel):
    algoritmo: str
    heuristica: str | None
    etiqueta: str = Field(description="Nombre para la gráfica, p. ej. A* (Manhattan)")
    consultas: int
    nodos_promedio: float | None
    costo_promedio_km: float | None
    costo_optimo_promedio_km: float | None
    razon_vs_optimo: float | None = Field(description="Costo del camino ÷ costo óptimo (1 = óptimo)")
    porcentaje_optimo: float | None
    ms_promedio: float | None


class PuntoConvergencia(BaseModel):
    generacion: int
    mejor: float = Field(description="Mejor aptitud promedio entre ejecuciones")
    promedio: float | None = Field(description="Aptitud promedio de la población, promediada entre ejecuciones")
    ejecuciones: int


class AhorroGenetico(BaseModel):
    tipo_plan: str
    planes: int
    reordenados: int
    km_antes: float
    km_despues: float
    km_ahorrados: float


class ResumenTransbordos(BaseModel):
    consultas: int
    encontrados: int
    nodos_explorados_promedio: float | None
    nodos_grafo_promedio: float | None
    ms_promedio: float | None



class BurbujaDFS(BaseModel):
    limite_profundidad: int
    nodos: int = Field(description="Nodos explorados")
    rutas: float | None = Field(description="Rutas encontradas (promedio de las consultas agrupadas)")
    consultas: int


class ParDFS(BaseModel):
    par: str
    total: int


class PuntoDistancia(BaseModel):
    modo: str | None
    euclidiana: float
    manhattan: float


class Laboratorio(SalidaDashboard):
    dfs_puntos: list[BurbujaDFS]
    dfs_pares_top: list[ParDFS]
    distancias_puntos: list[PuntoDistancia]
    busqueda_algoritmos: list[AlgoritmoBusqueda] = []
    genetico_convergencia: list[PuntoConvergencia] = []
    genetico_ahorro: list[AhorroGenetico] = []
    transbordos: ResumenTransbordos | None = None


class ConteoDia(BaseModel):
    fecha: date
    conversaciones: int
    mensajes: int


class ConteoHerramienta(BaseModel):
    herramienta: str
    total: int


class TiempoRespuesta(BaseModel):
    respuestas: int
    promedio_ms: float | None
    p90_ms: float | None


class ErroresAsistente(BaseModel):
    respuestas: int
    errores: int
    porcentaje_error: float


class ConteoOrigen(BaseModel):
    origen: str
    total: int


class Asistente(SalidaDashboard):
    por_dia: list[ConteoDia]
    herramientas: list[ConteoHerramienta]
    tiempo_respuesta: TiempoRespuesta
    errores: ErroresAsistente
    planes_por_origen: list[ConteoOrigen]
