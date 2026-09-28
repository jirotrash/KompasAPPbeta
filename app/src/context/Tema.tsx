import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { useColorScheme } from 'react-native';
import { TamaguiProvider, Theme } from 'tamagui';

import { PALETAS, type Esquema, type Paleta } from '@/constants/tema';
import { tamaguiConfig } from '@/tamagui.config';

const CLAVE = 'bu_tema';

export type PreferenciaTema = 'sistema' | 'claro' | 'oscuro';

type ValorTema = {
  preferencia: PreferenciaTema;
  esquema: Esquema;
  paleta: Paleta;
  cambiarPreferencia: (p: PreferenciaTema) => void;
};

const ContextoTema = createContext<ValorTema | null>(null);

/** Modo claro/oscuro con Tamagui: por defecto sigue al celular; el usuario lo cambia en Perfil. */
export function ProveedorTema({ children }: { children: ReactNode }) {
  const sistema = useColorScheme();
  const [preferencia, setPreferencia] = useState<PreferenciaTema>('sistema');

  useEffect(() => {
    AsyncStorage.getItem(CLAVE)
      .then((v) => {
        if (v === 'claro' || v === 'oscuro' || v === 'sistema') setPreferencia(v);
      })
      .catch(() => {});
  }, []);

  const esquema: Esquema = preferencia === 'sistema' ? (sistema === 'dark' ? 'oscuro' : 'claro') : preferencia;
  const tema = esquema === 'oscuro' ? 'dark' : 'light';

  const valor: ValorTema = {
    preferencia,
    esquema,
    paleta: PALETAS[esquema],
    cambiarPreferencia: (p) => {
      setPreferencia(p);
      AsyncStorage.setItem(CLAVE, p).catch(() => {});
    },
  };

  return (
    <ContextoTema.Provider value={valor}>
      <TamaguiProvider config={tamaguiConfig} defaultTheme={tema}>
        <Theme name={tema}>{children}</Theme>
      </TamaguiProvider>
    </ContextoTema.Provider>
  );
}

export function useTema() {
  const valor = useContext(ContextoTema);
  if (!valor) throw new Error('useTema debe usarse dentro de <ProveedorTema>');
  return valor;
}
