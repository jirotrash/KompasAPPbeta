// Secciones del panel de administración (/administrar?seccion=rutas). Igual que en el dashboard: en escritorio
// van en la barra lateral y en celular como pestañas.

import {
  IconoBandeja,
  IconoBuscar,
  IconoEtiqueta,
  IconoReporte,
  IconoRuta,
  IconoUbicacion,
} from '../../compartido/componentes/Iconos.tsx'

export const SECCIONES_ADMIN = [
  { id: 'rutas', texto: 'Rutas', Icono: IconoRuta, descripcion: 'Da de alta las rutas de transporte: nombre, trazo dibujado en el mapa y paradas. La app las usa para decir en qué camión subir y dónde bajar.' },
  { id: 'lugares', texto: 'Lugares', Icono: IconoUbicacion, descripcion: 'Lugares de la zona piloto que aparecen en "Cerca de ti" y en el buscador de la app.' },
  { id: 'catalogos', texto: 'Categorías y transportes', Icono: IconoEtiqueta, descripcion: 'Catálogos de la app. Los marcados como protegidos los usa el sistema experto: no se borran ni cambian de clave.' },
  { id: 'reportes', texto: 'Reportes', Icono: IconoReporte, descripcion: 'Reportes de la comunidad (cierres, accidentes, manifestaciones y afluencia): verifícalos, descártalos o bórralos.' },
  { id: 'busquedas', texto: 'Búsquedas', Icono: IconoBuscar, descripcion: 'Lo que la gente busca en "¿Cómo llego?". Las búsquedas sin camión muestran qué rutas faltan.' },
  { id: 'solicitudes', texto: 'Solicitudes de rutas', Icono: IconoBandeja, descripcion: 'Rutas que la gente pidió desde la app cuando no encontró camión.' },
] as const

export type IdSeccionAdmin = (typeof SECCIONES_ADMIN)[number]['id']

export const seccionAdminDe = (valor: string | null) => SECCIONES_ADMIN.find((s) => s.id === valor) ?? SECCIONES_ADMIN[0]
