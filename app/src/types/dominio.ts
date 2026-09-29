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
};

export type RespuestaRutas = { datos_suficientes: boolean; mensaje?: string; alternativas: Alternativa[] };

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
  hora?: string;
  interes?: Interes;
};

export type Recorrido = {
  titulo: string;
  puntos: PuntoRecorrido[];
  /** tramos[i] va de puntos[i] a puntos[i + 1] */
  tramos: Tramo[];
  avisos?: string[];
  fuente?: string;
  ejemplo?: boolean;
};
