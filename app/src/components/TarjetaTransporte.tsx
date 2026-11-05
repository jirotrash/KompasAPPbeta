import * as Linking from 'expo-linking';
import { useState } from 'react';
import { XStack, YStack } from 'tamagui';

import { MODOS } from '@/constants/catalogos';
import type { Coordenada } from '@/constants/zona';
import { useTema } from '@/context/Tema';
import type { Alternativa } from '@/types/dominio';
import { formatoKm, formatoMinutos } from '@/utils/geo';
import { busesDe, enlaceCaminata, numeroTransbordos, puntoAbordaje, resumenTiempo } from '@/utils/transporte';

import { EtiquetaEjemplo, MensajeError } from './Avisos';
import { BotonPrimario, BotonSecundario } from './Botones';
import ExplicacionReglas from './ExplicacionReglas';
import Icono from './Icono';
import { Recuadro, Tarjeta, Texto } from './ui';

export default function TarjetaTransporte({ alternativa: a, origen, onMapa }: { alternativa: Alternativa; origen: Coordenada; onMapa: () => void }) {
  const { paleta } = useTema();
  const [detalle, setDetalle] = useState(false);
  const [error, setError] = useState('');
  const tiempo = resumenTiempo(a);
  const buses = busesDe(a);
  const cambios = numeroTransbordos(a);
  const modo = MODOS[a.modo];
  const subida = puntoAbordaje(a);
  const color = a.modo === 'pie' ? paleta.transporteCaminando : a.modo === 'autobus' ? paleta.transportePublico : paleta.texto;
  const nombre = a.linea ?? modo.texto;

  async function caminarAlAbordaje() {
    if (!subida) return;
    setError('');
    try { await Linking.openURL(enlaceCaminata(origen, subida)); }
    catch { setError('No se pudo abrir Google Maps. Puedes consultar el recorrido en el mapa de Kompás.'); }
  }

  return <Tarjeta gap={14} testID={`alternativa-${a.id}`}>
    <XStack gap={12} items="center">
      <YStack bg="$suave" rounded={14} width={44} height={44} items="center" justify="center">
        <Icono nombre={modo.icono} color={color} tamano={22} />
      </YStack>
      <YStack flex={1} gap={4}>
        <Texto peso="fuerte" tam="lg">{nombre}</Texto>
        <Texto tam="xs" suave>{a.modo === 'autobus' ? cambios == null ? 'Transbordos por confirmar' : cambios === 0 ? 'Sin transbordos' : `${cambios} transbordo${cambios === 1 ? '' : 's'}` : modo.texto}
          {a.distancia_km != null ? ` · ${formatoKm(a.distancia_km)}` : ''}</Texto>
      </YStack>
    </XStack>
    {a.ejemplo && <EtiquetaEjemplo />}
    <Recuadro gap={6}>
      <Texto peso="fuerte" tam="xl" acento>{tiempo.texto}</Texto>
      <Texto tam="xs" suave>{tiempo.nota}</Texto>
    </Recuadro>
    <XStack gap={16} flexWrap="wrap">
      <YStack gap={3}>
        <Texto suave tam="xs">Caminata</Texto>
        <Texto peso="semi" tam="sm">{a.modo === 'taxi' || a.modo === 'app' ? 'Al punto de recogida' : formatoMinutos(a.tiempos.caminata)}</Texto>
      </YStack>
      <YStack gap={3}>
        <Texto suave tam="xs">Tarifa</Texto>
        <Texto peso="semi" tam="sm">{a.modo === 'pie' ? '$0 · a pie' : a.tarifa != null ? `$${a.tarifa.toFixed(2)} MXN` : 'Por confirmar'}</Texto>
      </YStack>
      {a.modo !== 'pie' && <YStack gap={3}>
        <Texto suave tam="xs">Espera</Texto>
        <Texto peso="semi" tam="sm">{a.tiempos.espera == null ? 'Sin dato' : `${formatoMinutos(a.tiempos.espera)} aprox.`}</Texto>
      </YStack>}
    </XStack>
    {a.modo === 'autobus' && <YStack gap={5}>
      <Texto tam="sm"><Texto peso="fuerte" tam="sm">Subida: </Texto>{a.parada_subida?.nombre ?? a.abordaje?.nombre ?? 'Sin dato'}</Texto>
      <Texto tam="sm"><Texto peso="fuerte" tam="sm">Bajada: </Texto>{a.parada_bajada?.nombre ?? a.descenso?.nombre ?? 'Sin dato'}</Texto>
      {a.paradas_reales === false && <Texto tam="xs" suave>Son puntos de referencia del trazo. Confirma dónde permite subir la línea antes de viajar.</Texto>}
    </YStack>}
    {a.modo === 'taxi' || a.modo === 'app' ? <Texto tam="xs" suave>Confirma precio, disponibilidad y punto de recogida con el proveedor. Kompás no reserva el viaje.</Texto> : null}
    {a.avisos?.map((aviso, i) => <Texto key={`${i}-${aviso}`} tam="xs" suave>{aviso}</Texto>)}
    <BotonSecundario texto={detalle ? 'Ocultar pasos' : 'Ver pasos del viaje'} onPress={() => setDetalle((v) => !v)} />
    {detalle && <YStack gap={12}>
      {buses.length > 0 ? <>
        <Texto tam="sm">1. Camina hasta {buses[0].parada_subida?.nombre}.</Texto>
        {buses.map((t, i) => <Recuadro key={`${t.id_ruta ?? i}-${i}`} gap={5}>
          <Texto peso="semi" tam="sm">{i + 2}. {i ? 'Transborda a' : 'Toma'} {t.linea ?? 'la línea indicada'}</Texto>
          <Texto tam="sm">Sube en {t.parada_subida?.nombre} y baja en {t.parada_bajada?.nombre}.</Texto>
          <Texto suave tam="xs">Trayecto: {formatoMinutos(t.duracion_min)} estimados · {(t.paradas_intermedias ?? []).length} paradas intermedias registradas.</Texto>
          {i > 0 && <Texto suave tam="xs">Camina desde la bajada anterior hasta esta subida; confirma la conexión y su espera.</Texto>}
        </Recuadro>)}
        <Texto tam="sm">{buses.length + 2}. Camina desde la última bajada hasta tu destino.</Texto>
      </> : <Texto tam="sm">{a.modo === 'pie' ? 'Consulta el trayecto a pie en el mapa.' : a.modo === 'autobus' ? 'Consulta subida y bajada en el mapa; esta alternativa no contiene el detalle por tramo.' : 'Acuerda el punto de recogida y revisa la tarifa antes de confirmar con el proveedor.'}</Texto>}
      <ExplicacionReglas reglas={a.reglas_cumplidas} />
      <Texto tam="xs" suave>Fuente: {a.fuente}</Texto>
      {subida && !a.ejemplo && a.paradas_reales === true && <BotonSecundario texto="Caminar al abordaje · Google Maps" onPress={caminarAlAbordaje} />}
      <MensajeError>{error}</MensajeError>
    </YStack>}
    <BotonPrimario texto="Ver recorrido en mapa" icono="mapa" onPress={onMapa} />
  </Tarjeta>;
}
