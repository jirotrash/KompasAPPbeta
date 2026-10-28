// Tipos de los datos que van y vienen de la API (CONTEXTO.md §6.1, §7 y §8).
import type { Coordenada } from '@/constants/zona';
import type { Dia, ParGeoJSON } from '@/utils/geo';

export type GeoPunto = { type: 'Point'; coordinates: ParGeoJSON };
export type GeoLinea = { type: 'LineString'; coordinates: ParGeoJSON[] };

export type Contexto = 'solo' | 'pareja' | 'amigos' | 'familia';
export type Interes = 'comer' | 'cafe' | 'cultura' | 'entretenimiento' | 'aire_libre';
export type Movilidad = 'caminando' | 'transporte_publico' | 'taxi_app' | 'combinado';

export type DatoConFuente<T> = T & { fuente: string; fecha: string | null };

export type Lugar = {
  _id: string;
  nombre: string;
  categoria: string;
  interes: Interes;
  municipio?: string;
  ubicacion: GeoPunto;
  horario: Partial<Record<Dia, [string, string] | null>> | null;
  costo_promedio: number | null;
  contextos: Contexto[];
  calificacion: DatoConFuente<{ valor: number }> | null;
  afluencia: DatoConFuente<{ nivel: 'baja' | 'media' | 'alta' }> | null;
  foto_url?: string | null;
};

/** La API puede mandar solo el id ("R1") o el id con su descripción. */
export type Regla = string | { id: string; descripcion?: string };

// ───────────── Traslados ─────────────

export type ModoTramo = 'pie' | 'autobus' | 'taxi' | 'app';

export type Parada = { nombre: string; ubicacion: GeoPunto };

export type Tramo = {
  modo: ModoTramo;
  duracion_min: number | null;
  distancia_km?: number | null;
  linea?: string;
  sentido?: string;
  abordaje?: Parada;
  descenso?: Parada;
  trazo?: GeoLinea;
  aviso?: string;
  /** Texto bajo el tramo en autobús (si no viene: "Incluye caminata a la parada y espera estimada."). */
  nota?: string;
};

/** Parada de una ruta de Kompás: real o "Punto N" del trazo (no se inventan nombres). km = desde el inicio de la ruta. */
export type ParadaRuta = Coordenada & { nombre: string; km: number };

/** Tramo de una opción en autobús: camina → ruta X → (transbordo) → ruta Y → camina. */
export type TramoOpcion = {
  modo: 'pie' | 'autobus';
  distancia_km: number;
  duracion_min: number;
  desde?: Coordenada;
  hasta?: Coordenada;
  id_ruta?: number;
  linea?: string;
  parada_subida?: ParadaRuta;
  parada_bajada?: ParadaRuta;
  /** [[lng, lat], ...] entre subida y bajada */
  tramo_en_ruta?: ParGeoJSON[];
  paradas_intermedias?: ParadaRuta[];
  /** Trazo completo de la ruta [[lng, lat], ...] (se dibuja tenue) */
  trazo_ruta?: ParGeoJSON[];
};

/** Respuesta de GET /api/rutas: una alternativa para ir de A a B. */
export type Alternativa = {
  id: string;
  modo: ModoTramo;
  ruta_id?: string;
  linea?: string;
  sentido?: string;
  tarifa?: number | null;
  abordaje?: Parada;
  descenso?: Parada;
  transbordos?: (Parada & { linea: string })[];
  tiempos: { caminata: number | null; espera: number | null; trayecto: number | null; transbordos?: number | null };
  distancia_km?: number;
  tipo_horario?: 'programado' | 'actualizado' | null;
  trazo?: GeoLinea;
  fuente: string;
  fecha_verificacion: string | null;
  reglas_cumplidas?: Regla[];
  avisos?: string[];
  ejemplo?: boolean;
  // Opcionales (v0.6): opciones en autobús directas o combinadas con transbordo
  tipo?: 'directo' | 'combinado';
  id_ruta?: number;
  parada_subida?: ParadaRuta;
  parada_bajada?: ParadaRuta;
  tramo_en_ruta?: ParGeoJSON[];
  paradas_intermedias?: ParadaRuta[];
  numero_transbordos?: number;
  tramos?: TramoOpcion[];
};

export type RespuestaRutas = { datos_suficientes: boolean; mensaje?: string; alternativas: Alternativa[] };

// ───────────── Demostración académica DFS ─────────────

export type ParadaDFS = { id: string; nombre: string; lat: number; lng: number };

