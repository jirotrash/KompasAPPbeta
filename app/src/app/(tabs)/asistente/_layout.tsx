import { Stack } from 'expo-router';

import { useTema } from '@/context/Tema';

/** Pestaña Asistente: lista de conversaciones y, encima, el chat de cada una. */
export default function LayoutAsistente() {
  const { paleta } = useTema();
  return (
    <Stack
      screenOptions={{
        contentStyle: { backgroundColor: paleta.fondo },
        headerShadowVisible: false,
        headerTintColor: paleta.texto,
        headerStyle: { backgroundColor: paleta.fondo },
        headerBackButtonDisplayMode: 'minimal',
      }}
    >
      <Stack.Screen name="index" options={{ headerShown: false }} />
      <Stack.Screen name="[id]" options={{ title: 'Asistente' }} />
    </Stack>
  );
}
