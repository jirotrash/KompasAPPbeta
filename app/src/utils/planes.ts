import type { PlanGuardado } from '@/types/dominio';

export const ESTADOS_GUARDADOS: Record<PlanGuardado['estado_usuario'], string> = {
  borrador: 'Por elegir', guardado: 'Guardado', realizado: 'Realizado',
};

export function fechaPlan(valor: string | null) {
  if (!valor) return 'Sin fecha registrada';
  const fecha = new Date(valor);
  return Number.isNaN(fecha.getTime()) ? 'Sin fecha registrada' : fecha.toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' });
}
