import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { YStack } from 'tamagui';

import { Cargando, MensajeError, MensajeInfo } from '@/components/Avisos';
import { BotonPrimario, BotonSecundario } from '@/components/Botones';
import CampoTexto from '@/components/CampoTexto';
import { ChipGroup } from '@/components/Chips';
import Pantalla from '@/components/Pantalla';
import { Subtitulo, Tarjeta, Texto, Titulo } from '@/components/ui';
import { TIPOS_PLAN } from '@/constants/catalogos';
import { useUbicacion } from '@/context/Ubicacion';
import { useViaje } from '@/context/Viaje';
import { cambiarPlan, eliminarPlan, obtenerPlan, recuperarPlan, USA_MOCK } from '@/services/api';
import type { CambioPlan, Plan, PlanGuardado } from '@/types/dominio';
import { diaDeHoy, horaActual } from '@/utils/geo';
import { ESTADOS_GUARDADOS, fechaPlan } from '@/utils/planes';

export default function DetallePlan() {
  const { id: parametro } = useLocalSearchParams<{ id: string }>();
  const id = Number(parametro);
  if (!Number.isSafeInteger(id) || id <= 0) return <Pantalla><MensajeError>El identificador del plan no es válido.</MensajeError></Pantalla>;
  return <EditorPlan key={id} id={id} />;
}

