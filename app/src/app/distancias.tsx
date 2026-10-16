import { useMemo, useState } from 'react';
import { useWindowDimensions } from 'react-native';
import { ScrollView, XStack, YStack } from 'tamagui';

import { EtiquetaEjemplo, MensajeError } from '@/components/Avisos';
import { BotonSecundario } from '@/components/Botones';
import Icono from '@/components/Icono';
import Mapa from '@/components/mapa/Mapa';
import type { LineaMapa, MarcadorMapa } from '@/components/mapa/tipos';
import { Recuadro, Texto } from '@/components/ui';
import type { Coordenada } from '@/constants/zona';
import { ANCHO_TABLET } from '@/constants/tema';
import { useTema } from '@/context/Tema';
import { compararDistanciasGeo, USA_MOCK } from '@/services/api';
import type { ComparacionGeo } from '@/types/dominio';
import { formatoKm, formatoMinutos } from '@/utils/geo';

const ANCHO_PANEL = 380;

function Metrica({ color, punteada, titulo, valor, detalle, calculo }: {
  color: string;
  punteada?: boolean;
  titulo: string;
  valor: string;
  detalle: string;
  calculo: string;
}) {
  return (
    <YStack gap={6} p={14} rounded={14} borderWidth={1} borderColor="$borde" bg="$tarjeta">
      <XStack items="center" gap={10}>
        <XStack width={26} gap={3}>
          {punteada
            ? [0, 1, 2].map((i) => <YStack key={i} width={6} height={4} rounded={2} style={{ backgroundColor: color }} />)
            : <YStack width={26} height={4} rounded={2} style={{ backgroundColor: color }} />}
        </XStack>
        <Texto peso="fuerte" flex={1}>
          {titulo}
        </Texto>
        <Texto peso="fuerte" tam="lg">
          {valor}
        </Texto>
      </XStack>
      <Texto tam="sm" suave>
        {detalle}
      </Texto>
      <Recuadro>
        <Texto tam="sm">{calculo}</Texto>
      </Recuadro>
    </YStack>
  );
}