export type TramoDFS = { de: string; a: string; linea: string; modo: string; tiempo_min: number };

export type RutaDFS = {
  paradas: string[];
  nodos_id: string[];
  tiempo_total_minutos: number;
  numero_transbordos: number;
  tramos: TramoDFS[];
};

export type PasoDFS = {
  paso: number;
  tipo: 'visita' | 'avanza' | 'objetivo' | 'limite' | 'ciclo_evitado' | 'retroceso';
  nodo: string;
  hacia?: string | null;
  profundidad: number;
  camino: string[];
  mensaje: string;
};

/** Respuesta del backend para la demostración; nunca representa una ruta operativa. */
export type RespuestaDFS = {
  exito: boolean;
  fuente: string;
  datos_verificados: boolean;
  mensaje?: string | null;
  aviso?: string | null;
  orden_exploracion: string[];
  traza: PasoDFS[];
  total_nodos_explorados: number;
  total_rutas_encontradas: number;
  rutas: RutaDFS[];
};

// ───────────── Laboratorio de métricas de distancia ─────────────

export type PuntoPlano = { x: number; y: number };

export type ComparacionDistancias = {
  a: PuntoPlano;
  b: PuntoPlano;
  esquina: PuntoPlano;
  horizontal: number;
  vertical: number;
  euclidiana: number;
  manhattan: number;
  diferencia: number;
  alineados: boolean;
  pasos: { euclidiana: string; manhattan: string };
};

/** GET /api/distancias/geo: las mismas métricas con coordenadas reales (km). */
export type ComparacionGeo = {
  origen: { lat: number; lng: number };
  destino: { lat: number; lng: number };
  /** Vuelta del recorrido Manhattan: latitud del origen, longitud del destino. */
  esquina: { lat: number; lng: number };
  este_oeste_km: number;
  norte_sur_km: number;
  linea_recta_km: number;
  euclidiana_km: number;
  manhattan_km: number;
  diferencia_km: number;
  minutos_caminando_recta: number;
  minutos_caminando_calles: number;
  pasos: { euclidiana: string; manhattan: string };
  nota: string;
};

// ───────────── Planes (sistema experto) ─────────────

export type PeticionPlan = {
  contexto: Contexto;
  presupuesto: { min: number; max: number };
  tiempo_horas: number;
  intereses: Interes[];
  movilidad: Movilidad[];
  origen: Coordenada;
  hora_salida: string;
  dia: Dia;
};

export type ParadaPlan = { lugar_id: string; nombre: string; llegada_estimada: string; lugar?: Lugar };

export type EstadoPlan = 'recomendable' | 'pendiente_verificacion' | 'descartado' | 'requiere_correccion';

export type Plan = {
  /** "economico" solo lo usa el modo demostración; la API manda equilibrado, rapido o cercano */
  tipo: 'equilibrado' | 'rapido' | 'economico' | 'cercano';
  estado?: EstadoPlan;
  /** Puntuación de preferencias del motor de Einar (0–6) */
  puntuacion?: number;
  /** Suma estimada por persona según el rango de precios de Google; no es una cotización */
  rango_costo?: { min: number | null; max: number | null; moneda: 'MXN' } | null;
  mejor_opcion: boolean;
  /** null mientras la base no tenga costos de los lugares */
  costo: number | null;
  duracion_horas: number;
  distancia_km: number;
  paradas: ParadaPlan[];
  /** Traslados entre paradas (origen→1, 1→2…). Si no vienen, la app los calcula a pie o en auto. */
  tramos?: Tramo[];
  explicacion: string;
  reglas_cumplidas: Regla[];
};

/** Candidato que no se recomendó. La API manda el itinerario (nombre, estado, datos faltantes);
 *  el modo demostración manda el lugar descartado. */
export type Descartado = {
  reglas: Regla[];
  tipo?: Plan['tipo'];
  nombre?: string;
  lugares?: string[];
  estado?: Exclude<EstadoPlan, 'recomendable'>;
  datos_faltantes?: string[];
  lugar?: Lugar;
};

export type RespuestaPlanes = {
  datos_suficientes?: boolean;
  mensaje?: string | null;
  /** Advertencias del motor y de los hechos (p. ej. R13: no se verifican cierres) */
  aviso?: string | null;
  version_reglas?: string;
  planes: Plan[];
  descartados?: Descartado[];
};

// ───────────── Reportes ─────────────

