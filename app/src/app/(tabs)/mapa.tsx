import { router } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { useWindowDimensions } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ScrollView, XStack, YStack } from 'tamagui';

import { EtiquetaEjemplo, FuenteDato } from '@/components/Avisos';
import { BotonPrimario, BotonSecundario } from '@/components/Botones';
import Icono from '@/components/Icono';
import LineaRecorrido from '@/components/LineaRecorrido';
import Mapa from '@/components/mapa/Mapa';
import { Pildora, Texto } from '@/components/ui';
import type { MarcadorMapa } from '@/components/mapa/tipos';
import { MODOS } from '@/constants/catalogos';
import { ANCHO_BARRA_LATERAL, ANCHO_TABLET } from '@/constants/tema';
import { useTema } from '@/context/Tema';
import { useUbicacion } from '@/context/Ubicacion';
import { useViaje } from '@/context/Viaje';
import useTrazos from '@/hooks/useTrazos';
import { buscarLugares, obtenerReportes, USA_MOCK } from '@/services/api';
import type { Lugar, Reporte } from '@/types/dominio';
import { desdeGeoJSON, formatoKm, formatoMinutos } from '@/utils/geo';
import { distanciaTotal, duracionTotal } from '@/utils/recorrido';

const ANCHO_PANEL_TABLET = 380;

