// Panel de administración sin API (VITE_USE_MOCK=true). Parte de los datos de ejemplo de src/mock y guarda
// los cambios en memoria: al recargar la página se pierden. Repite las reglas de la API (zona piloto,
// categorías protegidas, 404/409) para que el panel se comporte igual.

import { ErrorApi } from '../../compartido/api/cliente.ts'
import { estaDentroDeZona, ZONA } from '../../compartido/config/zona.ts'
import type { GeoPunto, ParGeoJSON } from '../../compartido/tipos/dominio.ts'
import { LUGARES, RUTAS } from '../../mock/datos.ts'
import type {
  Busqueda,
  CategoriaAdmin,
  EstadoReporte,
  EstadoSolicitud,
  LugarAdmin,
  LugarEntrada,
  ReporteAdmin,
  RutaAdmin,
  RutaEntrada,
  Solicitud,
  TransporteAdmin,
} from './tipos.ts'

const esperar = (ms = 200) => new Promise((r) => setTimeout(r, ms))
const copia = <T>(v: T): T => structuredClone(v)

/** "Café" → "cafe", "Taxi/App" → "taxi_app" (igual que app/compartido/texto.py). */
const clave = (nombre: string) =>
  nombre.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '')

const INTERESES = ['comer', 'cafe', 'cultura', 'entretenimiento', 'aire_libre']
const MOVILIDADES = ['caminando', 'transporte_publico', 'taxi_app', 'combinado']

function enZona([lng, lat]: ParGeoJSON, que = 'Hay puntos') {
  if (!estaDentroDeZona(lat, lng)) throw new ErrorApi(`${que} fuera de la zona piloto (${ZONA.nombre}).`, 422)
}
const noEncontrado = (texto: string) => new ErrorApi(texto, 404)

// ───────────── Datos iniciales ─────────────

let siguiente = 100
const nuevoId = () => ++siguiente
const punto = (lng: number, lat: number): GeoPunto => ({ type: 'Point', coordinates: [lng, lat] })

const categoriasBD: CategoriaAdmin[] = ['Comer', 'Café', 'Cultura', 'Entretenimiento', 'Aire libre'].map((nombre, i) => ({
  id: i + 1,
  nombre,
  descripcion: null,
  clave: clave(nombre),
  protegida: true,
}))

const transportesBD: TransporteAdmin[] = ['Caminando', 'Transporte público', 'Taxi/App', 'Combinado'].map((nombre, i) => ({
  id: i + 1,
  nombre,
  clave: clave(nombre),
  protegida: true,
}))

const CATEGORIA_EJEMPLO: Record<string, string> = { cafeteria: 'cafe', restaurante: 'comer', museo: 'cultura', parque: 'aire_libre' }

function aLugar(id: number, nombre: string, ubicacion: GeoPunto, idCategoria: number): LugarAdmin {
  const categoria = categoriasBD.find((c) => c.id === idCategoria)
  const [lng, lat] = ubicacion.coordinates
  const interes = categoria && INTERESES.includes(categoria.clave) ? categoria.clave : null
  return { id, _id: String(id), nombre, lat, lng, ubicacion, categoria: categoria?.nombre ?? null, id_categoria: categoria?.id ?? null, interes }
}

let lugaresBD: LugarAdmin[] = LUGARES.map((l, i) => {
  const valor = CATEGORIA_EJEMPLO[l.categoria] ?? 'entretenimiento'
  return aLugar(i + 1, l.nombre, l.ubicacion, categoriasBD.find((c) => c.clave === valor)!.id)
})

let rutasBD: RutaAdmin[] = RUTAS.map((r, i) => ({
  id: i + 1,
  _id: String(i + 1),
  nombre: r.linea,
  trazo: r.paradas.map((p) => p.ubicacion.coordinates),
  paradas: r.paradas.map((p) => ({ nombre: p.nombre, ubicacion: p.ubicacion })),
}))

const haceHoras = (h: number) => new Date(Date.now() - h * 3_600_000).toISOString()

