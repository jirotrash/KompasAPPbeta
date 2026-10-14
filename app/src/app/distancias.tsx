import { useState } from 'react';
import { type GestureResponderEvent, type LayoutChangeEvent, Pressable, View } from 'react-native';
import { XStack, YStack } from 'tamagui';

import { MensajeError } from '@/components/Avisos';
import { BotonSecundario } from '@/components/Botones';
import Icono from '@/components/Icono';
import Pantalla from '@/components/Pantalla';
import { Recuadro, Tarjeta, Texto, Titulo } from '@/components/ui';
import { useTema } from '@/context/Tema';
import { compararDistancias } from '@/services/api';
import type { ComparacionDistancias, PuntoPlano } from '@/types/dominio';

const MAX = 6; // los ejes van de 0 a 6
const MARGEN_EJE = 22; // espacio para los números de los ejes
const GROSOR = 3;
const PASOS = [
  { valor: 1, texto: 'Enteros' },
  { valor: 0.5, texto: 'Medios (0.5)' },
];

const fmt = (n: number) => String(Math.round(n * 100) / 100);
const plural = (n: number, uno: string, varios: string) => (n === 1 ? uno : varios);

/** Plano cartesiano de 0 a 6 en el que se tocan los puntos A y B. */
function Plano({ puntos, paso, onTocar }: { puntos: PuntoPlano[]; paso: number; onTocar: (p: PuntoPlano) => void }) {
  const { paleta } = useTema();
  const [lado, setLado] = useState(0);
  const u = lado / MAX; // píxeles por unidad

  const medir = (e: LayoutChangeEvent) => setLado(Math.min(e.nativeEvent.layout.width - MARGEN_EJE, 420));
  const aPx = (p: PuntoPlano) => ({ left: p.x * u, top: (MAX - p.y) * u });

  const tocar = (e: GestureResponderEvent) => {
    if (!lado) return;
    // En iOS/Android el toque trae locationX/Y; en la web llega un MouseEvent con offsetX/Y
    const ev = e.nativeEvent as unknown as { locationX?: number; locationY?: number; offsetX?: number; offsetY?: number };
    const lx = Number.isFinite(ev.locationX) ? ev.locationX : ev.offsetX;
    const ly = Number.isFinite(ev.locationY) ? ev.locationY : ev.offsetY;
    if (lx == null || ly == null || !Number.isFinite(lx) || !Number.isFinite(ly)) return;
    const ajustar = (v: number) => Math.min(MAX, Math.max(0, Math.round(v / paso) * paso));
    onTocar({ x: ajustar(lx / u), y: ajustar(MAX - ly / u) });
  };

  const [A, B] = puntos;
  const lineas = A && B && (A.x !== B.x || A.y !== B.y);

  return (
    <View onLayout={medir} style={{ width: '100%' }}>
      {lado > 0 && (
        <View style={{ flexDirection: 'row' }}>
          {/* Eje Y */}
          <View style={{ width: MARGEN_EJE, height: lado }}>
            {Array.from({ length: MAX + 1 }, (_, i) => (
              <Texto key={i} tam="xs" suave style={{ position: 'absolute', top: (MAX - i) * u - 8, right: 6 }}>
                {i}
              </Texto>
            ))}
          </View>

          <View>
            <Pressable
              onPress={tocar}
              accessibilityRole="button"
              accessibilityLabel="Plano cartesiano: toca para colocar un punto"
              style={{ width: lado, height: lado, backgroundColor: paleta.tarjeta }}
            >
              {/* Cuadrícula (pointerEvents none: el toque siempre llega al plano) */}
              {Array.from({ length: MAX + 1 }, (_, i) => (
                <View key={`v${i}`} pointerEvents="none" style={{ position: 'absolute', left: i * u - 0.5, top: 0, width: i ? 1 : 2, height: lado, backgroundColor: i ? paleta.borde : paleta.textoSuave }} />
              ))}
              {Array.from({ length: MAX + 1 }, (_, i) => (
                <View key={`h${i}`} pointerEvents="none" style={{ position: 'absolute', top: (MAX - i) * u - 0.5, left: 0, height: i ? 1 : 2, width: lado, backgroundColor: i ? paleta.borde : paleta.textoSuave }} />
              ))}

              {lineas && <Lineas A={A} B={B} u={u} lado={lado} />}

              {puntos.map((p, i) => {
                const otro = puntos[1 - i];
                // La etiqueta va del lado contrario al otro punto, sin salirse del plano
                let derecha = otro ? p.x >= otro.x : true;
                let arriba = otro ? p.y >= otro.y : true;
                if (p.x > MAX - 1.5) derecha = false;
                else if (p.x < 1.5) derecha = true;
                if (p.y > MAX - 0.5) arriba = false;
                else if (p.y < 0.5) arriba = true;
                const { left, top } = aPx(p);
                return (
                  <View key={i} pointerEvents="none" style={{ position: 'absolute', left: 0, top: 0 }}>
                    <View style={{ position: 'absolute', left: left - 8, top: top - 8, width: 16, height: 16, borderRadius: 8, backgroundColor: paleta.acento, borderWidth: 2, borderColor: paleta.tarjeta }} />
                    <Texto
                      tam="sm"
                      peso="fuerte"
                      style={{ position: 'absolute', top: arriba ? top - 26 : top + 8, left: derecha ? left + 8 : left - 88, width: 80, textAlign: derecha ? 'left' : 'right' }}
                    >
                      {`${'AB'[i]}(${fmt(p.x)}, ${fmt(p.y)})`}
                    </Texto>
                  </View>
                );
              })}
            </Pressable>

            {/* Eje X */}
            <View style={{ height: MARGEN_EJE, width: lado }}>
              {Array.from({ length: MAX + 1 }, (_, i) => (
                <Texto key={i} tam="xs" suave style={{ position: 'absolute', left: i * u - 4, top: 3 }}>
                  {i}
                </Texto>
              ))}
            </View>
          </View>
        </View>
      )}
    </View>
  );
}

