// Implementación de ejemplo de cada endpoint (misma forma de respuesta que la API real).
import { estaDentroDeZona, type Coordenada } from '@/constants/zona';
import type { Alternativa, Lugar, NuevoReporte, NuevoUsuario, PeticionPlan, RespuestaRutas, Sesion } from '@/types/dominio';
import { desdeGeoJSON, distanciaKm, FACTOR_CALLES, VELOCIDAD_KMH } from '@/utils/geo';

import { trazarPorCalles } from '../mapas';
import { LUGARES } from './datos';
import { inferirPlanes } from './motor';
import { agregarReporte, reportesVigentes } from './reportes';
import { autobusesEntre } from './traslados';

const esperar = (ms = 450) => new Promise((r) => setTimeout(r, ms));

class ErrorMock extends Error {
  constructor(
    mensaje: string,
    public estado: number,
  ) {
    super(mensaje);
  }
}

// ─────────────── Auth ───────────────

export async function login({ email, password }: { email: string; password: string }): Promise<Sesion> {
  await esperar();
  if (!email.includes('@') || password.length < 6) throw new ErrorMock('Correo o contraseña incorrectos.', 401);
  const nombre = email.split('@')[0];
  return { token: 'token-de-ejemplo', usuario: { id: 1, nombre: nombre[0].toUpperCase() + nombre.slice(1), email, rol: 'usuario' } };
}

export async function registrar({ password, segundo_apellido, ...datos }: NuevoUsuario): Promise<Sesion> {
  await esperar();
  if (!datos.nombre || !datos.primer_apellido || !datos.email.includes('@') || password.length < 6) {
    throw new ErrorMock('Revisa los datos: la contraseña necesita al menos 6 caracteres.', 422);
  }
  return { token: 'token-de-ejemplo', usuario: { id: 1, ...datos, segundo_apellido: segundo_apellido || null, rol: 'usuario' } };
}

// ─────────────── Rutas ───────────────

export async function buscarRutas({ origen, destino, hora }: { origen: Coordenada; destino: Coordenada; hora: string }): Promise<RespuestaRutas> {
  await esperar();
  if (!estaDentroDeZona(origen) || !estaDentroDeZona(destino)) {
    return {
      datos_suficientes: false,
      mensaje: 'El origen o el destino está fuera de la zona piloto (Toluca, Lerma y San Mateo Atenco).',
      alternativas: [],
    };
  }

  const autobuses = autobusesEntre(origen, destino, hora);

  // Trazo real por calles (OSRM); si no responde se estima por distancia en línea recta
  const [callesPie, callesAuto] = await Promise.all([
    trazarPorCalles(origen, destino, 'pie'),
    trazarPorCalles(origen, destino, 'auto'),
  ]);
  const kmEstimados = distanciaKm(origen, destino) * FACTOR_CALLES;
  const FUENTE_CALLES = 'OSRM · OpenStreetMap';

  const kmPie = callesPie?.distancia_km ?? kmEstimados;
  const pie: Alternativa = {
    id: 'pie',
    modo: 'pie',
    distancia_km: kmPie,
    tiempos: { caminata: callesPie?.duracion_min ?? Math.round((kmEstimados / VELOCIDAD_KMH.pie) * 60), espera: null, trayecto: null },
    trazo: callesPie?.trazo,
    fuente: callesPie ? FUENTE_CALLES : 'Estimación por distancia',
    fecha_verificacion: null,
    reglas_cumplidas: kmPie <= 1.5 ? ['R12'] : [],
    avisos: kmPie > 4 ? ['Trayecto largo para hacerlo a pie.'] : [],
  };
  const auto = (modo: 'taxi' | 'app'): Alternativa => ({
    id: modo,
    modo,
    distancia_km: callesAuto?.distancia_km ?? kmEstimados,
    tiempos: {
      caminata: null,
      espera: 5,
      trayecto: callesAuto?.duracion_min ?? Math.round((kmEstimados / VELOCIDAD_KMH.auto) * 60),
    },
    trazo: callesAuto?.trazo,
    fuente: callesAuto ? FUENTE_CALLES : 'Estimación por distancia',
    fecha_verificacion: null,
    avisos: ['El tiempo no considera el tráfico.', 'La tarifa la define el proveedor; consúltala en su app o con el conductor.'],
  });

  return {
    datos_suficientes: autobuses.length > 0,
    mensaje: autobuses.length ? undefined : 'No tenemos información suficiente de transporte público para esta ruta.',
    alternativas: [...autobuses, pie, auto('taxi'), auto('app')],
  };
}

// ─────────────── Lugares y planes ───────────────

export async function buscarLugares({ cerca, categoria }: { cerca?: Coordenada; categoria?: string } = {}): Promise<Lugar[]> {
  await esperar(250);
  const lista = categoria ? LUGARES.filter((l) => l.categoria === categoria) : [...LUGARES];
  if (cerca) {
    lista.sort(
      (a, b) => distanciaKm(cerca, desdeGeoJSON(a.ubicacion.coordinates)) - distanciaKm(cerca, desdeGeoJSON(b.ubicacion.coordinates)),
    );
  }
  return lista;
}

export async function generarPlanes(peticion: PeticionPlan) {
  await esperar(700);
  return inferirPlanes(LUGARES, peticion);
}

// ─────────────── Reportes ───────────────

export async function crearReporte(datos: NuevoReporte) {
  await esperar();
  return agregarReporte(datos);
}

export async function obtenerReportes(rutaId?: string) {
  await esperar(250);
  const vigentes = reportesVigentes();
  return rutaId ? vigentes.filter((r) => r.ruta_id === rutaId) : vigentes;
}