let reportesBD: ReporteAdmin[] = (
  [
    ['cierre_total', 1, 'pendiente', 'Calle cerrada por obra'],
    ['accidente', 0.5, 'verificado', undefined],
    ['manifestacion', 30, 'descartado', 'Ya se retiraron'],
    ['afluencia', 3, 'pendiente', undefined],
  ] as const
).map(([tipo, horas, estado, comentario], i) => {
  const vigencia = { cierre_total: 6, accidente: 2, manifestacion: 3, afluencia: 1 }[tipo]
  const fin = new Date(Date.now() - horas * 3_600_000 + vigencia * 3_600_000)
  return {
    _id: `reporte_${i + 1}`,
    tipo,
    ubicacion: punto(-99.62 + i * 0.03, 19.28 + i * 0.004),
    observado_en: haceHoras(horas),
    vigente_hasta: fin.toISOString(),
    confirmaciones: i,
    estado,
    comentario,
    id_usuario: i + 2,
    vigente: fin > new Date(),
  }
})

const busquedasBD: Busqueda[] = Array.from({ length: 14 }, (_, i) => {
  const conCamion = i % 3 === 0
  return {
    id: `busqueda_${i + 1}`,
    id_usuario: i % 4 === 0 ? null : (i % 5) + 2,
    origen: punto(-99.66 + (i % 5) * 0.03, 19.27 + (i % 3) * 0.012),
    destino: punto(-99.52 - (i % 4) * 0.02, 19.29 - (i % 2) * 0.01),
    datos_suficientes: conCamion,
    opciones_autobus: conCamion ? 1 : 0,
    rutas: conCamion ? [1] : [],
    distancia_km: Math.round((6 + (i % 7) * 1.7) * 100) / 100,
    creado_en: haceHoras(i * 5 + 1),
  }
})

let solicitudesBD: Solicitud[] = [
  ['Tomo una combi que pasa por Tollocan', 'pendiente', null],
  [null, 'pendiente', null],
  ['De la terminal a la UAEMéx', 'atendida', 'Se agregó la ruta de ejemplo B'],
].map(([comentario, estado, nota], i) => ({
  id: `solicitud_${i + 1}`,
  id_usuario: i + 3,
  origen: punto(-99.6 + i * 0.02, 19.3 - i * 0.01),
  destino: punto(-99.53 - i * 0.01, 19.28 + i * 0.005),
  comentario,
  estado: estado as EstadoSolicitud,
  nota_admin: nota,
  creado_en: haceHoras(i * 20 + 2),
  actualizado_en: haceHoras(i * 10 + 1),
}))

// ───────────── Operaciones ─────────────

export const rutas = {
  async listar() {
    await esperar()
    return copia(rutasBD)
  },
  async guardar(datos: RutaEntrada, id?: number) {
    await esperar()
    if (!datos.nombre.trim()) throw new ErrorApi('Escribe el nombre de la ruta.', 422)
    if (datos.trazo.length < 2) throw new ErrorApi('Revisa los datos enviados. trazo: el trazo necesita al menos 2 puntos', 422)
    datos.trazo.forEach((p) => enZona(p))
    datos.paradas.forEach((p) => enZona(p.ubicacion.coordinates))
    const idRuta = id ?? nuevoId()
    const ruta: RutaAdmin = {
      id: idRuta,
      _id: String(idRuta),
      nombre: datos.nombre.trim(),
      trazo: datos.trazo,
      ...(datos.paradas.length ? { paradas: datos.paradas } : {}),
    }
    if (id === undefined) rutasBD = [...rutasBD, ruta]
    else if (!rutasBD.some((r) => r.id === id)) throw noEncontrado('No encontramos esa ruta.')
    else rutasBD = rutasBD.map((r) => (r.id === id ? ruta : r))
    return copia(ruta)
  },
  async borrar(id: number) {
    await esperar()
    if (!rutasBD.some((r) => r.id === id)) throw noEncontrado('No encontramos esa ruta.')
    rutasBD = rutasBD.filter((r) => r.id !== id)
    return null
  },
}

export const lugares = {
  async listar() {
    await esperar()
    return copia(lugaresBD)
  },
  async guardar(datos: LugarEntrada, id?: number) {
    await esperar()
    if (!datos.nombre.trim()) throw new ErrorApi('Escribe el nombre del lugar.', 422)
    enZona(datos.ubicacion.coordinates, 'El lugar está')
    if (!categoriasBD.some((c) => c.id === datos.id_categoria)) throw noEncontrado('No encontramos esa categoría.')
    const lugar = aLugar(id ?? nuevoId(), datos.nombre.trim(), datos.ubicacion, datos.id_categoria)
    if (id === undefined) lugaresBD = [...lugaresBD, lugar]
    else if (!lugaresBD.some((l) => l.id === id)) throw noEncontrado('No encontramos ese lugar.')
    else lugaresBD = lugaresBD.map((l) => (l.id === id ? lugar : l))
    return copia(lugar)
  },
  async borrar(id: number) {
    await esperar()
    if (!lugaresBD.some((l) => l.id === id)) throw noEncontrado('No encontramos ese lugar.')
    lugaresBD = lugaresBD.filter((l) => l.id !== id)
    return null
  },
}

