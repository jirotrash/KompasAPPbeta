// Solo modo demostración: los ejemplos se conservan por cuenta en este dispositivo.
import AsyncStorage from '@react-native-async-storage/async-storage';

import type { Coordenada } from '@/constants/zona';
import type { CambioPlan, PeticionPlan, Plan, PlanGuardado, PlanRecuperado, RespuestaPlanes, Sesion } from '@/types/dominio';
import { diaDeHoy } from '@/utils/geo';

import { LUGARES } from './datos';
import { reconstruirEjemplo } from './motor';

type Registro = { ficha: PlanGuardado; peticion: Omit<PeticionPlan, 'origen'>; opciones: Plan[] };

async function leer(): Promise<{ clave: string; registros: Registro[] }> {
  const texto = await AsyncStorage.getItem('bu_sesion');
  const sesion = texto ? JSON.parse(texto) as Sesion : null;
  if (!sesion?.usuario.email) throw new Error('Inicia sesión para ver tus planes.');
  const clave = `kompas_planes_demo_v1:${sesion.usuario.email.toLowerCase()}`;
  const datos = await AsyncStorage.getItem(clave);
  return { clave, registros: datos ? JSON.parse(datos) as Registro[] : [] };
}

function encontrar(registros: Registro[], id: number) {
  const registro = registros.find((r) => r.ficha.id === id);
  if (!registro) throw new Error('No encontramos ese plan en tu cuenta.');
  return registro;
}

export async function registrarGeneracion(peticion: PeticionPlan, respuesta: RespuestaPlanes): Promise<RespuestaPlanes> {
  const { clave, registros } = await leer();
  const id = Math.max(Date.now(), ...registros.map((r) => r.ficha.id + 1));
  const fecha = new Date().toISOString();
  const { origen: _origen, ...preferencias } = peticion;
  const ficha: PlanGuardado = {
    id, titulo: `Salida: ${peticion.contexto}`, estado_usuario: 'borrador', tipo_seleccionado: null,
    tiene_detalle: respuesta.planes.length > 0,
    alternativas: respuesta.planes.map((p) => ({ tipo: p.tipo, numero_paradas: p.paradas.length })),
    no_acompanantes: { solo: 0, pareja: 1, amigos: 3, familia: 3 }[peticion.contexto],
    tiempo_disponible: peticion.tiempo_horas * 60,
    categoria: peticion.intereses[0], transporte: peticion.movilidad[0],
    fecha_plan: fecha, creado_en: fecha, actualizado_en: fecha,
  };
  await AsyncStorage.setItem(clave, JSON.stringify([{ ficha, peticion: preferencias, opciones: respuesta.planes }, ...registros]));
  return { ...respuesta, id_plan: id };
}

export async function listar(antesDe?: number): Promise<PlanGuardado[]> {
  const { registros } = await leer();
  return registros.filter((r) => antesDe == null || r.ficha.id < antesDe).sort((a, b) => b.ficha.id - a.ficha.id).slice(0, 20).map((r) => r.ficha);
}

export async function detalle(id: number): Promise<PlanGuardado> {
  return encontrar((await leer()).registros, id).ficha;
}

export async function cambiar(id: number, cambios: CambioPlan): Promise<PlanGuardado> {
  const { clave, registros } = await leer();
  const registro = encontrar(registros, id);
  if (cambios.titulo != null && (!cambios.titulo.trim() || cambios.titulo.trim().length > 80)) throw new Error('Escribe un nombre de 1 a 80 caracteres.');
  if (cambios.tipo_seleccionado && !registro.opciones.some((p) => p.tipo === cambios.tipo_seleccionado)) throw new Error('Elige una alternativa disponible.');
  if (cambios.estado_usuario && !(cambios.tipo_seleccionado ?? registro.ficha.tipo_seleccionado)) throw new Error('Primero elige una alternativa.');
  registro.ficha = {
    ...registro.ficha,
    ...(cambios.tipo_seleccionado ? { estado_usuario: 'guardado' as const } : {}),
    ...cambios,
    ...(cambios.titulo != null ? { titulo: cambios.titulo.trim() } : {}),
    actualizado_en: new Date().toISOString(),
  };
  await AsyncStorage.setItem(clave, JSON.stringify(registros));
  return registro.ficha;
}

export async function borrar(id: number): Promise<void> {
  const { clave, registros } = await leer();
  encontrar(registros, id);
  await AsyncStorage.setItem(clave, JSON.stringify(registros.filter((r) => r.ficha.id !== id)));
}

export async function recuperar(id: number, origen: Coordenada, horaSalida: string): Promise<PlanRecuperado> {
  const registro = encontrar((await leer()).registros, id);
  const opcion = registro.opciones.find((p) => p.tipo === registro.ficha.tipo_seleccionado);
  if (!opcion) throw new Error('Primero elige y guarda una alternativa.');
  const peticion: PeticionPlan = { ...registro.peticion, origen, hora_salida: horaSalida, dia: diaDeHoy() };
  const lugares = opcion.paradas.map((p) => LUGARES.find((l) => l._id === p.lugar_id));
  if (lugares.some((l) => !l)) throw new Error('Falta un lugar del ejemplo. El plan sigue guardado.');
  const evaluada = reconstruirEjemplo(lugares.filter((l) => l != null), peticion, opcion.tipo);
  const respuesta: RespuestaPlanes = {
    ...evaluada, id_plan: id,
    aviso: 'Modo demostración: recorrido revisado con datos de ejemplo para salir ahora.',
  };
  return { peticion, respuesta };
}