/** Toca dos puntos en el mapa: línea recta (Euclidiana) contra recorrido por cuadras (Manhattan). */
export default function DistanciasEnMapa() {
  const { paleta } = useTema();
  const { width, height } = useWindowDimensions();
  const esAncho = width >= ANCHO_TABLET;

  const [puntos, setPuntos] = useState<Coordenada[]>([]);
  const [resultado, setResultado] = useState<ComparacionGeo | null>(null);
  const [calculando, setCalculando] = useState(false);
  const [error, setError] = useState('');
  const [altoPanel, setAltoPanel] = useState(0);

  const tocarMapa = (p: Coordenada) => {
    // Con A y B ya puestos, un toque nuevo empieza otra vez con A
    const nuevos = puntos.length === 2 ? [p] : [...puntos, p];
    setPuntos(nuevos);
    setResultado(null);
    setError('');
    if (nuevos.length === 2) {
      setCalculando(true);
      compararDistanciasGeo(nuevos[0], nuevos[1])
        .then(setResultado)
        .catch((causa) => setError(causa instanceof Error ? causa.message : 'No se pudieron calcular las distancias.'))
        .finally(() => setCalculando(false));
    }
  };

  const borrar = () => {
    setPuntos([]);
    setResultado(null);
    setError('');
  };

  const marcadores = useMemo<MarcadorMapa[]>(
    () =>
      puntos.map((p, i) => ({
        id: `punto_${i}`,
        tipo: i === 0 ? 'origen' : 'lugar',
        etiqueta: 'AB'[i],
        titulo: `Punto ${'AB'[i]}`,
        ...p,
      })),
    [puntos],
  );

  const lineas = useMemo<LineaMapa[]>(() => {
    if (puntos.length < 2) return [];
    const [a, b] = puntos;
    return [
      // Manhattan: primero este-oeste (sobre la latitud de A) y luego norte-sur
      { id: 'manhattan', modo: 'pie', color: paleta.aviso, punteada: true, coordenadas: [a, { lat: a.lat, lng: b.lng }, b] },
      { id: 'euclidiana', modo: 'pie', color: paleta.primario, coordenadas: [a, b] },
    ];
  }, [puntos, paleta.aviso, paleta.primario]);

  const instruccion = [
    'Toca el mapa para colocar el punto A.',
    'Ahora toca para colocar el punto B.',
    'Toca otra vez para empezar de nuevo.',
  ][puntos.length];

  const panel = (
    <YStack
      onLayout={(e) => setAltoPanel(e.nativeEvent.layout.height)}
      position="absolute"
      bg="$tarjeta"
      {...(esAncho
        ? { l: 16, t: 16, rounded: 24, borderWidth: 1, borderColor: '$borde' }
        : { b: 0, l: 0, r: 0, borderTopLeftRadius: 24, borderTopRightRadius: 24 })}
      style={
        esAncho
          ? { width: ANCHO_PANEL, maxHeight: height - 140 }
          : { maxHeight: height * 0.5, boxShadow: '0 -4px 16px rgba(18,48,71,0.10)' }
      }
    >
      <ScrollView shrink={1} showsVerticalScrollIndicator={false}>
        <YStack gap={12} p={20}>
          <XStack items="center" gap={10}>
            <Icono nombre="regla" color={paleta.primario} tamano={20} />
            <Texto tam="xl" peso="fuerte" flex={1}>
              Euclidiana vs. Manhattan
            </Texto>
            {USA_MOCK && <EtiquetaEjemplo />}
          </XStack>
          <Texto tam="sm" suave>
            La línea recta contra el recorrido por cuadras. {instruccion}
          </Texto>

          {calculando && (
            <Texto tam="sm" suave>
              Calculando…
            </Texto>
          )}
          <MensajeError>{error}</MensajeError>

          {resultado && (
            <>
              <Metrica
                color={paleta.primario}
                titulo="Euclidiana"
                valor={formatoKm(resultado.euclidiana_km)}
                detalle="Línea recta de A a B."
                calculo={resultado.pasos.euclidiana}
              />
              <Metrica
                color={paleta.aviso}
                punteada
                titulo="Manhattan"
                valor={formatoKm(resultado.manhattan_km)}
                detalle={`${formatoKm(resultado.este_oeste_km)} este-oeste + ${formatoKm(resultado.norte_sur_km)} norte-sur, solo en ángulo recto.`}
                calculo={resultado.pasos.manhattan}
              />
              <YStack gap={4} p={14} rounded={14} bg="$suave">
                <Texto peso="fuerte">
                  {resultado.diferencia_km < 0.005 ? 'Los puntos están alineados' : `Manhattan es ${formatoKm(resultado.diferencia_km)} más largo`}
                </Texto>
                <Texto tam="sm">
                  Caminando: {formatoMinutos(resultado.minutos_caminando_recta)} en línea recta y{' '}
                  {formatoMinutos(resultado.minutos_caminando_calles)} por calles.
                </Texto>
                <Texto tam="xs" suave>
                  {resultado.nota}
                </Texto>
              </YStack>
            </>
          )}

          {puntos.length > 0 && <BotonSecundario texto="Borrar puntos" icono="cerrar" onPress={borrar} />}
        </YStack>
      </ScrollView>
    </YStack>
  );

  return (
    <YStack flex={1} bg="$fondo">
      <Mapa
        marcadores={marcadores}
        lineas={lineas}
        onPressMapa={tocarMapa}
        encuadrar={false}
        mostrarMiUbicacion={false}
        margen={{ abajo: esAncho ? 0 : altoPanel, izquierda: esAncho ? ANCHO_PANEL + 16 : 0 }}
      />
      {panel}
    </YStack>
  );
}
