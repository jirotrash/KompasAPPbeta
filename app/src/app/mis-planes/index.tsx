import { router, useFocusEffect } from 'expo-router';
import { useCallback, useRef, useState } from 'react';
import { XStack, YStack } from 'tamagui';

import { Cargando, MensajeError, MensajeInfo } from '@/components/Avisos';
import { BotonPrimario, BotonSecundario } from '@/components/Botones';
import Pantalla from '@/components/Pantalla';
import { Subtitulo, Tarjeta, Texto, Titulo } from '@/components/ui';
import { TIPOS_PLAN } from '@/constants/catalogos';
import { listarPlanes, USA_MOCK } from '@/services/api';
import type { PlanGuardado } from '@/types/dominio';
import { fechaPlan, ESTADOS_GUARDADOS } from '@/utils/planes';

export default function MisPlanes() {
  const [planes, setPlanes] = useState<PlanGuardado[]>([]);
  const [cargando, setCargando] = useState(true);
  const [mas, setMas] = useState(false);
  const [error, setError] = useState('');
  const consulta = useRef(0);

  const recargar = useCallback(() => {
    const turno = ++consulta.current;
    setCargando(true);
    setError('');
    listarPlanes()
      .then((datos) => { if (turno === consulta.current) { setPlanes(datos); setMas(datos.length === 20); } })
      .catch((e: unknown) => { if (turno === consulta.current) setError(e instanceof Error ? e.message : 'No se pudieron cargar tus planes.'); })
      .finally(() => { if (turno === consulta.current) setCargando(false); });
  }, []);

  useFocusEffect(useCallback(() => {
    recargar();
    return () => { consulta.current++; };
  }, [recargar]));

  async function cargarMas() {
    if (cargando || !planes.length) return;
    setCargando(true);
    setError('');
    const turno = ++consulta.current;
    try {
      const siguientes = await listarPlanes(planes[planes.length - 1].id);
      if (turno !== consulta.current) return;
      setPlanes((actuales) => [...actuales, ...siguientes.filter((p) => !actuales.some((a) => a.id === p.id))]);
      setMas(siguientes.length === 20);
    } catch (e) {
      if (turno === consulta.current) setError(e instanceof Error ? e.message : 'No se pudieron cargar más planes.');
    } finally { if (turno === consulta.current) setCargando(false); }
  }

  return (
    <Pantalla bordes={['left', 'right']}>
      <Titulo>Mis planes</Titulo>
      <Subtitulo mt={4}>Tus salidas, listas para retomarlas.</Subtitulo>
      <YStack gap={16} mt={24}>
        {USA_MOCK && <MensajeInfo>Modo demostración: ejemplos guardados en este dispositivo.</MensajeInfo>}
        <BotonPrimario texto="Crear una salida" icono="planificar" onPress={() => router.navigate('/planificar')} />
        <MensajeError>{error}</MensajeError>
        {!!error && <BotonSecundario texto="Reintentar" onPress={recargar} />}
        {!cargando && !error && planes.length === 0 && (
          <Tarjeta gap={8}>
            <Texto peso="fuerte">Tu próxima salida empieza aquí</Texto>
            <Texto suave>Crea un plan y guarda la alternativa que prefieras. Podrás volver a ella desde esta pantalla.</Texto>
          </Tarjeta>
        )}
        {planes.map((plan) => (
          <Tarjeta key={plan.id} gap={12}>
            <XStack justify="space-between" items="center" gap={12}>
              <Texto peso="fuerte" tam="lg" flex={1}>{plan.titulo}</Texto>
              <Texto tam="xs" peso="semi" color={plan.estado_usuario === 'realizado' ? '$ok' : '$primario'}>
                {ESTADOS_GUARDADOS[plan.estado_usuario]}
              </Texto>
            </XStack>
            <Texto suave tam="sm">{fechaPlan(plan.fecha_plan)} · {plan.tiempo_disponible / 60} h disponibles</Texto>
            <Texto tam="sm">{plan.tipo_seleccionado ? TIPOS_PLAN[plan.tipo_seleccionado] : 'Alternativa por elegir'}</Texto>
            {!plan.tiene_detalle && <Texto suave tam="xs">Resumen disponible. Este registro no tiene un recorrido recuperable.</Texto>}
            <BotonSecundario texto={`Abrir: ${plan.titulo}`} onPress={() => router.push({ pathname: '/mis-planes/[id]', params: { id: String(plan.id) } })} />
          </Tarjeta>
        ))}
        {cargando && <Cargando texto="Cargando tus planes…" />}
        {mas && !cargando && <BotonSecundario texto="Cargar más" onPress={cargarMas} />}
      </YStack>
    </Pantalla>
  );
}