/** Línea Euclidiana (diagonal) y camino Manhattan (horizontal y luego vertical). */
function Lineas({ A, B, u, lado }: { A: PuntoPlano; B: PuntoPlano; u: number; lado: number }) {
  const { paleta } = useTema();
  const pa = { x: A.x * u, y: (MAX - A.y) * u };
  const pb = { x: B.x * u, y: (MAX - B.y) * u };
  const esquina = { x: pb.x, y: pa.y };
  const largo = Math.hypot(pb.x - pa.x, pb.y - pa.y);
  const angulo = Math.atan2(pb.y - pa.y, pb.x - pa.x);
  const dx = Math.abs(B.x - A.x);
  const dy = Math.abs(B.y - A.y);
  const etiqueta = { position: 'absolute' as const, width: 40, textAlign: 'center' as const };

  // Etiquetas de cada tramo del lado contrario al otro punto, sin salirse
  let horizontalArriba = B.y < A.y;
  if (A.y > MAX - 0.5) horizontalArriba = false;
  else if (A.y < 0.5) horizontalArriba = true;
  let verticalDerecha = B.x > A.x;
  if (B.x > MAX - 0.7) verticalDerecha = false;
  else if (B.x < 0.7) verticalDerecha = true;

  return (
    <View pointerEvents="none" style={{ position: 'absolute', left: 0, top: 0, width: lado, height: lado }}>
      {/* Manhattan */}
      {dx > 0 && (
        <View style={{ position: 'absolute', left: Math.min(pa.x, pb.x), top: pa.y - GROSOR / 2, width: Math.abs(pb.x - pa.x), height: GROSOR, backgroundColor: paleta.aviso }} />
      )}
      {dy > 0 && (
        <View style={{ position: 'absolute', left: pb.x - GROSOR / 2, top: Math.min(pa.y, pb.y), width: GROSOR, height: Math.abs(pb.y - pa.y), backgroundColor: paleta.aviso }} />
      )}
      {dx > 0 && dy > 0 && (
        <View
          style={{
            position: 'absolute',
            width: 10,
            height: 10,
            borderWidth: 1.5,
            borderColor: paleta.aviso,
            left: A.x < B.x ? esquina.x - 10 : esquina.x,
            top: B.y > A.y ? esquina.y - 10 : esquina.y,
          }}
        />
      )}

      {/* Euclidiana: una barra del largo de la diagonal, girada sobre su centro */}
      <View
        style={{
          position: 'absolute',
          left: (pa.x + pb.x) / 2 - largo / 2,
          top: (pa.y + pb.y) / 2 - GROSOR / 2,
          width: largo,
          height: GROSOR,
          backgroundColor: paleta.primario,
          transform: [{ rotate: `${angulo}rad` }],
        }}
      />

      {dx > 0 && dy > 0 && (
        <>
          <Texto tam="xs" peso="fuerte" style={{ ...etiqueta, color: paleta.aviso, left: (pa.x + pb.x) / 2 - 20, top: horizontalArriba ? pa.y - 20 : pa.y + 4 }}>
            {fmt(dx)}
          </Texto>
          <Texto tam="xs" peso="fuerte" style={{ ...etiqueta, color: paleta.aviso, left: verticalDerecha ? pb.x + 2 : pb.x - 42, top: (pa.y + pb.y) / 2 - 8 }}>
            {fmt(dy)}
          </Texto>
        </>
      )}
    </View>
  );
}

function TarjetaMetrica({ color, titulo, detalle, calculo }: { color: string; titulo: string; detalle: string; calculo: string }) {
  return (
    <Tarjeta gap={8}>
      <XStack items="center" gap={10}>
        <YStack width={22} height={4} rounded={2} style={{ backgroundColor: color }} />
        <Texto peso="fuerte" flex={1}>
          {titulo}
        </Texto>
      </XStack>
      <Texto tam="sm" suave>
        {detalle}
      </Texto>
      <Recuadro>
        <Texto tam="sm">{calculo}</Texto>
      </Recuadro>
    </Tarjeta>
  );
}

