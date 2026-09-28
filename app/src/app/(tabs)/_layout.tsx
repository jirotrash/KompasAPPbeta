import Tabs from 'expo-router/js-tabs';
import { useWindowDimensions } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import Icono, { type NombreIcono } from '@/components/Icono';
import { ANCHO_BARRA_LATERAL } from '@/constants/tema';
import { useTema } from '@/context/Tema';

const PESTANAS: { name: string; title: string; icono: NombreIcono }[] = [
  { name: 'index', title: 'Inicio', icono: 'inicio' },
  { name: 'planificar', title: 'Planificar', icono: 'planificar' },
  { name: 'mapa', title: 'Mapa', icono: 'mapa' },
  { name: 'perfil', title: 'Perfil', icono: 'perfil' },
];

export default function LayoutPestanas() {
  const { paleta } = useTema();
  const { width } = useWindowDimensions();
  const lateral = width >= ANCHO_BARRA_LATERAL;
  const insets = useSafeAreaInsets();

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        // Celular y tablet vertical: barra abajo (como el mockup). Pantallas anchas: barra lateral.
        tabBarPosition: lateral ? 'left' : 'bottom',
        tabBarVariant: 'uikit',
        tabBarActiveTintColor: paleta.primario,
        tabBarActiveBackgroundColor: lateral ? paleta.suave : undefined,
        tabBarInactiveTintColor: paleta.textoSuave,
        tabBarLabelStyle: { fontSize: 12, fontWeight: '600' },
        tabBarStyle: lateral
          ? { backgroundColor: paleta.tarjeta, borderColor: paleta.borde, paddingTop: insets.top + 12, width: 200, minWidth: 200 }
          : {
              backgroundColor: paleta.tarjeta,
              borderColor: paleta.borde,
              height: 64 + insets.bottom,
              paddingTop: 6,
              paddingBottom: insets.bottom + 6,
            },
        sceneStyle: { backgroundColor: paleta.fondo },
      }}
    >
      {PESTANAS.map(({ name, title, icono }) => (
        <Tabs.Screen
          key={name}
          name={name}
          options={{ title, tabBarIcon: ({ color }) => <Icono nombre={icono} color={color} tamano={24} /> }}
        />
      ))}
    </Tabs>
  );
}
