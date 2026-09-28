import type { ReactNode } from 'react';
import { ActivityIndicator } from 'react-native';
import { styled, XStack } from 'tamagui';

import { useTema } from '@/context/Tema';

import Icono, { type NombreIcono } from './Icono';
import { Texto } from './ui';

const Base = styled(XStack, {
  minH: 52,
  rounded: 14,
  px: 20,
  gap: 8,
  items: 'center',
  justify: 'center',
  cursor: 'pointer',
  variants: {
    tipo: {
      primario: { bg: '$primario', pressStyle: { bg: '$primarioPresionado' } },
      secundario: { bg: '$tarjeta', borderWidth: 1, borderColor: '$borde', pressStyle: { bg: '$suave' } },
    },
    inactivo: { true: { opacity: 0.6 } },
  } as const,
});

type Props = {
  texto: string;
  onPress: () => void;
  cargando?: boolean;
  deshabilitado?: boolean;
  icono?: NombreIcono;
  /** Para contenido extra a la izquierda del texto (p. ej. el logo de Google). */
  prefijo?: ReactNode;
  flex?: boolean;
};

function Boton({ texto, onPress, cargando, deshabilitado, icono, prefijo, flex, tipo }: Props & { tipo: 'primario' | 'secundario' }) {
  const { paleta } = useTema();
  const inactivo = !!(cargando || deshabilitado);
  const color = tipo === 'primario' ? paleta.sobrePrimario : paleta.texto;
  return (
    <Base
      tipo={tipo}
      inactivo={inactivo}
      flex={flex ? 1 : undefined}
      role="button"
      aria-label={texto}
      aria-disabled={inactivo}
      aria-busy={cargando}
      onPress={inactivo ? undefined : onPress}
    >
      {cargando ? <ActivityIndicator color={color} /> : (prefijo ?? (icono && <Icono nombre={icono} color={color} tamano={20} />))}
      <Texto peso={tipo === 'primario' ? 'fuerte' : 'semi'} color={tipo === 'primario' ? '$sobrePrimario' : '$texto'}>
        {texto}
      </Texto>
    </Base>
  );
}

/** Botón verde de ancho completo ("Crear mi plan", "Iniciar sesión"). */
export const BotonPrimario = (p: Props) => <Boton {...p} tipo="primario" />;

/** Botón blanco con borde (acciones secundarias, Google/Apple). */
export const BotonSecundario = (p: Props) => <Boton {...p} tipo="secundario" />;

/** Enlace de texto verde ("¿Olvidaste tu contraseña?", "Regístrate"). */
export function Enlace({ texto, onPress }: { texto: string; onPress: () => void }) {
  return (
    <Texto role="link" peso="semi" acento onPress={onPress} cursor="pointer" pressStyle={{ opacity: 0.7 }}>
      {texto}
    </Texto>
  );
}