/** Laboratorio: el usuario coloca A y B y se comparan la distancia Euclidiana y la Manhattan. */
export default function LaboratorioDistancias() {
  const { paleta } = useTema();
  const [puntos, setPuntos] = useState<PuntoPlano[]>([]);
  const [paso, setPaso] = useState(1);
  const [resultado, setResultado] = useState<ComparacionDistancias | null>(null);
  const [error, setError] = useState('');

  const colocar = (p: PuntoPlano) => {
    // Con A y B ya puestos, un toque nuevo empieza otra vez con A
    const nuevos = puntos.length === 2 ? [p] : [...puntos, p];
    setPuntos(nuevos);
    setResultado(null);
    setError('');
    if (nuevos.length === 2) {
      compararDistancias(nuevos[0], nuevos[1])
        .then(setResultado)
        .catch((causa) => setError(causa instanceof Error ? causa.message : 'No se pudieron calcular las distancias.'));
    }
  };

  const borrar = () => {
    setPuntos([]);
    setResultado(null);
    setError('');
  };

  const instruccion = ['Toca el plano para colocar el punto A.', 'Ahora toca para colocar el punto B.', 'Toca otra vez para empezar de nuevo.'][puntos.length];

  return (
    <Pantalla bordes={['left', 'right']}>
      <YStack gap={16}>
        <XStack gap={12} p={16} rounded={16} bg="$suave" borderWidth={1} borderColor="$primario">
          <Icono nombre="regla" color={paleta.primario} tamano={22} />
          <YStack flex={1} gap={4}>
            <Titulo fontSize={21} lineHeight={26}>
              Euclidiana vs. Manhattan
            </Titulo>
            <Texto tam="sm">La línea recta contra el recorrido por cuadras. {instruccion}</Texto>
          </YStack>
        </XStack>

        <YStack gap={8}>
          <Texto peso="semi">Ajustar los puntos a</Texto>
          <XStack gap={8}>
            {PASOS.map(({ valor, texto }) => (
              <XStack
                key={valor}
                flex={1}
                minH={44}
                rounded={12}
                items="center"
                justify="center"
                role="radio"
                aria-checked={paso === valor}
                onPress={() => setPaso(valor)}
                cursor="pointer"
                bg={paso === valor ? '$primario' : '$tarjeta'}
                borderWidth={1}
                borderColor={paso === valor ? '$primario' : '$borde'}
              >
                <Texto peso="fuerte" color={paso === valor ? '$sobrePrimario' : '$texto'}>
                  {texto}
                </Texto>
              </XStack>
            ))}
          </XStack>
        </YStack>

        <Plano puntos={puntos} paso={paso} onTocar={colocar} />

        {puntos.length > 0 && <BotonSecundario texto="Borrar puntos" icono="cerrar" onPress={borrar} />}

        <MensajeError>{error}</MensajeError>

        {resultado && resultado.euclidiana === 0 && (
          <Tarjeta>
            <Texto>A y B son el mismo punto: las dos distancias valen 0.</Texto>
          </Tarjeta>
        )}

        {resultado && resultado.euclidiana > 0 && (
          <YStack gap={12}>
            <TarjetaMetrica
              color={paleta.primario}
              titulo={`Distancia Euclidiana = ${fmt(resultado.euclidiana)}`}
              detalle="Línea recta de A a B."
              calculo={resultado.pasos.euclidiana}
            />
            <TarjetaMetrica
              color={paleta.aviso}
              titulo={`Distancia Manhattan = ${fmt(resultado.manhattan)}`}
              detalle={`${fmt(resultado.horizontal)} ${plural(resultado.horizontal, 'horizontal', 'horizontales')} + ${fmt(resultado.vertical)} ${plural(resultado.vertical, 'vertical', 'verticales')}, moviéndose solo en ángulo recto.`}
              calculo={resultado.pasos.manhattan}
            />
            <Tarjeta gap={6}>
              <Texto peso="fuerte">{resultado.alineados ? 'Los puntos están alineados' : `Manhattan es ${fmt(resultado.diferencia)} más largo`}</Texto>
              <Texto tam="sm" suave>
                {resultado.alineados
                  ? 'Cuando A y B comparten una coordenada, ir en línea recta ya es ir por la cuadra: ambas distancias coinciden.'
                  : 'Nunca se puede ir en diagonal entre cuadras, por eso Manhattan es igual o mayor que la Euclidiana.'}
              </Texto>
            </Tarjeta>
          </YStack>
        )}

        <Tarjeta gap={6}>
          <XStack items="center" gap={8}>
            <Icono nombre="pie" color={paleta.primario} tamano={18} />
            <Texto peso="fuerte">¿Dónde lo usa Kompás?</Texto>
          </XStack>
          <Texto tam="sm" suave>
            Para estimar cuánto mide un trayecto a pie o en taxi, Kompás calcula la distancia por calles con la métrica Manhattan sobre las
            coordenadas del mapa, en lugar de usar solo la línea recta.
          </Texto>
        </Tarjeta>
      </YStack>
    </Pantalla>
  );
}
