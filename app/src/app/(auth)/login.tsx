import { router } from 'expo-router';
import { useRef, useState } from 'react';
import type { TextInput } from 'react-native';
import { XStack, YStack } from 'tamagui';

import { MensajeError, MensajeInfo } from '@/components/Avisos';
import { BotonPrimario, Enlace } from '@/components/Botones';
import CampoTexto from '@/components/CampoTexto';
import MarcoAcceso, { AccesoSocial } from '@/components/MarcoAcceso';
import { Texto } from '@/components/ui';
import { useSesion } from '@/context/Sesion';
import { USA_MOCK } from '@/services/api';

export default function Login() {
  const { login } = useSesion();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [aviso, setAviso] = useState('');
  const [enviando, setEnviando] = useState(false);
  const campoPassword = useRef<TextInput>(null);

  async function entrar() {
    setAviso('');
    if (!email.trim() || !password) return setError('Escribe tu correo y tu contraseña.');
    setError('');
    setEnviando(true);
    try {
      await login({ email: email.trim(), password });
      // Al haber sesión, la navegación protegida muestra las pestañas automáticamente
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo iniciar sesión.');
      setEnviando(false);
    }
  }

  return (
    <MarcoAcceso titulo="¡Hola de nuevo!" subtitulo="Inicia sesión para continuar planificando tus salidas perfectas">
      <YStack gap={16}>
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
          <Enlace
            texto="¿Olvidaste tu contraseña?"
            onPress={() => setAviso('La recuperación de contraseña todavía no está disponible.')}
          />
        </XStack>
        <MensajeError>{error}</MensajeError>
        <MensajeInfo>{aviso}</MensajeInfo>
        <BotonPrimario texto="Iniciar sesión" onPress={entrar} cargando={enviando} />
        {USA_MOCK && (
          <Texto tam="xs" suave text="center">
            Modo demostración: cualquier correo y una contraseña de 6 o más caracteres.
          </Texto>
        )}
      </YStack>

      <AccesoSocial />

      <XStack justify="center" flexWrap="wrap" gap={4}>
        <Texto tam="sm" suave>
          ¿No tienes una cuenta?
        </Texto>
        <Enlace texto="Regístrate" onPress={() => router.push('/registro')} />
      </XStack>
    </MarcoAcceso>
  );
}
