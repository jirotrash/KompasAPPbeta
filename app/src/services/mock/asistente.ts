// SIMULACIÓN del asistente para probar la interfaz sin API ni Ollama (EXPO_PUBLIC_USE_MOCK=true).
// Las respuestas son de DEMOSTRACIÓN: se marcan como tales y usan las rutas y lugares de ejemplo.
import type { Coordenada } from '@/constants/zona';
import type { Conversacion, EstadoAsistente, MensajeChat, RespuestaMensaje, ResumenConversacion, TarjetaAsistente } from '@/types/dominio';
import { desdeGeoJSON, normalizarTexto } from '@/utils/geo';

import { LUGARES } from './datos';
import { autobusesEntre } from './traslados';

const esperar = (ms = 900) => new Promise((r) => setTimeout(r, ms));
const AVISO = 'Respuesta de demostración (modo de ejemplo, sin el modelo de IA).';
const CENTRO_TOLUCA = { lat: 19.2926, lng: -99.6557, nombre: 'Centro de Toluca' };

const conversaciones = new Map<string, Conversacion>();

const ahora = () => new Date().toISOString();
const titulo = (texto: string) => {
  const palabras = texto.trim().split(/\s+/);
  return palabras.slice(0, 6).join(' ') + (palabras.length > 6 ? '…' : '');
};

export async function estado(): Promise<EstadoAsistente> {
  await esperar(200);
  return { disponible: true, modelo: 'demostración' };
}

export async function listar(): Promise<ResumenConversacion[]> {
  await esperar(250);
  return [...conversaciones.values()]
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at))
    .map((c) => {
      const visibles = c.mensajes.filter((m) => (m.rol === 'usuario' || m.rol === 'asistente') && m.contenido);
      return { id: c.id, titulo: c.titulo, ultimo_mensaje: visibles.at(-1)?.contenido ?? null, fecha: c.updated_at, total_mensajes: c.mensajes.length };
    });
}

export async function crear(): Promise<Conversacion> {
  await esperar(200);
  const c: Conversacion = { id: `demo_${Date.now()}`, titulo: null, modelo: 'demostración', mensajes: [], planes_creados: [], created_at: ahora(), updated_at: ahora() };
  conversaciones.set(c.id, c);
  return c;
}

export async function obtener(id: string): Promise<Conversacion> {
  await esperar(200);
  const c = conversaciones.get(id);
  if (!c) throw Object.assign(new Error('No encontramos esa conversación.'), { estado: 404 });
  return c;
}

export async function borrar(id: string): Promise<null> {
  await esperar(200);
  conversaciones.delete(id);
  return null;
}

/** Busca un lugar de ejemplo mencionado en el texto; si no hay, responde sin inventar. */
function responder(texto: string, ubicacion: Coordenada): { contenido: string; tarjeta?: TarjetaAsistente } {
  const n = normalizarTexto(texto);
  const lugar = LUGARES.find((l) => normalizarTexto(l.nombre).split(' ').some((p) => p.length > 4 && n.includes(p)));
  if (/(llego|llegar|ir a|como voy)/.test(n) && lugar) {
    const destino = { ...desdeGeoJSON(lugar.ubicacion.coordinates), nombre: lugar.nombre };
    const [bus] = autobusesEntre(ubicacion, destino, '12:00');
    const contenido = bus
      ? `Puedes tomar la ${bus.linea}: sube en ${bus.parada_subida?.nombre} y baja en ${bus.parada_bajada?.nombre}. El trayecto es de unos ${bus.tiempos.trayecto} min (estimado). ${AVISO}`
      : `No tengo una ruta de autobús de ejemplo que llegue a ${lugar.nombre}; puedes ir a pie o en taxi/app. ${AVISO}`;
    return {
      contenido,
      tarjeta: {
        tipo: 'ruta',
        titulo: `Tu ubicación → ${lugar.nombre}`,
        subtitulo: bus?.linea ?? 'A pie o en taxi/app',
        origen: { ...ubicacion, nombre: 'Tu ubicación' },
        destino,
        alternativa: bus ?? null,
        ejemplo: true,
      },
    };
  }
  if (/(llego|llegar|ir a)/.test(n)) {
    return { contenido: `No encontré ese lugar entre los lugares de ejemplo, así que no puedo darte una ruta (no invento rutas). ${AVISO}` };
  }
  return {
    contenido: `Puedo ayudarte a llegar a un lugar, buscar lugares o armar una salida en Toluca, Lerma y San Mateo Atenco. Prueba: "¿Cómo llego al museo de ejemplo?". ${AVISO}`,
  };
}

export async function enviar(id: string, texto: string, ubicacion?: Coordenada): Promise<RespuestaMensaje> {
  await esperar();
  const c = conversaciones.get(id);
  if (!c) throw Object.assign(new Error('No encontramos esa conversación.'), { estado: 404 });
  const usuario: MensajeChat = { rol: 'usuario', contenido: texto, creado_en: ahora() };
  const { contenido, tarjeta } = responder(texto, ubicacion ?? CENTRO_TOLUCA);
  const herramienta: MensajeChat[] = tarjeta ? [{ rol: 'herramienta', nombre: 'como_llegar', tarjeta, creado_en: ahora() }] : [];
  const respuesta: MensajeChat = { rol: 'asistente', contenido, duracion_ms: 900, creado_en: ahora() };
  c.mensajes.push(usuario, ...herramienta, respuesta);
  c.titulo = c.titulo ?? titulo(texto);
  c.updated_at = ahora();
  return { conversacion_id: id, titulo: c.titulo, mensaje: respuesta, tarjetas: tarjeta ? [tarjeta] : [], herramientas_usadas: tarjeta ? ['como_llegar'] : [] };
}
