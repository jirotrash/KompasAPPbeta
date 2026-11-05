import type { Coordenada } from '@/constants/zona';
import type { Alternativa, TramoOpcion } from '@/types/dominio';

import { desdeGeoJSON, formatoMinutos } from './geo';

export type FiltroTransporte = 'todos' | 'autobus' | 'auto' | 'pie';
export type OrdenTransporte = 'tiempo' | 'caminata' | 'transbordos';

const valido = (n: number | null | undefined): n is number => typeof n === 'number' && Number.isFinite(n) && n >= 0;

/** null es dato desconocido; los componentes que no aplican al modo no se exigen. */
export function resumenTiempo(a: Alternativa) {
  const requeridos = a.modo === 'pie' ? ['caminata'] as const
    : a.modo === 'autobus' ? ['caminata', 'espera', 'trayecto'] as const : ['espera', 'trayecto'] as const;
  const valores = requeridos.map((k) => a.tiempos[k]);
  const conocidos = valores.filter(valido);
  const minutos = conocidos.length ? conocidos.reduce((s, n) => s + n, 0) : null;
  const faltantes = requeridos.filter((k) => !valido(a.tiempos[k]));
  const completo = faltantes.length === 0;
  const soloEspera = faltantes.length === 1 && faltantes[0] === 'espera';
  return {
    minutos, completo,
    texto: minutos == null ? 'Sin tiempo disponible' : `${formatoMinutos(minutos)}${completo ? '' : soloEspera ? ' + espera' : ' + tiempo sin dato'}`,
    nota: completo ? 'Estimación, no tiempo en vivo.' : soloEspera
      ? 'La espera no está registrada. El total y la hora de llegada aún no se pueden calcular.'
      : 'Faltan tiempos de algunos tramos. La suma mostrada es parcial.',
  };
}

export function numeroTransbordos(a: Alternativa): number | null {
  if (a.modo !== 'autobus') return 0;
  if (valido(a.numero_transbordos)) return a.numero_transbordos;
  const buses = (a.tramos ?? []).filter((t) => t.modo === 'autobus');
  if (buses.length) return Math.max(0, buses.length - 1);
  if (a.transbordos) return a.transbordos.length;
  return a.tipo === 'directo' ? 0 : null;
}

export function ordenarAlternativas(opciones: Alternativa[], filtro: FiltroTransporte, orden: OrdenTransporte) {
  const numero = (n: number | null | undefined) => valido(n) ? n : Number.POSITIVE_INFINITY;
  return opciones.filter((a) => filtro === 'todos' || (filtro === 'auto' ? a.modo === 'taxi' || a.modo === 'app' : a.modo === filtro))
    .sort((a, b) => {
      // Se ordena por lo calculado, nunca se declara que una espera desconocida vale cero.
      const valor = (o: Alternativa) => orden === 'tiempo' ? numero(resumenTiempo(o).minutos)
        : orden === 'caminata' ? numero(o.tiempos.caminata)
          : numero(numeroTransbordos(o));
      const x = valor(a), y = valor(b);
      return (x === y ? 0 : x < y ? -1 : 1) || a.id.localeCompare(b.id);
    });
}

export function busesDe(a: Alternativa): TramoOpcion[] {
  return (a.tramos ?? []).filter((t) => t.modo === 'autobus' && t.parada_subida && t.parada_bajada);
}

export function puntoAbordaje(a: Alternativa): Coordenada | null {
  return a.parada_subida ?? (a.abordaje ? desdeGeoJSON(a.abordaje.ubicacion.coordinates) : null);
}

/** Solo se abre cuando el usuario pulsa el botón; no pide un viaje ni compra transporte. */
export function enlaceCaminata(origen: Coordenada, destino: Coordenada) {
  const params = new URLSearchParams({ api: '1', origin: `${origen.lat},${origen.lng}`, destination: `${destino.lat},${destino.lng}`, travelmode: 'walking' });
  return `https://www.google.com/maps/dir/?${params}`;
}
