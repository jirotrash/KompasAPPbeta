// Reportes comunitarios de ejemplo, guardados en memoria mientras la app está abierta.
import type { NuevoReporte, Reporte, TipoReporte } from '@/types/dominio';

const VIGENCIA_H: Record<TipoReporte, number> = { cierre_total: 6, accidente: 2, manifestacion: 3, afluencia: 1 };
const enHoras = (h: number, desde = Date.now()) => new Date(desde + h * 3600_000).toISOString();

const reportes: Reporte[] = [
  {
    _id: 'reporte_ejemplo_1',
    tipo: 'manifestacion',
    ubicacion: { type: 'Point', coordinates: [-99.625, 19.279] },
    ruta_id: 'ruta_ejemplo_b',
    observado_en: new Date().toISOString(),
    vigente_hasta: enHoras(3),
    confirmaciones: 1,
    estado: 'pendiente',
    comentario: 'Reporte de ejemplo',
  },
];

export const reportesVigentes = () => reportes.filter((r) => new Date(r.vigente_hasta).getTime() > Date.now());

export function agregarReporte(datos: NuevoReporte): Reporte {
  const observado = new Date(datos.observado_en).getTime();
  const nuevo: Reporte = {
    ...datos,
    _id: `reporte_${Date.now()}`,
    vigente_hasta: enHoras(VIGENCIA_H[datos.tipo], observado),
    confirmaciones: 0,
    estado: 'pendiente',
  };
  reportes.unshift(nuevo);
  return nuevo;
}
