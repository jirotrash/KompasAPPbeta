// Misma respuesta que GET /api/distancias/plano (backend/app/ia/metricas_distancia.py).
import type { ComparacionDistancias, PuntoPlano } from '@/types/dominio';
import { distanciaEuclidiana, distanciaManhattan } from '@/utils/geo';

/** 5 → "5", 5.8309 → "5.83" (como fmt() del backend) */
const fmt = (n: number) => String(Math.round(n * 100) / 100);
const r4 = (n: number) => Math.round(n * 10000) / 10000;

export async function compararDistancias(a: PuntoPlano, b: PuntoPlano): Promise<ComparacionDistancias> {
  const dx = Math.abs(b.x - a.x);
  const dy = Math.abs(b.y - a.y);
  const euclidiana = distanciaEuclidiana(a, b);
  const manhattan = distanciaManhattan(a, b);

  return {
    a,
    b,
    esquina: { x: b.x, y: a.y },
    horizontal: r4(dx),
    vertical: r4(dy),
    euclidiana: r4(euclidiana),
    manhattan: r4(manhattan),
    diferencia: r4(manhattan - euclidiana),
    alineados: dx === 0 || dy === 0,
    pasos: {
      euclidiana:
        `√((${fmt(b.x)} - ${fmt(a.x)})² + (${fmt(b.y)} - ${fmt(a.y)})²) = ` +
        `√(${fmt(dx ** 2)} + ${fmt(dy ** 2)}) = √${fmt(dx ** 2 + dy ** 2)} = ${fmt(euclidiana)}`,
      manhattan: `|${fmt(b.x)} - ${fmt(a.x)}| + |${fmt(b.y)} - ${fmt(a.y)}| = ${fmt(dx)} + ${fmt(dy)} = ${fmt(manhattan)}`,
    },
  };
}
