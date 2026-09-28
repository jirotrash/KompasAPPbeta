// SIMULACIÓN del sistema experto para probar la app sin backend.
// El motor real lo programa Einar en Python (backend/app/ia). Aquí solo se imita la FORMA:
// hechos booleanos → reglas SI…ENTONCES → hasta 3 planes con explicación y reglas cumplidas.

import { REGLAS } from '@/constants/catalogos';
import type { Coordenada } from '@/constants/zona';
import type { Lugar, PeticionPlan, Plan, Regla, RespuestaPlanes, Tramo } from '@/types/dominio';
import { aHora, aMinutosDelDia, desdeGeoJSON } from '@/utils/geo';

import { elegirTramo } from './traslados';

/** Minutos que se pasan en cada tipo de lugar (supuesto del prototipo). */
const ESTANCIA_MIN: Record<string, number> = { cafeteria: 60, restaurante: 90, parque: 60, museo: 90, cine: 150, plaza: 90 };
const MAX_PARADAS = 3;

const regla = (id: string, detalle?: string) => ({ id, descripcion: detalle ? `${REGLAS[id]} (${detalle})` : REGLAS[id] });
const coordenadas = (l: Lugar) => desdeGeoJSON(l.ubicacion.coordinates);
const estancia = (l: Lugar) => ESTANCIA_MIN[l.categoria] ?? 60;

type Evaluado = { lugar: Lugar; cumplidas: Regla[]; descartes: Regla[]; puntaje: number; traslado: number };

function evaluar(lugar: Lugar, p: PeticionPlan): Evaluado {
  const tiempoMax = p.tiempo_horas * 60;
  const traslado = elegirTramo(p.origen, coordenadas(lugar), p.movilidad, p.hora_salida).duracion_min ?? 0;

  // Hechos
  const datos_suficientes = Boolean(lugar.horario && lugar.costo_promedio != null);
  const horarioDia = lugar.horario?.[p.dia];
  const llegada = aMinutosDelDia(p.hora_salida) + traslado;
  const abierto =
    !!horarioDia && llegada >= aMinutosDelDia(horarioDia[0]) && llegada + estancia(lugar) <= aMinutosDelDia(horarioDia[1]);
  const dentro_presupuesto = datos_suficientes && (lugar.costo_promedio ?? 0) <= p.presupuesto.max;
  const cabe_en_tiempo = traslado + estancia(lugar) <= tiempoMax;
  const coincide_contexto = lugar.contextos.includes(p.contexto);
  const coincide_intereses = p.intereses.length === 0 || p.intereses.includes(lugar.interes);
  const afluencia_alta = lugar.afluencia?.nivel === 'alta';

  const cumplidas: Regla[] = [];
  const descartes: Regla[] = [];
  if (!datos_suficientes) {
    return { lugar, cumplidas, descartes: [regla('R5', 'faltan horario o costo verificados')], puntaje: 0, traslado };
  }
  if (!abierto) descartes.push(regla('R8', `cerrado o sin tiempo suficiente a las ${aHora(llegada)}`));
  if (!dentro_presupuesto) descartes.push(regla('R9', `costo promedio $${lugar.costo_promedio}`));
  if (!cabe_en_tiempo) descartes.push(regla('R10', `requiere ~${traslado + estancia(lugar)} min`));

  const candidato = abierto && dentro_presupuesto && cabe_en_tiempo;
  if (candidato) {
    cumplidas.push('R1');
    if (coincide_contexto) cumplidas.push('R2');
    else descartes.push(regla('R11', `no es un lugar típico para "${p.contexto}"`));
  }
  if (candidato && coincide_contexto && !coincide_intereses) {
    descartes.push({ id: 'R7', descripcion: 'No coincide con los intereses que elegiste' });
  }

  let puntaje = (lugar.calificacion?.valor ?? 0) - traslado / 60;
  if (candidato && coincide_intereses && p.intereses.length) {
    cumplidas.push('R7');
    puntaje += 2;
  }
  if (afluencia_alta && p.contexto === 'pareja') {
    cumplidas.push(regla('R6', 'afluencia alta reportada'));
    puntaje -= 1.5;
  }
  return { lugar, cumplidas, descartes, puntaje, traslado };
}

