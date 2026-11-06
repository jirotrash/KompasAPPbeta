import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { ScrollView, XStack, YStack } from 'tamagui';

import { Cargando, MensajeError } from '@/components/Avisos';
import Icono, { type NombreIcono } from '@/components/Icono';
import Logo from '@/components/Logo';
import Pantalla from '@/components/Pantalla';
import TarjetaLugar from '@/components/TarjetaLugar';
import TarjetaPrediccion from '@/components/TarjetaPrediccion';
import { Pildora, Texto, Titulo } from '@/components/ui';
import { useSesion } from '@/context/Sesion';
import { useTema } from '@/context/Tema';
import { useUbicacion } from '@/context/Ubicacion';
import { useViaje } from '@/context/Viaje';
import {
  buscarLugares,
  type ClimaActual,
  consultarClima,
  destinosProbables,
  type RespuestaDestinosProbables,
  USA_MOCK,
} from '@/services/api';
import type { Lugar } from '@/types/dominio';
import { saludo } from '@/utils/geo';

function Acceso({ texto, icono, relleno, onPress }: { texto: string; icono: NombreIcono; relleno?: boolean; onPress: () => void }) {
  const { paleta } = useTema();
  return (
    <XStack
      minH={42}
      items="center"
      gap={8}
      px={14}
      rounded={12}
      borderWidth={1}
      borderColor={relleno ? '$primario' : '$borde'}
      bg={relleno ? '$primario' : '$tarjeta'}
      role="button"
      aria-selected={relleno}
      aria-label={texto}
      onPress={onPress}
      cursor="pointer"
      pressStyle={{ opacity: 0.75 }}
    >
      <Icono nombre={icono} color={relleno ? paleta.sobrePrimario : paleta.texto} tamano={16} />
      <Texto tam="sm" peso="semi" color={relleno ? '$sobrePrimario' : '$texto'}>
        {texto}
      </Texto>
    </XStack>
  );
}

function obtenerIconoClima(clima: ClimaActual): string {
  const d = clima.descripcion.toLowerCase();
  if (clima.lluvia) return '🌧️';
  if (d.includes('cloud') || d.includes('overcast') || d.includes('nublado')) return '☁️';
  if (d.includes('sun') || d.includes('clear') || d.includes('despejado')) return '☀️';
  return '⛅';
}

/** Mismo criterio que consejo_clima() de la API (ia_kompas/servicio.py). */
function consejoClima(clima: ClimaActual): string | null {
  if (clima.lluvia) return 'Lleva paraguas o impermeable.';
  if (clima.temperatura > 26) return 'Usa bloqueador solar.';
  if (clima.temperatura < 15) return 'Lleva suéter o chamarra.';
  return null;
}

