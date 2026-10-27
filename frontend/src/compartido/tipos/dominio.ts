// Tipos de los datos que van y vienen de la API. Copiados de la app móvil (app/src/types/dominio.ts)
// en lo que aplica a la web; el modo mock (src/mock) cumple los mismos tipos.

export type Coordenada = { lat: number; lng: number }
/** GeoJSON (MongoDB): [lng, lat]. */
export type ParGeoJSON = [number, number]
/** Leaflet: [lat, lng]. */
export type ParLeaflet = [number, number]

export type GeoPunto = { type: 'Point'; coordinates: ParGeoJSON }
export type GeoLinea = { type: 'LineString'; coordinates: ParGeoJSON[] }

export type Dia = 'dom' | 'lun' | 'mar' | 'mie' | 'jue' | 'vie' | 'sab'
export type DatoConFuente<T> = T & { fuente: string; fecha: string | null }

// ───────────── Lugares ─────────────

export type Lugar = {
  _id: string
  nombre: string
  categoria: string
  municipio?: string
  ubicacion: GeoPunto
  horario: Partial<Record<Dia, [string, string] | null>> | null
  costo_promedio: number | null
  contextos: string[]
  calificacion: DatoConFuente<{ valor: number }> | null
  afluencia: DatoConFuente<{ nivel: 'baja' | 'media' | 'alta' }> | null
  foto_url?: string | null
}

/** La API puede mandar solo el id ("R1") o el id con su descripción. */
export type Regla = string | { id: string; descripcion?: string }
export type ReglaDescrita = { id: string; descripcion: string }

// ───────────── Rutas ─────────────

export type ModoTramo = 'pie' | 'autobus' | 'taxi' | 'app'

export type Parada = { nombre: string; ubicacion: GeoPunto }

/** Parada de una ruta de Kompás: real o "Punto N" del trazo. km = desde el inicio de la ruta. */
export type ParadaRuta = Coordenada & { nombre: string; km: number }

/** Tramo de una opción en autobús: camina → ruta X → (transbordo) → ruta Y → camina. */
export type TramoOpcion = {
  modo: 'pie' | 'autobus'
  distancia_km: number
  duracion_min: number
  desde?: Coordenada
  hasta?: Coordenada
  id_ruta?: number
  linea?: string
  parada_subida?: ParadaRuta
  parada_bajada?: ParadaRuta
  /** [[lng, lat], ...] entre subida y bajada */
  tramo_en_ruta?: ParGeoJSON[]
  paradas_intermedias?: ParadaRuta[]
  /** Trazo completo de la ruta [[lng, lat], ...] */
  trazo_ruta?: ParGeoJSON[]
}

export type Tiempos = {
  caminata: number | null
  espera: number | null
  trayecto: number | null
  transbordos?: number | null
}

/** Una opción de GET /api/rutas?origen=&destino= para ir de A a B. */
export type Alternativa = {
  id: string
  modo: ModoTramo
  ruta_id?: string
  linea?: string
  sentido?: string
  tarifa?: number | null
  abordaje?: Parada
  descenso?: Parada
  transbordos?: (Parada & { linea: string })[]
  tiempos: Tiempos
  distancia_km?: number
  tipo_horario?: 'programado' | 'actualizado' | null
  trazo?: GeoLinea
  fuente: string
  fecha_verificacion: string | null
  reglas_cumplidas?: Regla[]
  avisos?: string[]
  ejemplo?: boolean
  // v0.6 (opcionales): opciones en autobús directas o combinadas
  tipo?: 'directo' | 'combinado'
  id_ruta?: number
  parada_subida?: ParadaRuta
  parada_bajada?: ParadaRuta
  tramo_en_ruta?: ParGeoJSON[]
  paradas_intermedias?: ParadaRuta[]
  numero_transbordos?: number
  tramos?: TramoOpcion[]
}

export type RespuestaRutas = { datos_suficientes: boolean; mensaje?: string | null; alternativas: Alternativa[] }

/** Ruta de ejemplo del modo mock (la API real solo guarda el trazo). */
export type RutaEjemplo = {
  _id: string
  linea: string
  sentido: string
  tarifa: number | null
  horario: { inicio: string; fin: string; frecuencia_min: number; tipo: 'programado' }
  paradas: { orden: number; nombre: string; ubicacion: GeoPunto }[]
  verificada: boolean
  fuente: string
  fecha_verificacion: string | null
}

/** GET /api/rutas (sin parámetros): trazos de la colección `rutas`. */
export type Ruta = { id: number; _id: string; nombre?: string; trazo: ParGeoJSON[]; paradas?: Parada[] }

/** Parada en el árbol binario de una ruta (GET /api/rutas/{id}/arbol). */
export type ParadaArbol = Coordenada & { km: number; id: string; nombre: string }

export type NodoArbol = { clave: number; parada: Omit<ParadaArbol, 'km'>; izquierdo: NodoArbol | null; derecho: NodoArbol | null }

export type ArbolRuta = {
  id_ruta: number
  nombre: string
  paradas_reales: boolean
  raiz: NodoArbol | null
  altura: number
  total_nodos: number
  inorden: ParadaArbol[]
  preorden: ParadaArbol[]
  postorden: ParadaArbol[]
}

// ───────────── Itinerarios (simulación del sistema experto en la web) ─────────────

export type PeticionItinerario = {
  contexto: string
  presupuesto: number
  tiempo_min: number
  gustos: string[]
  hora: string
  dia: Dia
  origen: Coordenada
}

export type Itinerario = {
  id: string
  titulo: string
  lugares: Lugar[]
  costo_total: number
  tiempo_total_min: number
  reglas_cumplidas: ReglaDescrita[]
  explicacion: string
}

export type LugarDescartado = { lugar: Lugar; reglas: ReglaDescrita[] }

export type RespuestaItinerarios = {
  datos_suficientes: boolean
  mensaje?: string
  itinerarios: Itinerario[]
  descartados: LugarDescartado[]
}

// ───────────── Reportes ─────────────

export type TipoReporte = 'afluencia' | 'cierre_total' | 'accidente' | 'manifestacion'

export type Reporte = {
  _id: string
  tipo: TipoReporte
  nivel_afluencia?: 'baja' | 'media' | 'alta'
  ubicacion: GeoPunto
  ruta_id?: string
  lugar_id?: string
  observado_en: string
  vigente_hasta: string
  usuario_id?: number
  confirmaciones: number
  estado: 'pendiente' | 'verificado' | 'descartado'
  comentario?: string
}

export type NuevoReporte = Omit<Reporte, '_id' | 'vigente_hasta' | 'confirmaciones' | 'estado' | 'usuario_id'>

// ───────────── Sesión ─────────────

export type Usuario = {
  id: number
  nombre: string
  primer_apellido?: string
  segundo_apellido?: string | null
  fecha_nacimiento?: string | null
  email: string
  rol: string
}

export type Sesion = { token: string; usuario: Usuario }

export type Credenciales = { email: string; password: string }
export type NuevoUsuario = Credenciales & { nombre: string }

// ───────────── Servicios de mapas (OpenStreetMap) ─────────────

export type Direccion = Coordenada & { id: string; nombre: string; detalle: string; municipio?: string }

export type TrazoCalles = { trazo: GeoLinea; distancia_km: number; duracion_min: number }
