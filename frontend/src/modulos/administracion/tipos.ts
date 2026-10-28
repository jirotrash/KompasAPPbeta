// Tipos de /api/admin/... (backend/app/modulos/<módulo>/esquemas.py). Coordenadas GeoJSON: [lng, lat].

import type { GeoPunto, Parada, ParGeoJSON, Reporte, Ruta } from '../../compartido/tipos/dominio.ts'

export type RutaAdmin = Ruta
export type RutaEntrada = { nombre: string; trazo: ParGeoJSON[]; paradas: Parada[] }

export type LugarAdmin = {
  id: number
  _id: string
  nombre: string
  lat: number
  lng: number
  ubicacion: GeoPunto
  categoria: string | null
  id_categoria: number | null
  interes: string | null
}
export type LugarEntrada = { nombre: string; id_categoria: number; ubicacion: GeoPunto }

/** protegida: la usan la app y el sistema experto (no se borra ni cambia de clave). */
export type CategoriaAdmin = { id: number; nombre: string; descripcion: string | null; clave: string; protegida: boolean }
export type CategoriaEntrada = { nombre: string; descripcion: string | null }
export type TransporteAdmin = { id: number; nombre: string; clave: string; protegida: boolean }
export type TransporteEntrada = { nombre: string }

export type EstadoReporte = Reporte['estado']
export type ReporteAdmin = Reporte & { id_usuario?: number | null; vigente: boolean }

export type Busqueda = {
  id: string
  id_usuario: number | null
  origen: GeoPunto
  destino: GeoPunto
  datos_suficientes: boolean
  opciones_autobus: number
  rutas: number[]
  distancia_km: number | null
  creado_en: string
}

export type EstadoSolicitud = 'pendiente' | 'atendida' | 'descartada'
export type Solicitud = {
  id: string
  id_usuario: number
  origen: GeoPunto
  destino: GeoPunto
  comentario: string | null
  estado: EstadoSolicitud
  nota_admin: string | null
  creado_en: string
  actualizado_en: string
}
