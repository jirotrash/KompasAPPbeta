// Formatos y ayudas del panel de administración.

import type { GeoPunto } from '../../compartido/tipos/dominio.ts'

/** Confirmación antes de borrar (diálogo nativo: accesible y sin dependencias). */
export const confirmar = (texto: string) => window.confirm(texto)

export function fechaHora(iso: string) {
  return new Date(iso).toLocaleString('es-MX', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export const coordenadas = ({ coordinates: [lng, lat] }: GeoPunto) => `${lat.toFixed(4)}, ${lng.toFixed(4)}`