function EditorPlan({ id }: { id: number }) {
  const { posicion, estado: estadoUbicacion } = useUbicacion();
  const { guardarPlanes } = useViaje();
  const [plan, setPlan] = useState<PlanGuardado | null>(null);
  const [titulo, setTitulo] = useState('');
  const [tipo, setTipo] = useState<Plan['tipo']>('equilibrado');
  const [cargando, setCargando] = useState(true);
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState('');
  const [aviso, setAviso] = useState('');
  const [confirmarBorrado, setConfirmarBorrado] = useState(false);
  const [intento, setIntento] = useState(0);

  useEffect(() => {
    let vigente = true;
    obtenerPlan(id)
      .then((p) => {
        if (vigente) { setPlan(p); setTitulo(p.titulo); setTipo(p.tipo_seleccionado ?? p.alternativas[0]?.tipo ?? 'equilibrado'); }
      })
      .catch((e: unknown) => { if (vigente) setError(e instanceof Error ? e.message : 'No se pudo abrir el plan.'); })
      .finally(() => { if (vigente) setCargando(false); });
    return () => { vigente = false; };
  }, [id, intento]);

  async function ejecutar(accion: () => Promise<void>) {
    if (ocupado) return;
    setOcupado(true); setError(''); setAviso('');
    try { await accion(); }
    catch (e) { setError(e instanceof Error ? e.message : 'No se pudo completar la acción.'); }
    finally { setOcupado(false); }
  }

  const actualizar = (cambios: CambioPlan) => ejecutar(async () => {
    const actualizado = await cambiarPlan(id, cambios);
    setPlan(actualizado); setTitulo(actualizado.titulo); setAviso('Cambios guardados.');
  });

  const abrirRecorrido = () => ejecutar(async () => {
    const recuperado = await recuperarPlan(id, posicion, horaActual());
    guardarPlanes({ ...recuperado.peticion, dia: recuperado.peticion.dia ?? diaDeHoy() }, recuperado.respuesta);
    router.push('/planes');
  });

  return (
    <Pantalla bordes={['left', 'right']}>
      <Titulo>{plan?.titulo ?? 'Detalle del plan'}</Titulo>
      <Subtitulo mt={4}>Organiza tu salida y consulta sus condiciones actuales.</Subtitulo>
      <YStack mt={24} gap={18}>
        {cargando && <Cargando />}
        <MensajeError>{error}</MensajeError>
        <MensajeInfo>{aviso}</MensajeInfo>
        {!cargando && !plan && <BotonSecundario texto="Reintentar" onPress={() => { setCargando(true); setError(''); setIntento((n) => n + 1); }} />}
        {plan && <>
          {USA_MOCK && <MensajeInfo>Modo demostración: datos de ejemplo.</MensajeInfo>}
          <Tarjeta gap={8}>
            <Texto peso="fuerte">{ESTADOS_GUARDADOS[plan.estado_usuario]}</Texto>
            <Texto suave>{fechaPlan(plan.fecha_plan)} · {plan.tiempo_disponible / 60} h disponibles</Texto>
            <Texto tam="sm">Interés: {plan.categoria} · Movilidad: {plan.transporte}</Texto>
          </Tarjeta>
          <CampoTexto etiqueta="Nombre del plan" value={titulo} onChangeText={setTitulo} maxLength={80} editable={!ocupado} />
          <BotonSecundario texto="Guardar nombre" deshabilitado={ocupado || !titulo.trim() || titulo.trim() === plan.titulo}
            onPress={() => actualizar({ titulo: titulo.trim() })} />
          {plan.tiene_detalle ? <Tarjeta gap={14}>
            <Texto peso="fuerte">Tu alternativa</Texto>
            <Texto suave tam="sm">Elige el recorrido que quieres conservar. Se revisará al abrirlo.</Texto>
            <ChipGroup opciones={plan.alternativas.map((a) => ({ valor: a.tipo, texto: `${TIPOS_PLAN[a.tipo]} · ${a.numero_paradas} paradas` }))}
              valor={tipo} onCambiar={(valor) => { if (!ocupado) setTipo(valor); }} estilo="suave" />
            <BotonSecundario texto="Guardar alternativa" deshabilitado={ocupado || tipo === plan.tipo_seleccionado}
              onPress={() => actualizar({ tipo_seleccionado: tipo })} />
            {plan.tipo_seleccionado && <>
              <Texto tam="xs" suave>Se conservan las paradas y su orden. Se actualizarán horarios, precios y tiempos para salir hoy desde {estadoUbicacion === 'gps' ? 'tu ubicación' : `${posicion.nombre} (referencia)`}.</Texto>
              <BotonPrimario texto="Consultar recorrido actualizado" icono="mapa" cargando={ocupado}
                deshabilitado={tipo !== plan.tipo_seleccionado} onPress={abrirRecorrido} />
              <BotonSecundario texto={plan.estado_usuario === 'realizado' ? 'Marcar como pendiente' : 'Marcar como realizado'}
                deshabilitado={ocupado} onPress={() => actualizar({ estado_usuario: plan.estado_usuario === 'realizado' ? 'guardado' : 'realizado' })} />
            </>}
          </Tarjeta> : <Tarjeta gap={8}>
            <Texto peso="semi">Solo hay un resumen de esta salida</Texto>
            <Texto suave>Este registro no contiene paradas recuperables. Puedes conservar el resumen o crear una salida nueva.</Texto>
            <BotonSecundario texto="Crear otra salida" onPress={() => router.navigate('/planificar')} />
          </Tarjeta>}
          {confirmarBorrado ? <Tarjeta gap={12}>
            <Texto peso="fuerte">¿Eliminar este plan de tu lista?</Texto>
            <Texto suave>Dejará de aparecer en Mis planes y no podrás abrirlo desde el asistente.</Texto>
            <BotonSecundario texto="Cancelar eliminación" deshabilitado={ocupado} onPress={() => setConfirmarBorrado(false)} />
            <BotonPrimario texto="Confirmar eliminación" cargando={ocupado} onPress={() => ejecutar(async () => {
              await eliminarPlan(id); router.replace('/mis-planes');
            })} />
          </Tarjeta> : <BotonSecundario texto="Eliminar plan" deshabilitado={ocupado} onPress={() => setConfirmarBorrado(true)} />}
        </>}
        <BotonSecundario texto="Volver a Mis planes" deshabilitado={ocupado} onPress={() => router.replace('/mis-planes')} />
      </YStack>
    </Pantalla>
  );
}
