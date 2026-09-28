import { ActivityIndicator } from 'react-native';
import { XStack } from 'tamagui';

import { useTema } from '@/context/Tema';
import { formatoFecha } from '@/utils/geo';

import Icono from './Icono';
import { Pildora, Texto } from './ui';

/** Se muestra cuando no hay datos verificados. Nunca se inventan rutas ni horarios. */
export function AvisoSinInformacion({ mensaje }: { mensaje?: string }) {
  const { paleta } = useTema();
  return (
    <XStack role="alert" gap={12} p={16} rounded={16} bg="$avisoFondo" borderWidth={1} borderColor="$aviso">
      <Icono nombre="info" color={paleta.aviso} tamano={20} />
      <Texto flex={1} tam="sm" peso="medio" color="$aviso">
        {mensaje || 'No tenemos información suficiente para esta ruta.'}
      </Texto>
    </XStack>
  );
}

export function MensajeError({ children }: { children?: string | null }) {
  if (!children) return null;
  return (
    <Texto role="alert" tam="sm" peso="medio" color="$peligro" bg="$peligroFondo" px={12} py={8} rounded={12}>
      {children}
    </Texto>
  );
}

export function MensajeInfo({ children }: { children?: string | null }) {
  if (!children) return null;
  return (
    <Texto role="status" tam="sm" color="$primario" bg="$suave" px={12} py={8} rounded={12}>
      {children}
    </Texto>
  );
}

export function EtiquetaEjemplo() {
  return (
    <Pildora tono="aviso" py={2}>
      <Texto tam="xs" peso="semi" color="$aviso">
        Dato de ejemplo
      </Texto>
    </Pildora>
  );
}

export function Cargando({ texto = 'Cargando…' }: { texto?: string }) {
  const { paleta } = useTema();
  return (
    <XStack items="center" gap={12} py={24}>
      <ActivityIndicator color={paleta.primario} />
      <Texto suave>{texto}</Texto>
    </XStack>
  );
}

/** De dónde viene un dato y qué tan reciente es (regla del proyecto: siempre fuente y antigüedad). */
export function FuenteDato({ fuente, fecha }: { fuente?: string | null; fecha?: string | null }) {
  return (
    <Texto tam="xs" suave>
      Fuente: {fuente || 'sin fuente'} · {fecha ? `actualizado el ${formatoFecha(fecha)}` : 'sin fecha de verificación'}
    </Texto>
  );
}

/** Título de sección con texto verde a la derecha opcional ("Presupuesto estimado … $200 – $1,500 MXN"). */
export function TituloSeccion({ titulo, derecha }: { titulo: string; derecha?: string }) {
  return (
    <XStack items="center" justify="space-between" gap={12} mb={12}>
      <Texto peso="semi">{titulo}</Texto>
      {derecha && (
        <Texto peso="fuerte" acento>
          {derecha}
        </Texto>
      )}
    </XStack>
  );
}