/** Mismas reglas para categorías y transportes: nombre único sin acentos y los protegidos no cambian de clave. */
function catalogo<T extends { id: number; nombre: string; clave: string; protegida: boolean }>(
  lista: T[],
  protegidas: string[],
  noExiste: string,
  enUso: (id: number) => number = () => 0,
) {
  return {
    async listar() {
      await esperar()
      return copia(lista)
    },
    async guardar(datos: { nombre: string } & Partial<T>, id?: number): Promise<T> {
      await esperar()
      const nombre = datos.nombre.trim()
      if (!clave(nombre)) throw new ErrorApi('Escribe un nombre con letras o números.', 422)
      if (lista.some((o) => o.clave === clave(nombre) && o.id !== id))
        throw new ErrorApi(`Ya existe «${nombre}» (o uno con el mismo nombre sin acentos).`, 409)
      const actual = lista.find((o) => o.id === id)
      if (id !== undefined && !actual) throw noEncontrado(noExiste)
      if (actual?.protegida && clave(nombre) !== actual.clave)
        throw new ErrorApi(`La app y el sistema experto usan «${actual.nombre}» como «${actual.clave}»: puedes cambiar acentos o mayúsculas, pero no el nombre.`, 409)
      const item = { ...actual, ...datos, id: id ?? nuevoId(), nombre, clave: clave(nombre), protegida: protegidas.includes(clave(nombre)) } as T
      if (actual) lista.splice(lista.indexOf(actual), 1, item)
      else lista.push(item)
      return copia(item)
    },
    async borrar(id: number) {
      await esperar()
      const actual = lista.find((o) => o.id === id)
      if (!actual) throw noEncontrado(noExiste)
      if (actual.protegida) throw new ErrorApi(`«${actual.nombre}» la usan la app y el sistema experto: no se puede borrar.`, 409)
      const n = enUso(id)
      if (n) throw new ErrorApi(`Hay ${n} lugar(es) con esta categoría: cámbialos de categoría antes de borrarla.`, 409)
      lista.splice(lista.indexOf(actual), 1)
      return null
    },
  }
}

export const categorias = catalogo<CategoriaAdmin>(categoriasBD, INTERESES, 'No encontramos esa categoría.', (id) =>
  lugaresBD.filter((l) => l.id_categoria === id).length,
)
export const transportes = catalogo<TransporteAdmin>(transportesBD, MOVILIDADES, 'No encontramos ese medio de transporte.')

export const reportes = {
  async listar(estado?: EstadoReporte) {
    await esperar()
    return copia(estado ? reportesBD.filter((r) => r.estado === estado) : reportesBD)
  },
  async moderar(id: string, estado: EstadoReporte) {
    await esperar()
    const reporte = reportesBD.find((r) => r._id === id)
    if (!reporte) throw noEncontrado('No encontramos ese reporte.')
    reporte.estado = estado
    return copia(reporte)
  },
  async borrar(id: string) {
    await esperar()
    if (!reportesBD.some((r) => r._id === id)) throw noEncontrado('No encontramos ese reporte.')
    reportesBD = reportesBD.filter((r) => r._id !== id)
    return null
  },
}

export async function busquedas(sinAutobus: boolean) {
  await esperar()
  return copia(sinAutobus ? busquedasBD.filter((b) => !b.datos_suficientes) : busquedasBD)
}

export const solicitudes = {
  async listar(estado?: EstadoSolicitud) {
    await esperar()
    return copia(estado ? solicitudesBD.filter((s) => s.estado === estado) : solicitudesBD)
  },
  async atender(id: string, estado: EstadoSolicitud, nota: string | null) {
    await esperar()
    const s = solicitudesBD.find((x) => x.id === id)
    if (!s) throw noEncontrado('No encontramos esa solicitud.')
    Object.assign(s, { estado, nota_admin: nota?.trim() || null, actualizado_en: new Date().toISOString() })
    return copia(s)
  },
  async borrar(id: string) {
    await esperar()
    if (!solicitudesBD.some((s) => s.id === id)) throw noEncontrado('No encontramos esa solicitud.')
    solicitudesBD = solicitudesBD.filter((s) => s.id !== id)
    return null
  },
}
