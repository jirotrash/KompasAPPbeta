// Convierte lo que regresa la API (un plan o una alternativa de ruta) en un "recorrido" que la
// pestaña Mapa sabe dibujar: puntos numerados + tramos entre ellos (a pie, autobús, taxi).
import { TIPOS_PLAN } from '@/constants/catalogos';
import type { Coordenada } from '@/constants/zona';
import type { Alternativa, ParadaRuta, Plan, PuntoRecorrido, Recorrido, Tramo, TramoOpcion } from '@/types/dominio';

import { aHora, aMinutosDelDia, desdeGeoJSON, distanciaKm, FACTOR_CALLES, VELOCIDAD_KMH } from './geo';

const NOTA_SIN_ESPERA = 'Tiempo de trayecto estimado; no incluye la espera (la ruta no tiene horario verificado).';

type Origen = Coordenada & { nombre: string };

export function recorridoDesdePlan(plan: Plan, origen: Origen, horaSalida: string): Recorrido {
  const puntos: PuntoRecorrido[] = [
    { ...origen, tipo: 'origen', hora: horaSalida },
    ...plan.paradas.map((p): PuntoRecorrido => {
      const coords = p.lugar ? desdeGeoJSON(p.lugar.ubicacion.coordinates) : origen;
      return { ...coords, nombre: p.nombre, tipo: 'lugar', hora: p.llegada_estimada, interes: p.lugar?.interes };
    }),
  ];
  // Si la API no manda los tramos, se estiman caminando entre paradas
  const tramos: Tramo[] =
    plan.tramos ??
    puntos.slice(1).map((p, i) => {
      const km = distanciaKm(puntos[i], p) * FACTOR_CALLES;
      return { modo: 'pie', distancia_km: km, duracion_min: Math.round((km / VELOCIDAD_KMH.pie) * 60) };
    });

  return {
    titulo: TIPOS_PLAN[plan.tipo],
    puntos,
    // Los avisos de cada traslado ya se muestran dentro de su tramo
    tramos,
  };
}

export function recorridoDesdeAlternativa(
  a: Alternativa,
  origen: Origen,
  destino: Origen,
  horaSalida: string,
): Recorrido {
  const salida = aMinutosDelDia(horaSalida);
  const base = { avisos: a.avisos, fuente: a.fuente, ejemplo: a.ejemplo };

  // Opciones de la API v0.6: tramos con subida, bajada (del árbol de paradas), tramo en ruta e intermedias
  const buses = (a.tramos ?? []).filter((t) => t.modo === 'autobus' && t.parada_subida && t.parada_bajada);
  if (a.modo === 'autobus' && buses.length) return recorridoEnAutobus(a, buses, origen, destino, salida, base);

  if (a.modo === 'autobus' && a.abordaje && a.descenso) {
    const sube = desdeGeoJSON(a.abordaje.ubicacion.coordinates);
    const baja = desdeGeoJSON(a.descenso.ubicacion.coordinates);
    const kmIda = distanciaKm(origen, sube) * FACTOR_CALLES;
    const kmVuelta = distanciaKm(baja, destino) * FACTOR_CALLES;
    const caminaIda = Math.round((kmIda / VELOCIDAD_KMH.pie) * 60);
    const caminaVuelta = Math.round((kmVuelta / VELOCIDAD_KMH.pie) * 60);
    const enParada = salida + caminaIda;
    const enDescenso = enParada + (a.tiempos.espera ?? 0) + (a.tiempos.trayecto ?? 0);
    return {
      ...base,
      titulo: `${a.linea ?? 'Autobús'} · ${destino.nombre}`,
      puntos: [
        { ...origen, tipo: 'origen', hora: horaSalida },
        { ...sube, nombre: a.abordaje.nombre, tipo: 'parada', hora: aHora(enParada) },
        { ...baja, nombre: a.descenso.nombre, tipo: 'parada', hora: aHora(enDescenso) },
        { ...destino, tipo: 'destino', hora: aHora(enDescenso + caminaVuelta) },
      ],
      tramos: [
        { modo: 'pie', duracion_min: caminaIda, distancia_km: kmIda },
        {
          modo: 'autobus',
          duracion_min: (a.tiempos.espera ?? 0) + (a.tiempos.trayecto ?? 0),
          linea: a.linea,
          sentido: a.sentido,
          abordaje: a.abordaje,
          descenso: a.descenso,
          trazo: a.trazo,
        },
        { modo: 'pie', duracion_min: caminaVuelta, distancia_km: kmVuelta },
      ],
    };
  }

  const total = (a.tiempos.caminata ?? 0) + (a.tiempos.espera ?? 0) + (a.tiempos.trayecto ?? 0);
  return {
    ...base,
    titulo: destino.nombre,
    puntos: [
      { ...origen, tipo: 'origen', hora: horaSalida },
      { ...destino, tipo: 'destino', hora: aHora(salida + total) },
    ],
    tramos: [{ modo: a.modo, duracion_min: total, distancia_km: a.distancia_km, trazo: a.trazo }],
  };
}