export type TipoReporte = 'afluencia' | 'cierre_total' | 'accidente' | 'manifestacion';

export type Reporte = {
  _id: string;
  tipo: TipoReporte;
  nivel_afluencia?: 'baja' | 'media' | 'alta';
  ubicacion: GeoPunto;
  ruta_id?: string;
  lugar_id?: string;
  observado_en: string;
  vigente_hasta: string;
  confirmaciones: number;
  estado: 'pendiente' | 'verificado' | 'descartado';
  comentario?: string;
};

export type NuevoReporte = Omit<Reporte, '_id' | 'vigente_hasta' | 'confirmaciones' | 'estado'>;

// ───────────── Solicitudes de rutas ─────────────

/** La persona pide una ruta que falta cuando "¿Cómo llego?" no encontró camión. El equipo la atiende en el panel. */
export type SolicitudRuta = {
  id: string;
  origen: GeoPunto;
  destino: GeoPunto;
  comentario: string | null;
  estado: 'pendiente' | 'atendida' | 'descartada';
  nota_admin: string | null;
  creado_en: string;
};

// ───────────── Sesión ─────────────

export type Usuario = {
  id: number;
  nombre: string;
  primer_apellido?: string;
  segundo_apellido?: string | null;
  /** AAAA-MM-DD */
  fecha_nacimiento?: string | null;
  email: string;
  rol: string;
};

/** Lo que manda la pantalla de registro a POST /api/auth/register. */
export type NuevoUsuario = {
  nombre: string;
  primer_apellido: string;
  segundo_apellido?: string;
  email: string;
  password: string;
  /** AAAA-MM-DD */
  fecha_nacimiento: string;
};
export type Sesion = { token: string; usuario: Usuario };

// ───────────── Recorrido que se dibuja en la pestaña Mapa ─────────────

export type PuntoRecorrido = Coordenada & {
  nombre: string;
  tipo: 'origen' | 'lugar' | 'parada' | 'destino';
  /** Solo en paradas de autobús: dónde subir, dónde bajar o dónde transbordar (el mapa las distingue). */
  rol?: 'subida' | 'bajada' | 'transbordo';
  hora?: string;
  interes?: Interes;
};

export type Recorrido = {
  titulo: string;
  puntos: PuntoRecorrido[];
  /** tramos[i] va de puntos[i] a puntos[i + 1] */
  tramos: Tramo[];
  /** Rutas de autobús completas (se dibujan tenues; el tramo en autobús va resaltado en `tramos`). */
  trazosRuta?: GeoLinea[];
  /** Paradas intermedias del tramo en autobús (puntos pequeños). */
  intermedias?: (Coordenada & { nombre: string })[];
  avisos?: string[];
  fuente?: string;
  ejemplo?: boolean;
};

// ───────────── Asistente (Ollama, a través de la API) ─────────────

export type EstadoAsistente = { disponible: boolean; modelo: string; modelo_instalado?: boolean };

export type PuntoNombrado = Coordenada & { nombre: string };

/** Ruta o plan que regresó el asistente. Las de conversaciones guardadas solo traen la referencia. */
export type TarjetaAsistente = {
  tipo: 'ruta' | 'plan';
  titulo: string;
  subtitulo?: string | null;
  id_ruta?: number | null;
  id_plan?: number | null;
  origen?: PuntoNombrado | null;
  destino?: PuntoNombrado | null;
  alternativa?: Alternativa | null;
  plan?: Plan | null;
  /** Destino como lo escribió el usuario (tarjetas de conversaciones guardadas) */
  destino_texto?: string | null;
  ejemplo?: boolean;
};

export type MensajeChat = {
  rol: 'usuario' | 'asistente' | 'herramienta' | 'error';
  contenido?: string | null;
  nombre?: string | null;
  duracion_ms?: number | null;
  tarjeta?: TarjetaAsistente | null;
  creado_en: string;
};

export type ResumenConversacion = { id: string; titulo: string | null; ultimo_mensaje: string | null; fecha: string; total_mensajes: number };

export type Conversacion = {
  id: string;
  titulo: string | null;
  modelo: string;
  mensajes: MensajeChat[];
  planes_creados: number[];
  created_at: string;
  updated_at: string;
};

/** POST /api/asistente/conversaciones/{id}/mensajes */
export type RespuestaMensaje = {
  conversacion_id: string;
  titulo: string | null;
  mensaje: MensajeChat;
  tarjetas: TarjetaAsistente[];
  herramientas_usadas: string[];
};
