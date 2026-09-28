import { router } from 'expo-router';
import { useState } from 'react';
import { XStack, YStack } from 'tamagui';

import { MensajeError } from '@/components/Avisos';
import { BotonPrimario, Enlace } from '@/components/Botones';
import CampoTexto from '@/components/CampoTexto';
import Icono from '@/components/Icono';
import MarcoAcceso, { AccesoSocial } from '@/components/MarcoAcceso';
import { Texto } from '@/components/ui';
import { useSesion } from '@/context/Sesion';
import { useTema } from '@/context/Tema';
import { edad, fechaISO, formatoFechaEscrita } from '@/utils/fechas';

const NIVELES = ['Débil', 'Media', 'Fuerte'];

/** 0 = vacía, 1 = débil, 2 = media, 3 = fuerte (largo y variedad de caracteres). */
function fuerzaContrasena(p: string) {
  if (!p) return 0;
  let puntos = 1;
  if (p.length >= 8) puntos++;
  if (/[A-Z]/.test(p) && /[0-9]/.test(p) && /[^A-Za-z0-9]/.test(p) && p.length >= 10) puntos++;
  return puntos;
}

function MedidorContrasena({ password }: { password: string }) {
  const fuerza = fuerzaContrasena(password);
  return (
    <YStack gap={6} aria-label={`Seguridad de contraseña: ${fuerza ? NIVELES[fuerza - 1] : 'sin escribir'}`}>
      <XStack gap={6}>
        {[1, 2, 3].map((n) => (
          <YStack key={n} flex={1} height={4} rounded={999} bg={n <= fuerza ? '$primario' : '$borde'} />
        ))}
      </XStack>
      <XStack justify="space-between">
        <Texto tam="xs" suave>
          Seguridad de contraseña
        </Texto>
        {fuerza > 0 && (
          <Texto tam="xs" peso="semi" acento>
            {NIVELES[fuerza - 1]}
          </Texto>
        )}
      </XStack>
    </YStack>
  );
}

export default function Registro() {
  const { registrar } = useSesion();
  const { paleta } = useTema();
  const [datos, setDatos] = useState({
    nombre: '',
    primer_apellido: '',
    segundo_apellido: '',
    email: '',
    nacimiento: '', // DD/MM/AAAA
    password: '',
  });
  const [acepta, setAcepta] = useState(false);
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  const cambiar = (campo: keyof typeof datos) => (valor: string) => setDatos((d) => ({ ...d, [campo]: valor }));

  const nacimientoISO = fechaISO(datos.nacimiento);
  const anios = nacimientoISO ? edad(nacimientoISO) : null;
  const edadValida = anios !== null && anios >= 0 && anios <= 120;

  async function crear() {
    if (!datos.nombre.trim() || !datos.primer_apellido.trim() || !datos.email.trim()) {
      return setError('Escribe tu nombre, tu primer apellido y tu correo.');
    }
    if (!nacimientoISO) return setError('Escribe tu fecha de nacimiento como DD/MM/AAAA.');
    if (!edadValida) return setError('Revisa tu fecha de nacimiento: no puede ser futura.');
    if (datos.password.length < 6) return setError('La contraseña necesita al menos 6 caracteres.');
    if (!acepta) return setError('Para crear tu cuenta acepta los términos y condiciones.');
    setError('');
    setEnviando(true);
    try {
      await registrar({
        nombre: datos.nombre.trim(),
        primer_apellido: datos.primer_apellido.trim(),
        segundo_apellido: datos.segundo_apellido.trim() || undefined,
        email: datos.email.trim(),
        password: datos.password,
        fecha_nacimiento: nacimientoISO,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo crear la cuenta.');
      setEnviando(false);
    }
  }

  return (
    <MarcoAcceso titulo="Crea tu cuenta" subtitulo="Únete a la comunidad de Kompás y empieza a explorar la ciudad a tu medida">
      <YStack gap={16}>
        <CampoTexto
          etiqueta="Nombre(s)"
          value={datos.nombre}
          onChangeText={cambiar('nombre')}
          placeholder="Tu nombre"
          autoComplete="given-name"
        />
        <XStack gap={12} flexWrap="wrap">
          <YStack flex={1} minW={140}>
            <CampoTexto
              etiqueta="Primer apellido"
              value={datos.primer_apellido}
              onChangeText={cambiar('primer_apellido')}
              placeholder="Apellido"
              autoComplete="family-name"
            />
          </YStack>
          <YStack flex={1} minW={140}>
            <CampoTexto
              etiqueta="Segundo apellido (opcional)"
              value={datos.segundo_apellido}
              onChangeText={cambiar('segundo_apellido')}
              placeholder="Apellido"
            />
          </YStack>
        </XStack>
        <CampoTexto
          etiqueta="Correo electrónico"
          value={datos.email}
          onChangeText={cambiar('email')}
          placeholder="ejemplo@correo.com"
          keyboardType="email-address"
          autoCapitalize="none"
          autoComplete="email"
        />
        <YStack gap={6}>
          <CampoTexto
            etiqueta="Fecha de nacimiento"
            value={datos.nacimiento}
            onChangeText={(texto) => cambiar('nacimiento')(formatoFechaEscrita(texto))}
            placeholder="DD/MM/AAAA"
            keyboardType="number-pad"
            maxLength={10}
            autoComplete="birthdate-full"
          />
          {edadValida && (
            <Texto tam="xs" suave>
              Tienes {anios} {anios === 1 ? 'año' : 'años'}
            </Texto>
          )}
        </YStack>
        <YStack gap={10}>
          <CampoTexto
            etiqueta="Contraseña"
            contrasena
            value={datos.password}
            onChangeText={cambiar('password')}
            placeholder="Mínimo 6 caracteres"
            autoComplete="new-password"
          />
          <MedidorContrasena password={datos.password} />
        </YStack>

        <XStack items="center" gap={10} flexWrap="wrap">
          <YStack
            width={22}
            height={22}
            rounded={6}
            borderWidth={2}
            borderColor="$primario"
            bg={acepta ? '$primario' : '$tarjeta'}
            items="center"
            justify="center"
            role="checkbox"
            aria-checked={acepta}
            aria-label="Acepto los términos y condiciones"
            onPress={() => setAcepta((v) => !v)}
            cursor="pointer"
            hitSlop={10}
          >
            {acepta && <Icono nombre="check" color={paleta.sobrePrimario} tamano={14} />}
          </YStack>
          <Texto tam="sm" onPress={() => setAcepta((v) => !v)}>
            Acepto los
          </Texto>
          <Enlace texto="Términos y condiciones" onPress={() => router.push('/terminos')} />
        </XStack>

        <MensajeError>{error}</MensajeError>
        <BotonPrimario texto="Crear cuenta" onPress={crear} cargando={enviando} />
      </YStack>

      <AccesoSocial />

      <XStack justify="center" flexWrap="wrap" gap={4}>
        <Texto tam="sm" suave>
          ¿Ya tienes una cuenta?
        </Texto>
        <Enlace texto="Inicia sesión" onPress={() => (router.canGoBack() ? router.back() : router.replace('/login'))} />
      </XStack>
    </MarcoAcceso>
  );
}
