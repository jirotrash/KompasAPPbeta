import { DarkTheme, DefaultTheme, SplashScreen, Stack, ThemeProvider } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';

import { ProveedorSesion, useSesion } from '@/context/Sesion';
import { ProveedorTema, useTema } from '@/context/Tema';
import { ProveedorUbicacion } from '@/context/Ubicacion';
import { ProveedorViaje } from '@/context/Viaje';

SplashScreen.preventAutoHideAsync();

function Navegacion() {
  const { usuario, cargando } = useSesion();
  const { esquema, paleta } = useTema();

  useEffect(() => {
    if (!cargando) SplashScreen.hideAsync();
  }, [cargando]);

  if (cargando) return null;

  const base = esquema === 'oscuro' ? DarkTheme : DefaultTheme;
  const temaNavegacion = {
    ...base,
    colors: {
      ...base.colors,
      primary: paleta.primario,
      background: paleta.fondo,
      card: paleta.fondo,
      text: paleta.texto,
      border: paleta.borde,
    },
  };

  return (
    <ThemeProvider value={temaNavegacion}>
      <ProveedorUbicacion activo={!!usuario}>
        <ProveedorViaje>
          <StatusBar style={esquema === 'oscuro' ? 'light' : 'dark'} />
          <Stack
            screenOptions={{
              headerShown: false,
              contentStyle: { backgroundColor: paleta.fondo },
              headerShadowVisible: false,
              headerTintColor: paleta.texto,
              headerStyle: { backgroundColor: paleta.fondo },
              headerBackButtonDisplayMode: 'minimal',
            }}
          >
            {/* Sin sesión solo se ve login/registro; con sesión, el resto de la app */}
            <Stack.Protected guard={!usuario}>
              <Stack.Screen name="(auth)" />
            </Stack.Protected>
            <Stack.Protected guard={!!usuario}>
              <Stack.Screen name="(tabs)" />
              <Stack.Screen name="planes" options={{ headerShown: true, title: '' }} />
              <Stack.Screen name="buscar" options={{ headerShown: true, title: '¿A dónde vas?' }} />
              <Stack.Screen name="reportar" options={{ headerShown: true, title: 'Reportar' }} />
            </Stack.Protected>
            {/* Disponible con y sin sesión (se abre desde el registro y el perfil). Va al final: al cambiar la
                sesión, Expo Router abre la primera pantalla disponible y debe ser login o las pestañas. */}
            <Stack.Screen name="terminos" options={{ headerShown: true, title: '' }} />
          </Stack>
        </ProveedorViaje>
      </ProveedorUbicacion>
    </ThemeProvider>
  );
}

export default function RootLayout() {
  return (
    <ProveedorTema>
      <ProveedorSesion>
        <Navegacion />
      </ProveedorSesion>
    </ProveedorTema>
  );
}
