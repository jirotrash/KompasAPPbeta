import { useEffect, useState } from 'react';

import type { Coordenada } from '@/constants/zona';
import { buscarRutas } from '@/services/api';
import type { RespuestaRutas } from '@/types/dominio';
import { horaActual } from '@/utils/geo';

type Punto = Coordenada & { nombre: string };
type Consulta = { clave: string; origen: Punto; destino: Punto; hora: string };
type Resultado = Consulta & ({ respuesta: RespuestaRutas; error?: never } | { respuesta?: never; error: string });

/** Cada respuesta queda vinculada a ambos extremos y al intento que la produjo. */
export default function useAlternativas(origen: Punto, destino: Punto | null) {
  const [intento, setIntento] = useState(0);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const clave = destino ? `${origen.lat},${origen.lng}/${destino.lat},${destino.lng}/${intento}` : '';

  useEffect(() => {
    if (!destino) return;
    let activo = true;
    const consulta: Consulta = { clave, origen: { ...origen }, destino: { ...destino }, hora: horaActual() };
    buscarRutas({ origen, destino, hora: consulta.hora })
      .then((respuesta) => { if (activo) setResultado({ ...consulta, respuesta }); })
      .catch((e: unknown) => { if (activo) setResultado({ ...consulta, error: e instanceof Error ? e.message : 'No se pudieron buscar rutas.' }); });
    return () => { activo = false; };
  }, [clave, origen, destino]);

  const actual = destino && resultado?.clave === clave ? resultado : null;
  return { resultado: actual, cargando: !!destino && !actual, reintentar: () => setIntento((n) => n + 1) };
}
