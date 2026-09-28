import { useEffect, useMemo, useState } from 'react';

import type { LineaMapa } from '@/components/mapa/tipos';
import { trazarPorCalles } from '@/services/mapas';
import type { Recorrido } from '@/types/dominio';
import { desdeGeoJSON } from '@/utils/geo';

/**
 * Líneas a dibujar para cada tramo del recorrido:
 * el trazo que manda la API (p. ej. el de la línea de autobús) o, si no viene,
 * el trazo por calles de OSRM (a pie o en auto). Mientras carga, una línea recta.
 */
export default function useTrazos(recorrido: Recorrido | null): LineaMapa[] {
  const [porCalles, setPorCalles] = useState<{ para: Recorrido | null; lineas: LineaMapa[] }>({ para: null, lineas: [] });

  const rectas = useMemo<LineaMapa[]>(
    () =>
      recorrido?.tramos.map((t, i) => ({
        id: `tramo_${i}`,
        modo: t.modo,
        coordenadas: t.trazo ? t.trazo.coordinates.map(desdeGeoJSON) : [recorrido.puntos[i], recorrido.puntos[i + 1]],
      })) ?? [],
    [recorrido],
  );

  useEffect(() => {
    if (!recorrido) return;
    let activo = true;
    Promise.all(
      recorrido.tramos.map(async (t, i) => {
        const base: LineaMapa = {
          id: `tramo_${i}`,
          modo: t.modo,
          coordenadas: t.trazo ? t.trazo.coordinates.map(desdeGeoJSON) : [recorrido.puntos[i], recorrido.puntos[i + 1]],
        };
        if (t.trazo || t.modo === 'autobus') return base;
        const calles = await trazarPorCalles(recorrido.puntos[i], recorrido.puntos[i + 1], t.modo === 'pie' ? 'pie' : 'auto');
        return calles ? { ...base, coordenadas: calles.trazo.coordinates.map(desdeGeoJSON) } : base;
      }),
    ).then((lineas) => activo && setPorCalles({ para: recorrido, lineas }));
    return () => {
      activo = false;
    };
  }, [recorrido]);

  return porCalles.para === recorrido ? porCalles.lineas : rectas;
}
