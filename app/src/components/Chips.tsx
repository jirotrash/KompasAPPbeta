import { styled, XStack } from 'tamagui';

import { useTema } from '@/context/Tema';

import Icono, { type NombreIcono } from './Icono';
import { Texto } from './ui';

// Dos estilos de selección de los mockups:
// "relleno" → ¿Con quién vas? / Tiempo disponible (seleccionado relleno verde)
// "suave"   → Intereses (seleccionado fondo verde claro con borde verde)
export type EstiloChip = 'relleno' | 'suave';

const Contenedor = styled(XStack, {
  minH: 44,
  px: 16,
  gap: 6,
  rounded: 12,
  items: 'center',
  justify: 'center',
  borderWidth: 1,
  borderColor: '$borde',
  bg: '$tarjeta',
  cursor: 'pointer',
  pressStyle: { opacity: 0.75 },
  variants: {
    seleccion: {
      relleno: { bg: '$primario', borderColor: '$primario' },
      suave: { bg: '$suave', borderColor: '$primario' },
      ninguna: {},
    },
    estirar: { true: { grow: 1, px: 8 } },
  } as const,
});

type Opcion<T> = { valor: T; texto: string; icono?: NombreIcono };

type PropsChip = {
  texto: string;
  activo: boolean;
  onPress: () => void;
  estilo?: EstiloChip;
  icono?: NombreIcono;
  /** Reparte el ancho de la fila entre los chips (filas como "Solo / Pareja / Amigos / Familia"). */
  estirar?: boolean;
};

export function Chip({ texto, activo, onPress, estilo = 'suave', icono, estirar }: PropsChip) {
  const { paleta } = useTema();
  const relleno = activo && estilo === 'relleno';
  const color = relleno ? paleta.sobrePrimario : activo ? paleta.primario : paleta.texto;
  return (
    <Contenedor
      seleccion={activo ? estilo : 'ninguna'}
      estirar={estirar}
      role="button"
      aria-selected={activo}
      aria-label={texto}
      onPress={onPress}
    >
      {icono && <Icono nombre={icono} color={color} tamano={16} />}
      <Texto numberOfLines={1} tam="sm" peso="semi" color={relleno ? '$sobrePrimario' : activo ? '$primario' : '$texto'}>
        {texto}
      </Texto>
    </Contenedor>
  );
}

type PropsGrupo<T> = {
  opciones: Opcion<T>[];
  estilo?: EstiloChip;
  estirar?: boolean;
} & ({ multiple?: false; valor: T; onCambiar: (v: T) => void } | { multiple: true; valor: T[]; onCambiar: (v: T[]) => void });

/** Grupo de chips de selección única o múltiple. */
export function ChipGroup<T extends string | number>(props: PropsGrupo<T>) {
  const { opciones, estilo, estirar } = props;
  const activo = (v: T) => (props.multiple ? props.valor.includes(v) : props.valor === v);
  const elegir = (v: T) => {
    if (props.multiple) props.onCambiar(props.valor.includes(v) ? props.valor.filter((x) => x !== v) : [...props.valor, v]);
    else props.onCambiar(v);
  };
  return (
    <XStack gap={8} flexWrap={estirar ? 'nowrap' : 'wrap'}>
      {opciones.map((o) => (
        <Chip
          key={String(o.valor)}
          texto={o.texto}
          icono={o.icono}
          activo={activo(o.valor)}
          onPress={() => elegir(o.valor)}
          estilo={estilo}
          estirar={estirar}
        />
      ))}
    </XStack>
  );
}
