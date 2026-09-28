// Convierte lo que regresa la API (un plan o una alternativa de ruta) en un "recorrido" que la
// pestaña Mapa sabe dibujar: puntos numerados + tramos entre ellos (a pie, autobús, taxi).
import { TIPOS_PLAN } from '@/constants/catalogos';
import type { Coordenada } from '@/constants/zona';
import type { Alternativa, Plan, PuntoRecorrido, Recorrido, Tramo } from '@/types/dominio';

import { aHora, aMinutosDelDia, desdeGeoJSON, distanciaKm, FACTOR_CALLES, VELOCIDAD_KMH } from './geo';

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

export const duracionTotal = (r: Recorrido) => r.tramos.reduce((s, t) => s + (t.duracion_min ?? 0), 0);
export const distanciaTotal = (r: Recorrido) => r.tramos.reduce((s, t) => s + (t.distancia_km ?? 0), 0);