/** Camina → ruta X → (transbordo a pie) → ruta Y → camina, con los tiempos estimados de la API. */
function recorridoEnAutobus(
  a: Alternativa,
  buses: TramoOpcion[],
  origen: Origen,
  destino: Origen,
  salida: number,
  base: Pick<Recorrido, 'avisos' | 'fuente' | 'ejemplo'>,
): Recorrido {
  const caminar = (desde: Coordenada, hasta: Coordenada): Tramo => {
    const km = distanciaKm(desde, hasta) * FACTOR_CALLES;
    return { modo: 'pie', duracion_min: Math.max(1, Math.round((km / VELOCIDAD_KMH.pie) * 60)), distancia_km: km };
  };
  // Caminatas que manda la API, en orden (antes del primer autobús, entre autobuses y al final)
  const caminatas = (a.tramos ?? []).filter((t) => t.modo === 'pie');
  const pie = (i: number, desde: Coordenada, hasta: Coordenada): Tramo =>
    caminatas[i] ? { modo: 'pie', duracion_min: caminatas[i].duracion_min, distancia_km: caminatas[i].distancia_km } : caminar(desde, hasta);

  let reloj = salida;
  const puntos: PuntoRecorrido[] = [{ ...origen, tipo: 'origen', hora: aHora(reloj) }];
  const tramos: Tramo[] = [];
  let anterior: Coordenada = origen;
  buses.forEach((t, i) => {
    const sube = t.parada_subida as ParadaRuta;
    const baja = t.parada_bajada as ParadaRuta;
    const caminata = pie(i, anterior, sube);
    tramos.push(caminata);
    reloj += caminata.duracion_min ?? 0;
    puntos.push({ lat: sube.lat, lng: sube.lng, nombre: sube.nombre, tipo: 'parada', rol: i === 0 ? 'subida' : 'transbordo', hora: aHora(reloj) });
    tramos.push({
      modo: 'autobus',
      duracion_min: t.duracion_min,
      distancia_km: t.distancia_km,
      linea: t.linea,
      abordaje: { nombre: sube.nombre, ubicacion: { type: 'Point', coordinates: [sube.lng, sube.lat] } },
      descenso: { nombre: baja.nombre, ubicacion: { type: 'Point', coordinates: [baja.lng, baja.lat] } },
      trazo: t.tramo_en_ruta?.length ? { type: 'LineString', coordinates: t.tramo_en_ruta } : undefined,
      nota: a.tiempos.espera == null ? NOTA_SIN_ESPERA : undefined,
    });
    reloj += t.duracion_min;
    puntos.push({ lat: baja.lat, lng: baja.lng, nombre: baja.nombre, tipo: 'parada', rol: i === buses.length - 1 ? 'bajada' : 'transbordo', hora: aHora(reloj) });
    anterior = baja;
  });
  const final = pie(buses.length, anterior, destino);
  tramos.push(final);
  puntos.push({ ...destino, tipo: 'destino', hora: aHora(reloj + (final.duracion_min ?? 0)) });

  return {
    ...base,
    titulo: `${a.linea ?? 'Autobús'} · ${destino.nombre}`,
    puntos,
    tramos,
    trazosRuta: buses.flatMap((t) => (t.trazo_ruta?.length ? [{ type: 'LineString' as const, coordinates: t.trazo_ruta }] : [])),
    intermedias: buses.flatMap((t) => (t.paradas_intermedias ?? []).map((p) => ({ lat: p.lat, lng: p.lng, nombre: p.nombre }))),
  };
}

export const duracionTotal = (r: Recorrido) => r.tramos.reduce((s, t) => s + (t.duracion_min ?? 0), 0);
export const distanciaTotal = (r: Recorrido) => r.tramos.reduce((s, t) => s + (t.distancia_km ?? 0), 0);
