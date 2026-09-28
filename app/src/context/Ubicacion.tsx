import * as Location from 'expo-location';
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

import { estaDentroDeZona, PUNTOS_REFERENCIA, type Coordenada } from '@/constants/zona';

export type EstadoUbicacion = 'buscando' | 'gps' | 'sin_permiso' | 'fuera_de_zona' | 'error';
type Posicion = Coordenada & { nombre: string };

type ValorUbicacion = {
  /** Punto de partida que usa la app: el GPS si está en la zona; si no, el Centro de Toluca. */
  posicion: Posicion;
  estado: EstadoUbicacion;
  /** Texto corto para la etiqueta del encabezado (p. ej. "Lerma, Méx."). */
  etiqueta: string;
  actualizar: () => void;
};

const REFERENCIA: Posicion = PUNTOS_REFERENCIA[0];
const ContextoUbicacion = createContext<ValorUbicacion | null>(null);

type Lectura = { estado: EstadoUbicacion; posicion: Posicion; ciudad?: string };

/** Pide permiso y lee el GPS. Fuera de la zona piloto o sin permiso regresa el Centro de Toluca. */
async function leerUbicacion(): Promise<Lectura> {
  try {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') return { estado: 'sin_permiso', posicion: REFERENCIA };
    const { coords } = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
    const actual = { lat: coords.latitude, lng: coords.longitude };
    if (!estaDentroDeZona(actual)) return { estado: 'fuera_de_zona', posicion: REFERENCIA };
    let ciudad: string | undefined;
    try {
      const [lugar] = await Location.reverseGeocodeAsync({ latitude: actual.lat, longitude: actual.lng });
      ciudad = lugar?.city ?? lugar?.subregion ?? lugar?.district ?? undefined;
    } catch {
      // Sin nombre de ciudad (p. ej. en web): se queda la etiqueta anterior
    }
    return { estado: 'gps', posicion: { ...actual, nombre: 'Tu ubicación' }, ciudad };
  } catch {
    return { estado: 'error', posicion: REFERENCIA };
  }
}

/** `activo`: solo pide permiso de ubicación cuando ya hay sesión (no en la pantalla de login). */
export function ProveedorUbicacion({ children, activo }: { children: ReactNode; activo: boolean }) {
  const [lectura, setLectura] = useState<Lectura>({ estado: 'buscando', posicion: REFERENCIA });
  const [etiqueta, setEtiqueta] = useState('Toluca, Méx.');

  const aplicar = (l: Lectura) => {
    setLectura(l);
    if (l.ciudad) setEtiqueta(`${l.ciudad}, Méx.`);
  };

  useEffect(() => {
    if (!activo) return;
    let vigente = true;
    leerUbicacion().then((l) => {
      if (vigente) aplicar(l);
    });
    return () => {
      vigente = false;
    };
  }, [activo]);

  const actualizar = () => {
    setLectura((l) => ({ ...l, estado: 'buscando' }));
    leerUbicacion().then(aplicar);
  };

  return (
    <ContextoUbicacion.Provider value={{ posicion: lectura.posicion, estado: lectura.estado, etiqueta, actualizar }}>
      {children}
    </ContextoUbicacion.Provider>
  );
}

export function useUbicacion() {
  const valor = useContext(ContextoUbicacion);
  if (!valor) throw new Error('useUbicacion debe usarse dentro de <ProveedorUbicacion>');
  return valor;
}
