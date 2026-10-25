import { useCallback, useEffect, useState } from 'react'
import * as api from '../api.js'

const FUENTES = {
  kpis: api.obtenerKpis,
  series: api.obtenerSeries,
  planes: api.obtenerPlanes,
  sistema: api.obtenerSistemaExperto,
  movilidad: api.obtenerMovilidad,
  reportes: api.obtenerReportesDashboard,
  lugares: api.obtenerLugaresDashboard,
  laboratorio: api.obtenerLaboratorio,
}

/**
 * Carga todos los endpoints del dashboard en paralelo con los filtros aplicados.
 * `filtros` debe cambiar de referencia solo cuando el usuario pulsa Actualizar.
 * @param {{desde?: string, hasta?: string, agrupar: string, incluirDemo: boolean}} filtros
 */
export default function useDashboard(filtros) {
  const [intento, setIntento] = useState(0)
  // `para` recuerda qué consulta respondió: si no coincide con la actual, se está cargando
  const [resultado, setResultado] = useState({ para: null, datos: null, error: '' })

  useEffect(() => {
    let vigente = true
    const consulta = { filtros, intento }
    Promise.all(Object.entries(FUENTES).map(([clave, pedir]) => pedir(filtros).then((datos) => [clave, datos])))
      .then((pares) => vigente && setResultado({ para: consulta, datos: Object.fromEntries(pares), error: '' }))
      .catch((error) => vigente && setResultado((previo) => ({ ...previo, para: consulta, error: error.message })))
    return () => {
      vigente = false
    }
  }, [filtros, intento])

  const recargar = useCallback(() => setIntento((n) => n + 1), [])
  const cargando = resultado.para?.filtros !== filtros || resultado.para?.intento !== intento

  return { datos: resultado.datos, error: cargando ? '' : resultado.error, cargando, recargar }
}
