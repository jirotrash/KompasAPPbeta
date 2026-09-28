import { useCallback, useEffect, useState } from 'react';
import { Linking, TextInput } from 'react-native';
import { XStack, YStack } from 'tamagui';

import { MensajeError, MensajeInfo, TituloSeccion } from '@/components/Avisos';
import { BotonPrimario } from '@/components/Botones';
import { ChipGroup } from '@/components/Chips';
import Icono from '@/components/Icono';
import Mapa from '@/components/mapa/Mapa';
import Pantalla from '@/components/Pantalla';
import { Tarjeta, Texto } from '@/components/ui';
import { TIPOS_REPORTE } from '@/constants/catalogos';
import { estaDentroDeZona, type Coordenada } from '@/constants/zona';
import { useTema } from '@/context/Tema';
import { useUbicacion } from '@/context/Ubicacion';
import { crearReporte, obtenerReportes } from '@/services/api';
import type { Reporte, TipoReporte } from '@/types/dominio';

const NIVELES = [
  { valor: 'baja' as const, texto: 'Baja' },
  { valor: 'media' as const, texto: 'Media' },
  { valor: 'alta' as const, texto: 'Alta' },
];

const formatoHora = (iso: string) =>
  new Date(iso).toLocaleString('es-MX', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });

/** Reporte comunitario. No es un servicio de emergencias. */
export default function Reportar() {
  const { paleta } = useTema();
  const { posicion } = useUbicacion();
  const [tipo, setTipo] = useState<TipoReporte>('afluencia');
  const [nivel, setNivel] = useState<'baja' | 'media' | 'alta'>('media');
  const [punto, setPunto] = useState<Coordenada>(posicion);
  const [comentario, setComentario] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState('');
  const [creado, setCreado] = useState<Reporte | null>(null);
  const [vigentes, setVigentes] = useState<Reporte[]>([]);

  const cargarVigentes = useCallback(() => {
    obtenerReportes()
      .then(setVigentes)
      .catch(() => setVigentes([]));
  }, []);
  useEffect(cargarVigentes, [cargarVigentes]);

  function elegirPunto(p: Coordenada) {
    if (!estaDentroDeZona(p)) return setError('Ese punto está fuera de la zona piloto.');
    setError('');
    setPunto(p);
  }

  async function enviar() {
    setError('');
    setEnviando(true);
    try {
      const nuevo = await crearReporte({
        tipo,
        nivel_afluencia: tipo === 'afluencia' ? nivel : undefined,
        ubicacion: { type: 'Point', coordinates: [punto.lng, punto.lat] },
        observado_en: new Date().toISOString(),
        comentario: comentario.trim() || undefined,
      });
      setCreado(nuevo);
      setComentario('');
      cargarVigentes();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo enviar el reporte.');
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Pantalla bordes={['left', 'right', 'bottom']}>
      <XStack
        gap={12}
        p={16}
        rounded={16}
        borderWidth={1}
        borderColor="$peligro"
        bg="$peligroFondo"
        role="link"
        aria-label="Llamar al 911"
        onPress={() => Linking.openURL('tel:911')}
        cursor="pointer"
      >
        <Icono nombre="aviso" color={paleta.peligro} tamano={20} />
        <Texto flex={1} tam="sm" color="$peligro">
          <Texto tam="sm" peso="fuerte" color="$peligro">
            Esto no es un servicio de emergencias.
          </Texto>{' '}
          Si hay personas heridas o en peligro, toca aquí para llamar al 911.
        </Texto>
      </XStack>

      <YStack mt={24} gap={24}>
        <YStack>
          <TituloSeccion titulo="¿Qué quieres reportar?" />
          <ChipGroup opciones={TIPOS_REPORTE} valor={tipo} onCambiar={setTipo} estilo="relleno" />
        </YStack>

        {tipo === 'afluencia' && (
          <YStack>
            <TituloSeccion titulo="Nivel de afluencia" />
            <ChipGroup opciones={NIVELES} valor={nivel} onCambiar={setNivel} estilo="suave" estirar />
          </YStack>
        )}

        <YStack>
          <TituloSeccion titulo="¿Dónde?" />
          <Texto tam="xs" suave mb={8}>
            Toca el mapa para mover el punto. Por defecto es tu ubicación.
          </Texto>
          <YStack height={240} overflow="hidden" rounded={20} borderWidth={1} borderColor="$borde">
            <Mapa marcadores={[{ id: 'punto', tipo: 'seleccion', ...punto }]} onPressMapa={elegirPunto} />
          </YStack>
        </YStack>

        <YStack>
          <TituloSeccion titulo="Comentario (opcional)" />
          <TextInput
            multiline
            maxLength={280}
            value={comentario}
            onChangeText={setComentario}
            placeholder="Ej. Cerrado un carril sobre la avenida"
            placeholderTextColor={paleta.textoSuave}
            aria-label="Comentario"
            style={{
              minHeight: 96,
              borderRadius: 12,
              borderWidth: 1,
              borderColor: paleta.borde,
              backgroundColor: paleta.tarjeta,
              paddingHorizontal: 14,
              paddingVertical: 12,
              fontSize: 15,
              color: paleta.texto,
              textAlignVertical: 'top',
            }}
          />
          <Texto tam="xs" suave text="right" mt={4}>
            {comentario.length}/280
          </Texto>
        </YStack>

        <MensajeError>{error}</MensajeError>
        <MensajeInfo>
          {creado
            ? `¡Gracias! Tu reporte quedó pendiente de verificación y estará vigente hasta el ${formatoHora(creado.vigente_hasta)}.`
            : null}
        </MensajeInfo>
        <BotonPrimario texto="Enviar reporte" icono="reporte" onPress={enviar} cargando={enviando} />

        <YStack gap={8}>
          <Texto tam="lg" peso="fuerte">
            Reportes vigentes
          </Texto>
          {vigentes.length === 0 && (
            <Texto tam="sm" suave>
              No hay reportes vigentes en la zona.
            </Texto>
          )}
          {vigentes.map((r) => (
            <Tarjeta key={r._id} p={12} gap={4}>
              <XStack items="center" justify="space-between">
                <Texto peso="semi">
                  {TIPOS_REPORTE.find((t) => t.valor === r.tipo)?.texto}
                  {r.nivel_afluencia ? ` · ${r.nivel_afluencia}` : ''}
                </Texto>
                <Texto tam="xs" peso="fuerte" color={r.estado === 'verificado' ? '$ok' : '$aviso'}>
                  {r.estado}
                </Texto>
              </XStack>
              <Texto tam="xs" suave>
                Visto: {formatoHora(r.observado_en)} · vigente hasta {formatoHora(r.vigente_hasta)} · {r.confirmaciones} confirmación(es)
              </Texto>
              {r.comentario && <Texto tam="sm">{r.comentario}</Texto>}
            </Tarjeta>
          ))}
        </YStack>
      </YStack>
    </Pantalla>
  );
}
