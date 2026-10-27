// Secciones del dashboard. En escritorio van en la barra lateral y en celular como pestañas.
// La sección activa vive en la URL (?seccion=planes) para que se pueda compartir o recargar.

import {
  IconoBus,
  IconoChat,
  IconoCerebro,
  IconoDashboard,
  IconoItinerario,
  IconoMatraz,
  IconoReporte,
} from '../../compartido/componentes/Iconos.tsx'

export const SECCIONES = [
  { id: 'resumen', texto: 'Resumen', Icono: IconoDashboard, descripcion: 'Uso general de Kompás en el periodo elegido.' },
  { id: 'planes', texto: 'Planes', Icono: IconoItinerario, descripcion: 'Qué buscan las personas al crear un plan: intereses, contexto, presupuesto y horario.' },
  { id: 'sistema', texto: 'Sistema experto', Icono: IconoCerebro, descripcion: 'Cómo decide el motor de reglas R01–R20 y qué reglas se activan más.' },
  { id: 'movilidad', texto: 'Movilidad', Icono: IconoBus, descripcion: 'Recorridos guardados por medio de transporte, rutas más usadas y paradas donde más se sube y se baja.' },
  { id: 'reportes', texto: 'Reportes y lugares', Icono: IconoReporte, descripcion: 'Reportes comunitarios y lugares registrados en la zona piloto.' },
  { id: 'laboratorio', texto: 'Laboratorio IA', Icono: IconoMatraz, descripcion: 'Búsqueda (DFS, UCS, voraz y A*), algoritmo genético, transbordos con A* y distancias Euclidiana vs. Manhattan.' },
  { id: 'asistente', texto: 'Asistente', Icono: IconoChat, descripcion: 'Uso del asistente con IA de la app (solo datos agregados, nunca el contenido de los mensajes).' },
] as const

export type IdSeccion = (typeof SECCIONES)[number]['id']

export const seccionDe = (valor: string | null) => SECCIONES.find((s) => s.id === valor) ?? SECCIONES[0]
