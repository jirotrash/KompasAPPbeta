import { router, Stack, useLocalSearchParams } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView, TextInput } from 'react-native';
import { XStack, YStack } from 'tamagui';

import { AvisoSinInformacion, Cargando, EtiquetaEjemplo, MensajeError } from '@/components/Avisos';
import Icono from '@/components/Icono';
import TarjetaAsistente from '@/components/TarjetaAsistente';
import { Texto } from '@/components/ui';
import { ANCHO_MAXIMO } from '@/constants/tema';
import { useTema } from '@/context/Tema';
import { useUbicacion } from '@/context/Ubicacion';
import { borrarConversacion, ErrorApi, enviarMensaje, estadoAsistente, obtenerConversacion, USA_MOCK } from '@/services/api';
import type { MensajeChat, TarjetaAsistente as DatosTarjeta } from '@/types/dominio';

const LIMITE = 2000;
const NO_DISPONIBLE = 'El asistente no está disponible en este momento.';

type Elemento = MensajeChat & { tarjetas?: DatosTarjeta[] };

function Burbuja({ m }: { m: Elemento }) {
  if (m.rol === 'herramienta') return m.tarjeta ? <TarjetaAsistente tarjeta={m.tarjeta} /> : null;
  if (m.rol === 'error') {
    return (
      <Texto self="center" tam="xs" color="$aviso" bg="$avisoFondo" px={12} py={6} rounded={12}>
        ⚠ {m.contenido ?? NO_DISPONIBLE}
      </Texto>
    );
  }
  const propio = m.rol === 'usuario';
  return (
    <YStack gap={8} self={propio ? 'flex-end' : 'flex-start'} maxW="85%">
      <YStack
        px={14}
        py={10}
        rounded={18}
        bg={propio ? '$primario' : '$tarjeta'}
        borderWidth={propio ? 0 : 1}
        borderColor="$borde"
        {...(propio ? { borderBottomRightRadius: 4 } : { borderBottomLeftRadius: 4 })}
      >
        <Texto color={propio ? '$sobrePrimario' : '$texto'}>{m.contenido}</Texto>
      </YStack>
      {m.tarjetas?.map((t, i) => (
        <TarjetaAsistente key={`${t.tipo}-${i}`} tarjeta={t} />
      ))}
    </YStack>
  );
}