export default function PantallaMapa() {
  const { paleta } = useTema();
  const { posicion } = useUbicacion();
  const { recorrido, setRecorrido } = useViaje();
  const insets = useSafeAreaInsets();
  const { width, height } = useWindowDimensions();
  const esTablet = width >= ANCHO_TABLET;
  const lineas = useTrazos(recorrido);

  const [lugares, setLugares] = useState<Lugar[]>([]);
  const [reportes, setReportes] = useState<Reporte[]>([]);
  const [altoPanel, setAltoPanel] = useState(0);
  const [plegado, setPlegado] = useState(false);

  useEffect(() => {
    let activo = true;
    buscarLugares({ cerca: posicion })
      .then((l) => activo && setLugares(l))
      .catch(() => {});
    obtenerReportes()
      .then((r) => activo && setReportes(r))
      .catch(() => {});
    return () => {
      activo = false;
    };
  }, [posicion]);

  const marcadores = useMemo<MarcadorMapa[]>(() => {
    const lista: MarcadorMapa[] = reportes.map((r) => ({
      id: r._id,
      tipo: 'reporte',
      ...desdeGeoJSON(r.ubicacion.coordinates),
      titulo: `Reporte: ${r.tipo.replace('_', ' ')} (${r.estado})`,
    }));
    if (!recorrido) {
      return [
        ...lista,
        ...lugares.map((l, i) => ({
          id: l._id,
          tipo: 'lugar' as const,
          etiqueta: String(i + 1),
          ...desdeGeoJSON(l.ubicacion.coordinates),
          titulo: l.nombre,
          onPress: () => router.push({ pathname: '/buscar', params: { lugar: l._id } }),
        })),
      ];
    }
    let numero = 0;
    return [
      ...lista,
      ...recorrido.puntos.map((p, i) => ({
        id: `punto_${i}`,
        tipo: p.tipo,
        etiqueta: p.tipo === 'lugar' ? String(++numero) : p.tipo === 'origen' ? '' : undefined,
        lat: p.lat,
        lng: p.lng,
        titulo: p.nombre,
      })),
    ];
  }, [recorrido, lugares, reportes]);

  const modos = recorrido ? [...new Set(recorrido.tramos.map((t) => MODOS[t.modo].texto))].join(' + ') : '';

  const panel = (
    <YStack
      onLayout={(e) => setAltoPanel(e.nativeEvent.layout.height)}
      position="absolute"
      bg="$tarjeta"
      {...(esTablet
        ? { l: 16, rounded: 24, borderWidth: 1, borderColor: '$borde' }
        : { b: 0, l: 0, r: 0, borderTopLeftRadius: 24, borderTopRightRadius: 24 })}
      style={
        esTablet
          ? { top: insets.top + 68, width: ANCHO_PANEL_TABLET, maxHeight: height - insets.top - 68 - 16 - (width >= ANCHO_BARRA_LATERAL ? 0 : 80) }
          : { maxHeight: plegado ? undefined : height * 0.5, boxShadow: '0 -4px 16px rgba(18,48,71,0.10)' }
      }
    >
      {!esTablet && (
        <YStack
          items="center"
          pt={10}
          pb={4}
          role="button"
          aria-label={plegado ? 'Mostrar detalles' : 'Ocultar detalles'}
          onPress={() => setPlegado((v) => !v)}
          cursor="pointer"
        >
          <YStack width={40} height={5} rounded={999} bg="$borde" />
        </YStack>
      )}

      {recorrido ? (
        <>
          <XStack items="flex-start" justify="space-between" gap={12} px={20} pt={8} pb={12}>
            <YStack flex={1}>
              <Texto tam="xl" peso="fuerte">
                Detalles del recorrido
              </Texto>
              <Texto tam="sm" suave>
                {modos} • {formatoKm(distanciaTotal(recorrido))} totales
              </Texto>
            </YStack>
            <Pildora tono="suave" px={12} py={6}>
              <Texto tam="sm" peso="fuerte" acento>
                {formatoMinutos(duracionTotal(recorrido))}
              </Texto>
            </Pildora>
          </XStack>
          {!plegado && (
            <ScrollView shrink={1} px={20} showsVerticalScrollIndicator={false}>
              <YStack gap={12} pb={20}>
                {recorrido.ejemplo && <EtiquetaEjemplo />}
                <LineaRecorrido recorrido={recorrido} />
                {recorrido.avisos?.map((a) => (
                  <Texto key={a} tam="xs" color="$aviso">
                    ⚠ {a}
                  </Texto>
                ))}
                {recorrido.fuente && <FuenteDato fuente={recorrido.fuente} fecha={null} />}
                <Texto tam="xs" suave>
                  Horas y tiempos estimados; pueden variar por el tráfico.
                </Texto>
                <BotonSecundario texto="Quitar recorrido" icono="cerrar" onPress={() => setRecorrido(null)} />
              </YStack>
            </ScrollView>
          )}
        </>
      ) : (
        <YStack gap={12} px={20} pt={8} pb={20}>
          <Texto tam="xl" peso="fuerte">
            Explora la zona
          </Texto>
          {!plegado && (
            <>
              <Texto tam="sm" suave>
                Los números son lugares cercanos; toca uno para ver cómo llegar. Los círculos rojos son reportes de la comunidad.
              </Texto>
              <BotonPrimario texto="Planear una salida" icono="ruta" onPress={() => router.navigate('/planificar')} />
              <BotonSecundario texto="Buscar un destino" icono="buscar" onPress={() => router.push('/buscar')} />
            </>
          )}
        </YStack>
      )}
    </YStack>
  );

  return (
    <YStack flex={1} bg="$fondo">
      <Mapa
        marcadores={marcadores}
        lineas={lineas}
        margen={{
          arriba: insets.top + 50,
          abajo: esTablet ? 0 : altoPanel,
          izquierda: esTablet ? ANCHO_PANEL_TABLET + 16 : 0,
        }}
      />

      {/* Etiqueta de la ruta, arriba a la izquierda como en el mockup */}
      <XStack
        position="absolute"
        l={0}
        r={0}
        px={16}
        gap={8}
        items="center"
        flexWrap="wrap"
        style={{ top: insets.top + 10, pointerEvents: 'box-none' }}
      >
        <XStack
          maxW="80%"
          items="center"
          gap={8}
          rounded={999}
          bg="$tarjeta"
          px={16}
          py={10}
          style={{ boxShadow: '0 2px 8px rgba(18,48,71,0.15)' }}
        >
          <Icono nombre="ruta" color={paleta.primario} tamano={16} />
          <Texto numberOfLines={1} tam="sm" peso="semi">
            {recorrido ? `Ruta: ${recorrido.titulo}` : 'Lugares cerca de ti'}
          </Texto>
        </XStack>
        {USA_MOCK && <EtiquetaEjemplo />}
      </XStack>

      {panel}
    </YStack>
  );
}
