// SIMULACIÓN de traslados con las rutas de ejemplo (lo real lo calcula la API con las rutas de MongoDB).
import type { Coordenada } from '@/constants/zona';
import type { Alternativa, Movilidad, Tramo } from '@/types/dominio';
import { aMinutosDelDia, desdeGeoJSON, distanciaKm, FACTOR_CALLES, VELOCIDAD_KMH } from '@/utils/geo';

import { RUTAS } from './datos';
import { reportesVigentes } from './reportes';

const RADIO_CAMINATA_KM = 1.2;
const DISTANCIA_CORTA_KM = 1.5;

function paradaMasCercana(paradas: (typeof RUTAS)[number]['paradas'], p: Coordenada) {
  return paradas
    .map((parada, i) => ({ parada, i, km: distanciaKm(p, desdeGeoJSON(parada.ubicacion.coordinates)) }))
    .sort((a, b) => a.km - b.km)[0];
}

/** Alternativa en una línea de ejemplo, o null si ninguna parada queda a distancia caminable. */
export function alternativaAutobus(
  ruta: (typeof RUTAS)[number],
  origen: Coordenada,
  destino: Coordenada,
  hora: string,
): Alternativa | null {
  const sube = paradaMasCercana(ruta.paradas, origen);
  const baja = paradaMasCercana(ruta.paradas, destino);
  if (sube.km > RADIO_CAMINATA_KM || baja.km > RADIO_CAMINATA_KM || sube.i >= baja.i) return null;

  const tramo = ruta.paradas.slice(sube.i, baja.i + 1);
  let kmTramo = 0;
  for (let i = 1; i < tramo.length; i++) {
    kmTramo += distanciaKm(desdeGeoJSON(tramo[i - 1].ubicacion.coordinates), desdeGeoJSON(tramo[i].ubicacion.coordinates));
  }

  const avisos: string[] = [];
  const min = aMinutosDelDia(hora);
  if (min < aMinutosDelDia(ruta.horario.inicio) || min > aMinutosDelDia(ruta.horario.fin)) {
    avisos.push(`Fuera del horario programado (${ruta.horario.inicio}–${ruta.horario.fin}).`);
  }
  reportesVigentes()
    .filter((r) => r.ruta_id === ruta._id)
    .forEach((r) =>
      avisos.push(`Reporte ${r.estado === 'verificado' ? 'verificado' : 'sin verificar'}: ${r.tipo.replace('_', ' ')} en la ruta.`),
    );

  return {
    id: `bus_${ruta._id}`,
    modo: 'autobus',
    ruta_id: ruta._id,
    linea: ruta.linea,
    sentido: ruta.sentido,
    tarifa: ruta.tarifa,
    abordaje: { nombre: sube.parada.nombre, ubicacion: sube.parada.ubicacion },
    descenso: { nombre: baja.parada.nombre, ubicacion: baja.parada.ubicacion },
    transbordos: [],
    tiempos: {
      caminata: Math.round(((sube.km + baja.km) * FACTOR_CALLES * 60) / VELOCIDAD_KMH.pie),
      espera: Math.round(ruta.horario.frecuencia_min / 2),
      trayecto: Math.round(((kmTramo * FACTOR_CALLES) / VELOCIDAD_KMH.autobus) * 60),
      transbordos: 0,
    },
    distancia_km: kmTramo * FACTOR_CALLES + sube.km + baja.km,
    tipo_horario: ruta.horario.tipo,
    trazo: { type: 'LineString', coordinates: tramo.map((p) => p.ubicacion.coordinates) },
    fuente: ruta.fuente,
    fecha_verificacion: ruta.fecha_verificacion,
    reglas_cumplidas: ['R13'],
    avisos,
    ejemplo: true,
  };
}

export const autobusesEntre = (origen: Coordenada, destino: Coordenada, hora: string) =>
  RUTAS.map((r) => alternativaAutobus(r, origen, destino, hora)).filter((a): a is Alternativa => a !== null);

const totalMinutos = (a: Alternativa) =>
  (a.tiempos.caminata ?? 0) + (a.tiempos.espera ?? 0) + (a.tiempos.trayecto ?? 0) + (a.tiempos.transbordos ?? 0);

/**
 * Elige cómo ir de un punto a otro según la movilidad que eligió el usuario:
 * a pie si es cerca, autobús si hay línea documentada, taxi/app si lo permitió, y si no, a pie.
 */
export function elegirTramo(a: Coordenada, b: Coordenada, movilidad: Movilidad[], hora: string): Tramo {
  const combinado = movilidad.includes('combinado');
  const permite = {
    pie: combinado || movilidad.includes('caminando'),
    bus: combinado || movilidad.includes('transporte_publico'),
    auto: combinado || movilidad.includes('taxi_app'),
  };
  const km = distanciaKm(a, b) * FACTOR_CALLES;
  const aPie = (aviso?: string): Tramo => ({
    modo: 'pie',
    duracion_min: Math.max(1, Math.round((km / VELOCIDAD_KMH.pie) * 60)),
    distancia_km: km,
    aviso,
  });

  if (permite.pie && km <= DISTANCIA_CORTA_KM) return aPie();

  if (permite.bus) {
    const [mejor] = autobusesEntre(a, b, hora).sort((x, y) => totalMinutos(x) - totalMinutos(y));
    if (mejor) {
      return {
        modo: 'autobus',
        duracion_min: totalMinutos(mejor),
        distancia_km: mejor.distancia_km,
        linea: mejor.linea,
        sentido: mejor.sentido,
        abordaje: mejor.abordaje,
        descenso: mejor.descenso,
        trazo: mejor.trazo,
        aviso: mejor.avisos?.[0],
      };
    }
  }

  if (permite.auto) {
    return {
      modo: 'taxi',
      duracion_min: Math.round((km / VELOCIDAD_KMH.auto) * 60) + 5,
      distancia_km: km,
      aviso: 'El tiempo no considera el tráfico. La tarifa la define el proveedor.',
    };
  }

  if (permite.pie) return aPie(km > 4 ? 'Trayecto largo para hacerlo a pie.' : undefined);
  return aPie('No tenemos una ruta de transporte público documentada para este tramo; se estima caminando.');
}