/** Chat con el asistente: burbujas, "Escribiendo…", tarjetas de rutas y planes, y borrar la conversación. */
export default function Chat() {
  const { paleta } = useTema();
  const { posicion } = useUbicacion();
  const { id } = useLocalSearchParams<{ id: string }>();
  const lista = useRef<ScrollView>(null);

  const [mensajes, setMensajes] = useState<Elemento[] | null>(null);
  const [titulo, setTitulo] = useState<string | null>(null);
  const [disponible, setDisponible] = useState(true);
  const [texto, setTexto] = useState('');
  const [escribiendo, setEscribiendo] = useState(false);
  const [error, setError] = useState('');
  const [confirmarBorrado, setConfirmarBorrado] = useState(false);

  useEffect(() => {
    let activo = true;
    obtenerConversacion(id)
      .then((c) => {
        if (!activo) return;
        setMensajes(c.mensajes);
        setTitulo(c.titulo);
      })
      .catch((e: unknown) => activo && setError(e instanceof Error ? e.message : 'No se pudo abrir la conversación.'));
    estadoAsistente()
      .then((e) => activo && setDisponible(e.disponible))
      .catch(() => activo && setDisponible(false));
    return () => {
      activo = false;
    };
  }, [id]);

  const enviar = async () => {
    const limpio = texto.trim();
    if (!limpio || escribiendo) return;
    setError('');
    setTexto('');
    setEscribiendo(true);
    const propio: Elemento = { rol: 'usuario', contenido: limpio, creado_en: new Date().toISOString() };
    setMensajes((m) => [...(m ?? []), propio]);
    try {
      const r = await enviarMensaje(id, limpio, { lat: posicion.lat, lng: posicion.lng });
      setTitulo(r.titulo);
      setDisponible(true);
      setMensajes((m) => [...(m ?? []), { ...r.mensaje, tarjetas: r.tarjetas }]);
    } catch (e) {
      // 503: el mensaje del usuario ya quedó guardado en la API
      if (e instanceof ErrorApi && e.estado === 503) {
        setDisponible(false);
        setMensajes((m) => [...(m ?? []), { rol: 'error', contenido: e.message, creado_en: new Date().toISOString() }]);
      } else {
        setError(e instanceof Error ? e.message : 'No se pudo enviar el mensaje.');
      }
    } finally {
      setEscribiendo(false);
    }
  };

  const borrar = async () => {
    try {
      await borrarConversacion(id);
      router.back();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo borrar la conversación.');
    }
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1, backgroundColor: paleta.fondo }} behavior={Platform.OS === 'ios' ? 'padding' : undefined} keyboardVerticalOffset={90}>
      <Stack.Screen
        options={{
          title: titulo ?? 'Asistente',
          headerRight: () => (
            <XStack
              p={8}
              role="button"
              aria-label="Borrar conversación"
              onPress={() => setConfirmarBorrado((v) => !v)}
              cursor="pointer"
            >
              <Icono nombre="basura" color={paleta.textoSuave} tamano={20} />
            </XStack>
          ),
        }}
      />
      <YStack flex={1} width="100%" self="center" maxW={ANCHO_MAXIMO}>
        {confirmarBorrado && (
          <XStack m={12} p={12} gap={12} items="center" rounded={14} bg="$peligroFondo">
            <Texto flex={1} tam="sm" color="$peligro">
              ¿Borrar esta conversación?
            </Texto>
            <Texto role="button" peso="fuerte" color="$peligro" onPress={borrar} cursor="pointer" p={6}>
              Borrar
            </Texto>
            <Texto role="button" peso="semi" suave onPress={() => setConfirmarBorrado(false)} cursor="pointer" p={6}>
              Cancelar
            </Texto>
          </XStack>
        )}
        {!disponible && (
          <YStack px={16} pt={12}>
            <AvisoSinInformacion mensaje={NO_DISPONIBLE} />
          </YStack>
        )}

        <ScrollView
          ref={lista}
          style={{ flex: 1 }}
          contentContainerStyle={{ padding: 16, gap: 12 }}
          onContentSizeChange={() => lista.current?.scrollToEnd({ animated: true })}
          keyboardShouldPersistTaps="handled"
        >
          {USA_MOCK && <EtiquetaEjemplo />}
          {mensajes === null && !error && <Cargando texto="Abriendo conversación…" />}
          {mensajes?.length === 0 && (
            <Texto tam="sm" suave text="center" mt={24}>
              Escribe, por ejemplo: «¿Cómo llego al Cosmovitral?» o «Arma un plan con amigos, 300 pesos, 3 horas».
            </Texto>
          )}
          {mensajes?.map((m, i) => (
            <Burbuja key={`${m.creado_en}-${i}`} m={m} />
          ))}
          {escribiendo && (
            <XStack self="flex-start" items="center" gap={8} px={14} py={10} rounded={18} bg="$tarjeta" borderWidth={1} borderColor="$borde">
              <ActivityIndicator color={paleta.primario} size="small" />
              <Texto tam="sm" suave>
                Escribiendo…
              </Texto>
            </XStack>
          )}
          <MensajeError>{error}</MensajeError>
        </ScrollView>

        <XStack gap={8} items="flex-end" p={12} borderTopWidth={1} borderColor="$borde" bg="$tarjeta">
          <TextInput
            value={texto}
            onChangeText={setTexto}
            placeholder="Escribe tu pregunta"
            placeholderTextColor={paleta.textoSuave}
            multiline
            maxLength={LIMITE}
            aria-label="Mensaje para el asistente"
            style={
              {
                flex: 1,
                maxHeight: 120,
                minHeight: 44,
                paddingHorizontal: 14,
                paddingVertical: 10,
                borderRadius: 14,
                borderWidth: 1,
                borderColor: paleta.borde,
                backgroundColor: paleta.fondo,
                color: paleta.texto,
                fontSize: 16,
                outlineStyle: 'none',
              } as object
            }
          />
          <YStack
            width={44}
            height={44}
            rounded={999}
            bg={texto.trim() && !escribiendo ? '$primario' : '$borde'}
            items="center"
            justify="center"
            role="button"
            aria-label="Enviar"
            aria-disabled={!texto.trim() || escribiendo}
            onPress={enviar}
            cursor="pointer"
          >
            <Icono nombre="enviar" color={texto.trim() && !escribiendo ? paleta.sobrePrimario : paleta.textoSuave} tamano={20} />
          </YStack>
        </XStack>
        {texto.length > LIMITE - 200 && (
          <Texto tam="xs" suave px={16} pb={8} text="right">
            {texto.length}/{LIMITE}
          </Texto>
        )}
      </YStack>
    </KeyboardAvoidingView>
  );
}
