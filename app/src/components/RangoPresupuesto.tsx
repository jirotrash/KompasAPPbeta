import { useEffect, useRef, useState } from 'react';
import { PanResponder, View, type LayoutChangeEvent } from 'react-native';

import { useTema } from '@/context/Tema';

type Rango = [number, number];

type Props = {
  min: number;
  max: number;
  paso: number;
  valor: Rango;
  onCambiar: (v: Rango) => void;
};

const TAM_PERILLA = 22;

/** Slider de dos puntas (mínimo y máximo), hecho con PanResponder para no agregar librerías nativas. */
export default function RangoPresupuesto({ min, max, paso, valor, onCambiar }: Props) {
  const { paleta } = useTema();
  const [ancho, setAncho] = useState(0);
  // Refs para que los gestos siempre lean los valores actuales
  const estado = useRef({ ancho: 0, valor, inicio: 0, onCambiar });
  useEffect(() => {
    estado.current.ancho = ancho;
    estado.current.valor = valor;
    estado.current.onCambiar = onCambiar;
  }, [ancho, valor, onCambiar]);

  const aPosicion = (v: number, w: number) => ((v - min) / (max - min)) * w;

  const crearGesto = (indice: 0 | 1) =>
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderTerminationRequest: () => false,
      onPanResponderGrant: () => {
        estado.current.inicio = aPosicion(estado.current.valor[indice], estado.current.ancho);
      },
      onPanResponderMove: (_, g) => {
        const { ancho: w, valor: actual, inicio } = estado.current;
        if (!w) return;
        const x = Math.min(Math.max(inicio + g.dx, 0), w);
        let v = Math.round((min + (x / w) * (max - min)) / paso) * paso;
        v = indice === 0 ? Math.min(v, actual[1] - paso) : Math.max(v, actual[0] + paso);
        if (v === actual[indice]) return;
        const nuevo: Rango = indice === 0 ? [v, actual[1]] : [actual[0], v];
        estado.current.valor = nuevo;
        estado.current.onCambiar(nuevo);
      },
    });

  // Se crean una sola vez. Los gestos leen `estado` solo al arrastrar, nunca durante el render.
  // eslint-disable-next-line react-hooks/refs
  const [gestos] = useState(() => [crearGesto(0), crearGesto(1)]);

  const ajustar = (indice: 0 | 1, delta: number) => {
    let v = valor[indice] + delta;
    v = indice === 0 ? Math.max(min, Math.min(v, valor[1] - paso)) : Math.min(max, Math.max(v, valor[0] + paso));
    onCambiar(indice === 0 ? [v, valor[1]] : [valor[0], v]);
  };

  const izquierda = aPosicion(valor[0], ancho);
  const derecha = aPosicion(valor[1], ancho);

  return (
    <View
      style={{ height: TAM_PERILLA + 12, marginHorizontal: TAM_PERILLA / 2, justifyContent: 'center' }}
      onLayout={(e: LayoutChangeEvent) => setAncho(e.nativeEvent.layout.width)}
    >
      <View style={{ height: 4, borderRadius: 999, backgroundColor: paleta.borde }} />
      <View
        style={{
          position: 'absolute',
          height: 4,
          borderRadius: 999,
          backgroundColor: paleta.primario,
          left: izquierda,
          width: Math.max(derecha - izquierda, 0),
        }}
      />
      {([0, 1] as const).map((i) => (
        <View
          key={i}
          {...gestos[i].panHandlers}
          accessible
          accessibilityRole="adjustable"
          accessibilityLabel={i === 0 ? 'Presupuesto mínimo' : 'Presupuesto máximo'}
          accessibilityValue={{ min, max, now: valor[i], text: `$${valor[i]}` }}
          accessibilityActions={[{ name: 'increment' }, { name: 'decrement' }]}
          onAccessibilityAction={(e) => ajustar(i, e.nativeEvent.actionName === 'increment' ? paso : -paso)}
          hitSlop={16}
          style={{
            position: 'absolute',
            width: TAM_PERILLA,
            height: TAM_PERILLA,
            borderRadius: 999,
            borderWidth: 2,
            borderColor: paleta.primario,
            backgroundColor: paleta.tarjeta,
            left: (i === 0 ? izquierda : derecha) - TAM_PERILLA / 2,
            boxShadow: '0 1px 3px rgba(0,0,0,0.15)',
          }}
        />
      ))}
    </View>
  );
}
