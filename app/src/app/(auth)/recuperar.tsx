import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { XStack, YStack } from 'tamagui';

import { MensajeError, MensajeInfo } from '@/components/Avisos';
import { BotonPrimario, Enlace } from '@/components/Botones';
import CampoTexto from '@/components/CampoTexto';
import MarcoAcceso from '@/components/MarcoAcceso';
import { Texto } from '@/components/ui';
import { useSesion } from '@/context/Sesion';
import { restablecerPassword, solicitarRecuperacion, verificarCodigo } from '@/services/api';

type Paso = 'correo' | 'codigo' | 'nueva';

const SUBTITULOS: Record<Paso, string> = {
  correo: 'Escribe el correo de tu cuenta y te enviaremos un código de verificación',
  codigo: 'Escribe el código de 6 dígitos que te enviamos por correo',
  nueva: 'Crea una contraseña nueva para tu cuenta',
};

/** Recuperar contraseña: correo → código de 6 dígitos → contraseña nueva (y entra a la app). */
export default function Recuperar() {
  const { login } = useSesion();
  const parametros = useLocalSearchParams<{ email?: string }>();
  const [paso, setPaso] = useState<Paso>('correo');
  const [email, setEmail] = useState(parametros.email ?? '');
  const [codigo, setCodigo] = useState('');
  const [password, setPassword] = useState('');
  const [confirmacion, setConfirmacion] = useState('');
  const [error, setError] = useState('');
  const [aviso, setAviso] = useState('');
  const [enviando, setEnviando] = useState(false);

  async function intentar(accion: () => Promise<void>) {
    setError('');
    setEnviando(true);
    try {
      await accion();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ocurrió un error. Intenta de nuevo.');
    } finally {
      setEnviando(false);
    }
  }

  const pedirCodigo = () =>
    intentar(async () => {
      if (!email.trim().includes('@')) throw new Error('Escribe el correo de tu cuenta.');
      const { mensaje } = await solicitarRecuperacion(email.trim());
      setAviso(mensaje);
      setCodigo('');
      setPaso('codigo');
    });

  const comprobarCodigo = () =>
    intentar(async () => {
      if (!/^\d{6}$/.test(codigo.trim())) throw new Error('El código tiene 6 dígitos.');
      await verificarCodigo(email.trim(), codigo.trim());
      setAviso('');
      setPaso('nueva');
    });

  const cambiarPassword = () =>
    intentar(async () => {
      if (password.length < 6) throw new Error('La contraseña necesita al menos 6 caracteres.');
      if (password !== confirmacion) throw new Error('Las contraseñas no coinciden.');
      await restablecerPassword(email.trim(), codigo.trim(), password);
      // Con la contraseña nueva se entra directo; la navegación protegida muestra las pestañas
      await login({ email: email.trim(), password });
    });

  return (
    <MarcoAcceso titulo="Recupera tu contraseña" subtitulo={SUBTITULOS[paso]}>
      <YStack gap={16}>
        {paso === 'correo' && (
          <CampoTexto
            etiqueta="Correo electrónico"
            value={email}
            onChangeText={setEmail}
            placeholder="ejemplo@correo.com"
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
            returnKeyType="send"
            onSubmitEditing={pedirCodigo}
          />
        )}

        {paso === 'codigo' && (
          <>
            <Texto tam="sm" suave>
              Enviado a <Texto tam="sm" peso="semi">{email.trim()}</Texto>. Vence en 15 minutos.
            </Texto>
            <CampoTexto
              etiqueta="Código de verificación"
              value={codigo}
              onChangeText={(texto) => setCodigo(texto.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              keyboardType="number-pad"
              autoComplete="one-time-code"
              textContentType="oneTimeCode"
              maxLength={6}
              returnKeyType="go"
              onSubmitEditing={comprobarCodigo}
            />
          </>
        )}

        {paso === 'nueva' && (
          <>
            <CampoTexto
              etiqueta="Contraseña nueva"
              contrasena
              value={password}
              onChangeText={setPassword}
              placeholder="Mínimo 6 caracteres"
              autoComplete="new-password"
            />
            <CampoTexto
              etiqueta="Confirma la contraseña"
              contrasena
              value={confirmacion}
              onChangeText={setConfirmacion}
              placeholder="Escríbela otra vez"
              autoComplete="new-password"
              returnKeyType="go"
              onSubmitEditing={cambiarPassword}
            />
          </>
        )}

        <MensajeError>{error}</MensajeError>
        <MensajeInfo>{aviso}</MensajeInfo>

        {paso === 'correo' && <BotonPrimario texto="Enviar código" onPress={pedirCodigo} cargando={enviando} />}
        {paso === 'codigo' && <BotonPrimario texto="Verificar código" onPress={comprobarCodigo} cargando={enviando} />}
        {paso === 'nueva' && <BotonPrimario texto="Cambiar contraseña" onPress={cambiarPassword} cargando={enviando} />}

        {paso === 'codigo' && (
          <XStack justify="center" flexWrap="wrap" gap={4}>
            <Texto tam="sm" suave>
              ¿No te llegó?
            </Texto>
            <Enlace texto="Enviar otro código" onPress={pedirCodigo} />
          </XStack>
        )}
      </YStack>

      <XStack justify="center">
        <Enlace texto="Volver a iniciar sesión" onPress={() => (router.canGoBack() ? router.back() : router.replace('/login'))} />
      </XStack>
    </MarcoAcceso>
  );
}
