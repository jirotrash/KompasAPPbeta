// Secciones del dashboard. En escritorio van en la barra lateral y en celular como pestañas.
// La sección activa vive en la URL (?seccion=planes) para que se pueda compartir o recargar.

import {
  IconoBus,
  IconoCerebro,
  IconoDashboard,
  IconoItinerario,
  IconoMatraz,
  IconoReporte,
} from '../../compartido/componentes/Iconos.jsx'

export const SECCIONES = [
  { id: 'resumen', texto: 'Resumen', Icono: IconoDashboard, descripcion: 'Uso general de Kompás en el periodo elegido.' },
  { id: 'planes', texto: 'Planes', Icono: IconoItinerario, descripcion: 'Qué buscan las personas al crear un plan: intereses, contexto, presupuesto y horario.' },
  { id: 'sistema', texto: 'Sistema experto', Icono: IconoCerebro, descripcion: 'Cómo decide el motor de reglas R01–R20 y qué reglas se activan más.' },
  { id: 'movilidad', texto: 'Movilidad', Icono: IconoBus, descripcion: 'Recorridos guardados por medio de transporte y rutas más usadas.' },
  { id: 'reportes', texto: 'Reportes y lugares', Icono: IconoReporte, descripcion: 'Reportes comunitarios y lugares registrados en la zona piloto.' },
  { id: 'laboratorio', texto: 'Laboratorio IA', Icono: IconoMatraz, descripcion: 'Uso de las demostraciones académicas: búsqueda DFS y distancias Euclidiana vs. Manhattan.' },
]

export const seccionDe = (valor) => SECCIONES.find((s) => s.id === valor) ?? SECCIONES[0]
