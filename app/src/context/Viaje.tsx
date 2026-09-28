import { createContext, useContext, useState, type ReactNode } from 'react';

import type { PeticionPlan, Recorrido, RespuestaPlanes } from '@/types/dominio';

/** Lo que el usuario está planeando: la respuesta del planificador y el recorrido que ve en el Mapa. */
type ValorViaje = {
  peticion: PeticionPlan | null;
  respuesta: RespuestaPlanes | null;
  guardarPlanes: (peticion: PeticionPlan, respuesta: RespuestaPlanes) => void;
  recorrido: Recorrido | null;
  setRecorrido: (r: Recorrido | null) => void;
};

const ContextoViaje = createContext<ValorViaje | null>(null);

export function ProveedorViaje({ children }: { children: ReactNode }) {
  const [peticion, setPeticion] = useState<PeticionPlan | null>(null);
  const [respuesta, setRespuesta] = useState<RespuestaPlanes | null>(null);
  const [recorrido, setRecorrido] = useState<Recorrido | null>(null);

  const guardarPlanes = (p: PeticionPlan, r: RespuestaPlanes) => {
    setPeticion(p);
    setRespuesta(r);
  };

  return (
    <ContextoViaje.Provider value={{ peticion, respuesta, guardarPlanes, recorrido, setRecorrido }}>
      {children}
    </ContextoViaje.Provider>
  );
}

export function useViaje() {
  const valor = useContext(ContextoViaje);
  if (!valor) throw new Error('useViaje debe usarse dentro de <ProveedorViaje>');
  return valor;
}
