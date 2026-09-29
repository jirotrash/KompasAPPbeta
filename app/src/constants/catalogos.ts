// Opciones que muestran las pantallas (textos de los mockups) y reglas de ejemplo del sistema experto.
import type { NombreIcono } from '@/components/Icono';
import type { Contexto, Interes, ModoTramo, Movilidad, Regla, TipoReporte } from '@/types/dominio';

export const CONTEXTOS: { valor: Contexto; texto: string }[] = [
  { valor: 'solo', texto: 'Solo' },
  { valor: 'pareja', texto: 'Pareja' },
  { valor: 'amigos', texto: 'Amigos' },
  { valor: 'familia', texto: 'Familia' },
];

export const TIEMPOS: { horas: number; texto: string }[] = [
  { horas: 2, texto: '2 hrs' },
  { horas: 4, texto: '4 hrs' },
  { horas: 6, texto: '6 hrs' },
  { horas: 10, texto: 'Todo el día' },
];

export const INTERESES: { valor: Interes; texto: string; icono: NombreIcono }[] = [
  { valor: 'comer', texto: 'Comer', icono: 'comer' },
  { valor: 'cafe', texto: 'Café', icono: 'cafe' },
  { valor: 'cultura', texto: 'Cultura', icono: 'cultura' },
  { valor: 'entretenimiento', texto: 'Entretenimiento', icono: 'entretenimiento' },
  { valor: 'aire_libre', texto: 'Aire libre', icono: 'aireLibre' },
];

export const iconoDeInteres = (i?: Interes): NombreIcono => INTERESES.find((x) => x.valor === i)?.icono ?? 'ubicacion';

export const MOVILIDADES: { valor: Movilidad; texto: string; icono: NombreIcono }[] = [
  { valor: 'caminando', texto: 'Caminando', icono: 'pie' },
  { valor: 'transporte_publico', texto: 'Transp. público', icono: 'autobus' },
  { valor: 'taxi_app', texto: 'Taxi/App', icono: 'taxi' },
  { valor: 'combinado', texto: 'Combinado', icono: 'combinado' },
];

export const MODOS: Record<ModoTramo, { texto: string; icono: NombreIcono }> = {
  pie: { texto: 'Caminando', icono: 'pie' },
  autobus: { texto: 'Autobús', icono: 'autobus' },
  taxi: { texto: 'Taxi', icono: 'taxi' },
  app: { texto: 'Transporte por app', icono: 'taxi' },
};

export const CATEGORIAS: Record<string, string> = {
  cafeteria: 'Café',
  restaurante: 'Restaurante',
  parque: 'Aire libre',
  museo: 'Cultura',
  cine: 'Entretenimiento',
  plaza: 'Compras',
};

export const TIPOS_PLAN = {
  equilibrado: 'Plan equilibrado',
  rapido: 'Plan rápido',
  economico: 'Plan económico',
  cercano: 'Plan cercano',
} as const;

/** Estado que da el sistema experto de Einar a cada itinerario candidato. */
export const ESTADOS_PLAN = {
  recomendable: 'Recomendable',
  pendiente_verificacion: 'Pendiente de verificar',
  descartado: 'Descartado',
  requiere_correccion: 'Requiere corrección',
} as const;

export const TIPOS_REPORTE: { valor: TipoReporte; texto: string }[] = [
  { valor: 'afluencia', texto: 'Afluencia' },
  { valor: 'cierre_total', texto: 'Cierre total' },
  { valor: 'accidente', texto: 'Accidente' },
  { valor: 'manifestacion', texto: 'Manifestación' },
];

/**
 * Reglas del sistema experto (versión de ejemplo; las definitivas las define Einar).
 * Sirven para mostrar la descripción cuando la API solo manda el id.
 */
export const REGLAS: Record<string, string> = {
  R1: 'abierto ∧ dentro_presupuesto ∧ cabe_en_tiempo → candidato',
  R2: 'candidato ∧ coincide_contexto → recomendable',
  R3: 'cierre_total_vigente ∧ reporte_verificado → descartar_ruta',
  R4: 'descartar_ruta → buscar_alternativa_documentada',
  R5: '¬datos_suficientes → avisar_sin_informacion',
  R6: 'afluencia_alta ∧ contexto_pareja → penalizar_lugar',
  R7: 'recomendable ∧ coincide_intereses → prioridad_alta',
  R8: '¬abierto → descartar_lugar',
  R9: '¬dentro_presupuesto → descartar_lugar',
  R10: '¬cabe_en_tiempo → descartar_lugar',
  R11: 'candidato ∧ ¬coincide_contexto → descartar_lugar',
  R12: 'distancia_corta ∧ caminando → ir_a_pie',
  R13: 'ruta_verificada ∧ transporte_publico → sugerir_autobus',
};

export function describirRegla(r: Regla) {
  if (typeof r === 'string') return { id: r, descripcion: REGLAS[r] ?? '' };
  return { id: r.id, descripcion: r.descripcion ?? REGLAS[r.id] ?? '' };
}