export default function Inicio() {
  const { usuario } = useSesion();
  const { paleta } = useTema();
  const { posicion, etiqueta, estado, actualizar } = useUbicacion();
  const { setRecorrido } = useViaje();
  const [lugares, setLugares] = useState<Lugar[] | null>(null);
  const [error, setError] = useState('');
  const [soloComer, setSoloComer] = useState(false);

  const [habitos, setHabitos] = useState<RespuestaDestinosProbables | null>(null);
  const [clima, setClima] = useState<ClimaActual | null>(null);
  const [mostrarTooltip, setMostrarTooltip] = useState(false);

  useEffect(() => {
    let activo = true;
    buscarLugares({ cerca: posicion })
      .then((lista) => activo && setLugares(lista))
      .catch((e) => activo && setError(e instanceof Error ? e.message : 'No se pudieron cargar los lugares.'));
    return () => {
      activo = false;
    };
  }, [posicion]);

  // Clima actual: si no responde no se muestra (no se inventa)
  useEffect(() => {
    let activo = true;
    consultarClima().then((c) => {
      if (!activo || !c) return;
      setClima(c);
      setMostrarTooltip(!!consejoClima(c));
    });
    return () => {
      activo = false;
    };
  }, []);

  // Destinos probables: el modelo aprende de los recorridos que el usuario inició (historial_rutas)
  useEffect(() => {
    let activo = true;
    if (!usuario) return;
    destinosProbables()
      .then((r) => activo && setHabitos(r))
      .catch(() => activo && setHabitos(null));
    return () => {
      activo = false;
    };
  }, [usuario]);

  const visibles = (lugares ?? []).filter((l) => !soloComer || l.interes === 'comer' || l.interes === 'cafe');

  return (
    <Pantalla ancho="amplio">
      {/* Encabezado */}
      <XStack items="center" justify="space-between" gap={12}>
        <Logo tamano={44} />

        <YStack items="flex-end">
          <XStack items="center" gap={8}>
            {/* Pildora de Clima Interactiva */}
            <XStack
              items="center"
              gap={6}
              px={10}
              py={8}
              rounded={999}
              borderWidth={1}
              borderColor="$borde"
              bg="$tarjeta"
              role="button"
              aria-label={clima ? `Clima: ${Math.round(clima.temperatura)} grados. Tocar para ver el consejo` : 'Clima no disponible'}
              onPress={() => setMostrarTooltip((v) => !v)}
              cursor="pointer"
              pressStyle={{ opacity: 0.7 }}
            >
              <Texto tam="xs">{clima ? obtenerIconoClima(clima) : '🌡️'}</Texto>
              <Texto tam="xs" peso="semi">
                {clima ? `${Math.round(clima.temperatura)}°C` : '—'}
              </Texto>
            </XStack>

            {/* Ubicación actual */}
            <XStack
              items="center"
              gap={4}
              px={12}
              py={8}
              rounded={999}
              borderWidth={1}
              borderColor="$borde"
              bg="$tarjeta"
              role="button"
              aria-label={`Ubicación: ${etiqueta}. Tocar para actualizar`}
              onPress={actualizar}
              cursor="pointer"
              pressStyle={{ opacity: 0.7 }}
            >
              <Icono nombre="ubicacion" color={paleta.primario} tamano={14} />
              <Texto tam="xs" peso="semi">
                {estado === 'buscando' ? 'Ubicando…' : etiqueta}
              </Texto>
            </XStack>
          </XStack>

          {/* Globo de texto (Tooltip) automático al abrir la app */}
          {mostrarTooltip && clima && consejoClima(clima) && (
            <YStack
              style={{ position: 'absolute', top: 40, right: 0, zIndex: 99 }}
              width={220}
              p={10}
              rounded={12}
              borderWidth={1}
              borderColor="$primario"
              bg="$tarjeta"
              elevation={4}
              gap={2}
            >
              <Texto tam="xs" peso="fuerte" color="$primario">
                💡 Recordatorio meteorológico
              </Texto>
              <Texto tam="xs" color="$textoSuave">
                {consejoClima(clima)}
              </Texto>
            </YStack>
          )}
        </YStack>
      </XStack>

      <YStack mt={24}>
        <Texto suave>{saludo()},</Texto>
        <Titulo>{usuario?.nombre}</Titulo>
      </YStack>

      {USA_MOCK && (
        <Pildora tono="aviso" mt={8}>
          <Texto tam="xs" peso="medio" color="$aviso">
            Modo demostración: datos de ejemplo, no rutas reales
          </Texto>
        </Pildora>
      )}
      {(estado === 'sin_permiso' || estado === 'fuera_de_zona') && (
        <Texto tam="xs" suave mt={8}>
          {estado === 'sin_permiso' ? 'Sin permiso de ubicación' : 'Estás fuera de la zona piloto'}: usamos el Centro de Toluca como
          referencia.
        </Texto>
      )}

      {/* Buscador (el ícono de filtros es un botón aparte) */}
      <XStack mt={20} minH={54} items="center" rounded={14} borderWidth={1} borderColor="$borde" bg="$tarjeta">
        <XStack
          flex={1}
          minH={54}
          items="center"
          gap={12}
          pl={16}
          role="button"
          aria-label="Buscar destino o lugar"
          onPress={() => router.push('/buscar')}
          cursor="pointer"
          pressStyle={{ opacity: 0.7 }}
        >
          <Icono nombre="buscar" color={paleta.textoSuave} tamano={20} />
          <Texto flex={1} suave>
            Buscar destino o lugar
          </Texto>
        </XStack>
        <XStack
          minH={54}
          px={16}
          items="center"
          role="button"
          aria-label="Planificar con filtros"
          onPress={() => router.navigate('/planificar')}
          cursor="pointer"
          pressStyle={{ opacity: 0.7 }}
        >
          <Icono nombre="filtros" color={paleta.textoSuave} tamano={20} />
        </XStack>
      </XStack>

      {/* Accesos rápidos */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} mx={-20} mt={16} $md={{ mx: -32 }}>
        <XStack gap={8} px={20} $md={{ px: 32 }}>
          <Acceso texto="Ir a un lugar" icono="ubicacion" onPress={() => router.push('/buscar')} />
          <Acceso texto="Planear una salida" icono="ruta" relleno onPress={() => router.navigate('/planificar')} />
          <Acceso texto={soloComer ? 'Comer ✓' : 'Comer'} icono="comer" relleno={soloComer} onPress={() => setSoloComer((v) => !v)} />
          <Acceso texto="Reportar" icono="reporte" onPress={() => router.push('/reportar')} />
        </XStack>
      </ScrollView>

      {/* Destino probable según los hábitos del usuario (historial_rutas) */}
      {habitos && (
        <YStack mt={20}>
          <TarjetaPrediccion datos={habitos} />
        </YStack>
      )}

      {/* Cerca de ti */}
      <XStack mt={28} mb={12} items="center" justify="space-between">
        <Texto tam="xl" peso="fuerte">
          {soloComer ? 'Para comer cerca de ti' : 'Cerca de ti'}
        </Texto>
        <Texto
          role="link"
          tam="sm"
          peso="semi"
          acento
          cursor="pointer"
          onPress={() => {
            setRecorrido(null);
            router.navigate('/mapa');
          }}
        >
          Ver mapa
        </Texto>
      </XStack>

      <MensajeError>{error}</MensajeError>
      {lugares === null && !error && <Cargando texto="Buscando lugares cercanos…" />}
      <XStack flexWrap="wrap" justify="space-between" rowGap={12}>
        {visibles.map((l) => (
          <YStack key={l._id} width="100%" $md={{ width: '49%' }} $xl={{ width: '32.5%' }}>
            <TarjetaLugar lugar={l} desde={posicion} onPress={() => router.push({ pathname: '/buscar', params: { lugar: l._id } })} />
          </YStack>
        ))}
      </XStack>
    </Pantalla>
  );
}