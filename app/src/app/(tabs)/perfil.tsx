import { router } from 'expo-router';
import type { ReactNode } from 'react';
import { XStack, YStack } from 'tamagui';

import { BotonSecundario } from '@/components/Botones';
import Icono, { type NombreIcono } from '@/components/Icono';
import Pantalla from '@/components/Pantalla';
import { Texto, Titulo } from '@/components/ui';
import { ZONA } from '@/constants/zona';
import { useSesion } from '@/context/Sesion';
import { useTema, type PreferenciaTema } from '@/context/Tema';
import { useUbicacion } from '@/context/Ubicacion';
import { USA_MOCK } from '@/services/api';
import { edad } from '@/utils/fechas';

const TEMAS: { valor: PreferenciaTema; texto: string; icono: NombreIcono }[] = [
  { valor: 'claro', texto: 'Claro', icono: 'sol' },
  { valor: 'oscuro', texto: 'Oscuro', icono: 'luna' },
  { valor: 'sistema', texto: 'Sistema', icono: 'sistema' },
];

const ESTADOS_UBICACION = {
  buscando: 'Buscando tu ubicación…',
  gps: 'Usando el GPS de tu celular',
  sin_permiso: 'Sin permiso: se usa el Centro de Toluca',
  fuera_de_zona: 'Fuera de la zona piloto: se usa el Centro de Toluca',
  error: 'No se pudo obtener; se usa el Centro de Toluca',
};

function Seccion({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <YStack gap={8}>
      <Texto tam="sm" peso="semi" suave textTransform="uppercase" letterSpacing={0.5}>
        {titulo}
      </Texto>
      <YStack overflow="hidden" rounded={20} borderWidth={1} borderColor="$borde" bg="$tarjeta">
        {children}
      </YStack>
    </YStack>
  );
}

function Fila({ icono, texto, detalle, onPress }: { icono: NombreIcono; texto: string; detalle?: string; onPress?: () => void }) {
  const { paleta } = useTema();
  return (
    <XStack
      minH={56}
      items="center"
      gap={12}
      px={16}
      py={12}
      role={onPress ? 'button' : undefined}
      onPress={onPress}
      cursor={onPress ? 'pointer' : undefined}
      pressStyle={onPress ? { bg: '$suave' } : undefined}
    >
      <Icono nombre={icono} color={paleta.primario} tamano={20} />
      <YStack flex={1}>
        <Texto peso="medio">{texto}</Texto>
        {detalle && (
          <Texto tam="xs" suave>
            {detalle}
          </Texto>
        )}
      </YStack>
      {onPress && <Icono nombre="derecha" color={paleta.textoSuave} tamano={18} />}
    </XStack>
  );
}

export default function Perfil() {
  const { usuario, logout } = useSesion();
  const { preferencia, cambiarPreferencia, paleta } = useTema();
  const { estado, actualizar } = useUbicacion();
  const nombreCompleto = [usuario?.nombre, usuario?.primer_apellido, usuario?.segundo_apellido].filter(Boolean).join(' ');
  const iniciales = [usuario?.nombre, usuario?.primer_apellido]
    .filter((p): p is string => !!p)
    .map((p) => p[0])
    .join('')
    .toUpperCase() || '?';
  const anios = usuario?.fecha_nacimiento ? edad(usuario.fecha_nacimiento) : null;

  return (
    <Pantalla>
      <Titulo>Perfil</Titulo>

      <XStack mt={24} items="center" gap={16}>
        <YStack width={64} height={64} rounded={999} bg="$primario" items="center" justify="center">
          <Texto tam="xl" peso="fuerte" color="$sobrePrimario">
            {iniciales}
          </Texto>
        </YStack>
        <YStack flex={1}>
          <Texto tam="xl" peso="fuerte">
            {nombreCompleto}
          </Texto>
          <Texto tam="sm" suave>
            {usuario?.email}
          </Texto>
          {anios !== null && (
            <Texto tam="sm" suave>
              {anios} años
            </Texto>
          )}
        </YStack>
      </XStack>

      <YStack mt={32} gap={24}>
        <Seccion titulo="Apariencia">
          <XStack gap={8} p={8}>
            {TEMAS.map((t) => {
              const activo = preferencia === t.valor;
              return (
                <YStack
                  key={t.valor}
                  flex={1}
                  minH={64}
                  items="center"
                  justify="center"
                  gap={4}
                  rounded={14}
                  bg={activo ? '$suave' : 'transparent'}
                  role="radio"
                  aria-checked={activo}
                  aria-label={t.texto}
                  onPress={() => cambiarPreferencia(t.valor)}
                  cursor="pointer"
                >
                  <Icono nombre={t.icono} color={activo ? paleta.primario : paleta.textoSuave} tamano={22} />
                  <Texto tam="sm" peso="semi" color={activo ? '$primario' : '$textoSuave'}>
                    {t.texto}
                  </Texto>
                </YStack>
              );
            })}
          </XStack>
        </Seccion>

        <Seccion titulo="Ubicación">
          <Fila icono="miUbicacion" texto="Actualizar ubicación" detalle={ESTADOS_UBICACION[estado]} onPress={actualizar} />
        </Seccion>

        <Seccion titulo="Comunidad">
          <Fila
            icono="reporte"
            texto="Reportar una incidencia"
            detalle="Afluencia, cierres, accidentes o manifestaciones"
            onPress={() => router.push('/reportar')}
          />
        </Seccion>

        <Seccion titulo="Acerca de">
          <Fila icono="mapa" texto="Zona piloto" detalle={ZONA.nombre} />
          <Fila icono="info" texto="Datos" detalle={USA_MOCK ? 'Modo demostración: datos de ejemplo' : 'Conectado a la API de Kompás'} />
          <Fila icono="documento" texto="Términos y condiciones" onPress={() => router.push('/terminos')} />
          <Fila icono="brujula" texto="Proyecto escolar" detalle="UTVT · ITIID-D71" />
        </Seccion>

        <BotonSecundario texto="Cerrar sesión" icono="salir" onPress={logout} />
      </YStack>
    </Pantalla>
  );
}
