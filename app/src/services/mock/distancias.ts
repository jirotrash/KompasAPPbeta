// Mismas respuestas que GET /api/distancias/plano y /geo (backend/app/routers/distancias.py).
import type { Coordenada } from '@/constants/zona';
import type { ComparacionDistancias, ComparacionGeo, PuntoPlano } from '@/types/dominio';
import { desgloseManhattanKm, distanciaEuclidiana, distanciaKm, distanciaManhattan } from '@/utils/geo';

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

const r3 = (n: number) => Math.round(n * 1000) / 1000;
/** Igual que minutos_caminando() del backend: ≈ 12 min por km. */
const minutosCaminando = (km: number) => Math.max(1, Math.floor(km * 12 + 0.5));

export async function compararDistanciasGeo(origen: Coordenada, destino: Coordenada): Promise<ComparacionGeo> {
  const { esteOeste, norteSur } = desgloseManhattanKm(origen, destino);
  const euclidiana = Math.hypot(esteOeste, norteSur);
  const manhattan = esteOeste + norteSur;
  const recta = distanciaKm(origen, destino);

  return {
    origen,
    destino,
    esquina: { lat: origen.lat, lng: destino.lng },
    este_oeste_km: r3(esteOeste),
    norte_sur_km: r3(norteSur),
    linea_recta_km: r3(recta),
    euclidiana_km: r3(euclidiana),
    manhattan_km: r3(manhattan),
    diferencia_km: r3(manhattan - euclidiana),
    minutos_caminando_recta: minutosCaminando(recta),
    minutos_caminando_calles: minutosCaminando(manhattan),
    pasos: {
      euclidiana:
        `√(${fmt(esteOeste)}² + ${fmt(norteSur)}²) = ` +
        `√(${fmt(esteOeste ** 2)} + ${fmt(norteSur ** 2)}) = ${fmt(euclidiana)} km`,
      manhattan: `${fmt(esteOeste)} + ${fmt(norteSur)} = ${fmt(manhattan)} km`,
    },
    nota: 'Kompás usa la distancia Manhattan para estimar trayectos por calles.',
  };
}
