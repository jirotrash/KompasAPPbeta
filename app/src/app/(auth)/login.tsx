import { router } from 'expo-router';
import { useRef, useState } from 'react';
import type { TextInput } from 'react-native';
import { XStack, YStack } from 'tamagui';

import { MensajeError } from '@/components/Avisos';
import { BotonPrimario, Enlace } from '@/components/Botones';
import CampoTexto from '@/components/CampoTexto';
import MarcoAcceso from '@/components/MarcoAcceso';
import { Texto } from '@/components/ui';
import { useSesion } from '@/context/Sesion';
import { USA_MOCK, cambiarServidor, obtenerServidor } from '@/services/api';

export default function Login() {
  const { login } = useSesion();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [servidor, setServidor] = useState(() => obtenerServidor().replace(/^http:\/\//, '').replace(/:8000$/, ''));
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);
  const campoPassword = useRef<TextInput>(null);

  async function entrar() {
    if (!email.trim() || !password) return setError('Escribe tu correo y tu contraseña.');
    setError('');
    setEnviando(true);
    try {
      if (!USA_MOCK) await cambiarServidor(servidor);
      await login({ email: email.trim(), password });
      // Al haber sesión, la navegación protegida muestra las pestañas automáticamente
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo iniciar sesión.');
      setEnviando(false);
    }
  }

  // Registro y recuperación también llaman a la API: primero se confirma la dirección del servidor
  async function irA(destino: 'registro' | 'recuperar') {
    setError('');
    try {
      if (!USA_MOCK) await cambiarServidor(servidor);
      if (destino === 'registro') router.push('/registro');
      else router.push({ pathname: '/recuperar', params: { email: email.trim() } });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se encontró el servidor.');
    }
  }

  return (
    <MarcoAcceso titulo="¡Hola de nuevo!" subtitulo="Inicia sesión para continuar planificando tus salidas perfectas">
      <YStack gap={16}>
        {!USA_MOCK && (
          <YStack gap={4}>
            <CampoTexto
              etiqueta="Dirección del servidor"
              value={servidor}
              onChangeText={setServidor}
              placeholder="192.168.1.50"
              keyboardType="url"
              autoCapitalize="none"
              autoCorrect={false}
            />
            <Texto tam="xs" suave>
              Es la IP que muestra la PC del servidor al encenderlo. Cambia cada vez que la PC se conecta a otra WiFi.
            </Texto>
          </YStack>
        )}
        <CampoTexto
          etiqueta="Correo electrónico"
          value={email}
          onChangeText={setEmail}
          placeholder="ejemplo@correo.com"
          keyboardType="email-address"
          autoCapitalize="none"
          autoComplete="email"
          returnKeyType="next"
          onSubmitEditing={() => campoPassword.current?.focus()}
        />
        <CampoTexto
          ref={campoPassword}
          etiqueta="Contraseña"
          contrasena
          value={password}
          onChangeText={setPassword}
          placeholder="Tu contraseña"
          autoComplete="current-password"
          returnKeyType="go"
          onSubmitEditing={entrar}
        />
        <XStack justify="flex-end">
          <Enlace texto="¿Olvidaste tu contraseña?" onPress={() => irA('recuperar')} />
        </XStack>
        <MensajeError>{error}</MensajeError>
        <BotonPrimario texto="Iniciar sesión" onPress={entrar} cargando={enviando} />
        {USA_MOCK && (
          <Texto tam="xs" suave text="center">
            Modo demostración: cualquier correo y una contraseña de 6 o más caracteres.
          </Texto>
        )}
      </YStack>

      <XStack justify="center" flexWrap="wrap" gap={4}>
        <Texto tam="sm" suave>
          ¿No tienes una cuenta?
        </Texto>
        <Enlace texto="Regístrate" onPress={() => irA('registro')} />
      </XStack>
    </MarcoAcceso>
  );
}
