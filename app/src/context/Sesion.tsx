import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

import * as api from '@/services/api';
import type { NuevoUsuario, Sesion, Usuario } from '@/types/dominio';

const CLAVE = 'bu_sesion';

type ValorSesion = {
  usuario: Usuario | null;
  cargando: boolean;
  login: (datos: { email: string; password: string }) => Promise<void>;
  registrar: (datos: NuevoUsuario) => Promise<void>;
  logout: () => void;
};

const ContextoSesion = createContext<ValorSesion | null>(null);

export function ProveedorSesion({ children }: { children: ReactNode }) {
  const [sesion, setSesion] = useState<Sesion | null>(null);
  const [cargando, setCargando] = useState(true);

  // Recupera la sesión guardada al abrir la app
  useEffect(() => {
    AsyncStorage.getItem(CLAVE)
      .then((texto) => {
        const guardada = texto ? (JSON.parse(texto) as Sesion) : null;
        api.usarToken(guardada?.token ?? null);
        setSesion(guardada);
      })
      .catch(() => setSesion(null))
      .finally(() => setCargando(false));
  }, []);

  const iniciar = async (nueva: Sesion | null) => {
    api.usarToken(nueva?.token ?? null);
    setSesion(nueva);
    try {
      if (nueva) await AsyncStorage.setItem(CLAVE, JSON.stringify(nueva));
      else await AsyncStorage.removeItem(CLAVE);
    } catch {
      // Si no se puede guardar, la sesión dura mientras la app esté abierta
    }
  };

  const valor: ValorSesion = {
    usuario: sesion?.usuario ?? null,
    cargando,
    login: async (datos) => iniciar(await api.login(datos)),
    registrar: async (datos) => iniciar(await api.registrar(datos)),
    logout: () => void iniciar(null),
  };

  return <ContextoSesion.Provider value={valor}>{children}</ContextoSesion.Provider>;
}

export function useSesion() {
  const valor = useContext(ContextoSesion);
  if (!valor) throw new Error('useSesion debe usarse dentro de <ProveedorSesion>');
  return valor;
}