/** Arma la secuencia origen → paradas calculando traslados, horas de llegada, costo y distancia. */
function armarPlan(seleccion: Evaluado[], p: PeticionPlan) {
  let minuto = aMinutosDelDia(p.hora_salida);
  let anterior: Coordenada = p.origen;
  const tramos: Tramo[] = [];
  const paradas = seleccion.map(({ lugar }) => {
    const tramo = elegirTramo(anterior, coordenadas(lugar), p.movilidad, aHora(minuto));
    tramos.push(tramo);
    minuto += tramo.duracion_min ?? 0;
    const llegada = aHora(minuto);
    minuto += estancia(lugar);
    anterior = coordenadas(lugar);
    return { lugar_id: lugar._id, nombre: lugar.nombre, llegada_estimada: llegada, lugar };
  });
  const duracion = minuto - aMinutosDelDia(p.hora_salida);
  const costo = seleccion.reduce((s, e) => s + (e.lugar.costo_promedio ?? 0), 0);
  const distancia = tramos.reduce((s, t) => s + (t.distancia_km ?? 0), 0);
  return { paradas, tramos, duracion, costo, distancia };
}

/** Agrega paradas en el orden dado mientras quepan en tiempo y presupuesto. */
function seleccionar(orden: Evaluado[], p: PeticionPlan, maximo: number, variedad = true) {
  const elegidos: Evaluado[] = [];
  for (const e of orden) {
    if (elegidos.length === maximo) break;
    if (variedad && elegidos.some((x) => x.lugar.interes === e.lugar.interes)) continue;
    const prueba = armarPlan([...elegidos, e], p);
    if (prueba.duracion <= p.tiempo_horas * 60 && prueba.costo <= p.presupuesto.max) elegidos.push(e);
  }
  return elegidos;
}

const EXPLICACIONES = {
  equilibrado: 'Buen balance entre calificación, variedad y distancia, dentro de tu presupuesto y tiempo.',
  rapido: 'Ideal si tienes poco tiempo: lugares cercanos y menos traslados.',
  economico: 'El de menor costo: prioriza lugares económicos o gratuitos.',
} as const;

export function inferirPlanes(lugares: Lugar[], p: PeticionPlan): RespuestaPlanes {
  const evaluados = lugares.map((l) => evaluar(l, p));
  const recomendables = evaluados.filter((e) => e.descartes.length === 0);
  const descartados = evaluados
    .filter((e) => e.descartes.length > 0)
    .map((e) => ({ lugar: e.lugar, reglas: e.descartes }));

  if (recomendables.length === 0) {
    return {
      datos_suficientes: false,
      mensaje: 'No tenemos información suficiente para armar un plan con esos datos. Prueba con otro horario, presupuesto o tiempo.',
      planes: [],
      descartados,
    };
  }

  const porPuntaje = [...recomendables].sort((a, b) => b.puntaje - a.puntaje);
  const porCercania = [...recomendables].sort((a, b) => a.traslado - b.traslado);
  const porCosto = [...recomendables].sort(
    (a, b) => (a.lugar.costo_promedio ?? 0) - (b.lugar.costo_promedio ?? 0) || b.puntaje - a.puntaje,
  );

  const propuestas = [
    { tipo: 'equilibrado' as const, seleccion: seleccionar(porPuntaje, p, MAX_PARADAS) },
    { tipo: 'rapido' as const, seleccion: seleccionar(porCercania, p, 2, false) },
    { tipo: 'economico' as const, seleccion: seleccionar(porCosto, p, MAX_PARADAS) },
  ];

  const vistos = new Set<string>();
  const planes: Plan[] = [];
  for (const { tipo, seleccion } of propuestas) {
    if (!seleccion.length) continue;
    const clave = seleccion.map((s) => s.lugar._id).sort().join('|');
    if (vistos.has(clave)) continue;
    vistos.add(clave);

    const { paradas, tramos, duracion, costo, distancia } = armarPlan(seleccion, p);
    const reglas = new Set<string>();
    seleccion.forEach((s) => s.cumplidas.forEach((r) => reglas.add(typeof r === 'string' ? r : r.id)));
    if (tramos.some((t) => t.modo === 'pie')) reglas.add('R12');
    if (tramos.some((t) => t.modo === 'autobus')) reglas.add('R13');

    planes.push({
      tipo,
      mejor_opcion: false,
      costo,
      duracion_horas: Math.round((duracion / 60) * 10) / 10,
      distancia_km: Math.round(distancia * 10) / 10,
      paradas,
      tramos,
      explicacion: EXPLICACIONES[tipo],
      reglas_cumplidas: [...reglas].sort((a, b) => Number(a.slice(1)) - Number(b.slice(1))),
    });
  }
  planes[0].mejor_opcion = true;

  return { datos_suficientes: true, planes, descartados };
}
