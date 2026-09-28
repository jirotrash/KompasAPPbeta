// Catálogos y cálculos del dominio compartidos por varias pantallas.

export const CATEGORIAS = {
  cafeteria: 'Cafetería',
  restaurante: 'Restaurante',
  parque: 'Parque',
  museo: 'Museo',
  cine: 'Cine',
  plaza: 'Plaza comercial',
}

export const nombreCategoria = (c) => CATEGORIAS[c] ?? c

export const CONTEXTOS = {
  cita: 'Cita',
  amigos: 'Amigos',
  familia: 'Familia',
  cotidiano: 'Cotidiano',
}

export const TIPOS_REPORTE = {
  afluencia: 'Afluencia',
  cierre_total: 'Cierre total',
  accidente: 'Accidente',
  manifestacion: 'Manifestación',
}

/** Suma de caminata + espera + trayecto + transbordos (minutos estimados). */
export const tiempoTotal = ({ tiempos }) =>
  ['caminata', 'espera', 'trayecto', 'transbordos'].reduce((s, k) => s + (tiempos[k] ?? 0), 0)

const DIAS = ['dom', 'lun', 'mar', 'mie', 'jue', 'vie', 'sab']
export const diaDeHoy = () => DIAS[new Date().getDay()]

export const horaActual = () => new Date().toTimeString().slice(0, 5)

/** Minúsculas y sin acentos, para comparar textos al buscar. */
export const normalizarTexto = (t) =>
  t
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .trim()
