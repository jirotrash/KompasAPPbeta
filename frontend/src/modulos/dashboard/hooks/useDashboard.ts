import { useCallback, useEffect, useState } from 'react'
import * as api from '../api.ts'
import type { DatosDashboard, Filtros } from '../tipos.ts'

const FUENTES: { [K in keyof DatosDashboard]: (filtros: Filtros) => Promise<DatosDashboard[K]> } = {
  kpis: api.obtenerKpis,
  series: api.obtenerSeries,
  planes: api.obtenerPlanes,
  sistema: api.obtenerSistemaExperto,
  movilidad: api.obtenerMovilidad,
  reportes: api.obtenerReportesDashboard,
  lugares: api.obtenerLugaresDashboard,
  laboratorio: api.obtenerLaboratorio,
  asistente: api.obtenerAsistente,
}

type Consulta = { filtros: Filtros; intento: number }
type Resultado = { para: Consulta | null; datos: DatosDashboard | null; error: string }

/**
 * Carga todos los endpoints del dashboard en paralelo con los filtros aplicados.
 * `filtros` debe cambiar de referencia solo cuando el usuario pulsa Actualizar.
 */
export default function useDashboard(filtros: Filtros) {
  const [intento, setIntento] = useState(0)
  // `para` recuerda qué consulta respondió: si no coincide con la actual, se está cargando
  const [resultado, setResultado] = useState<Resultado>({ para: null, datos: null, error: '' })

  useEffect(() => {
    let vigente = true
    const consulta = { filtros, intento }
    const claves = Object.keys(FUENTES) as (keyof DatosDashboard)[]
    Promise.all(claves.map((clave) => FUENTES[clave](filtros).then((datos) => [clave, datos] as const)))
      .then((pares) => vigente && setResultado({ para: consulta, datos: Object.fromEntries(pares) as DatosDashboard, error: '' }))
      .catch((error: unknown) =>
        vigente && setResultado((previo) => ({ ...previo, para: consulta, error: error instanceof Error ? error.message : String(error) })),
      )
    return () => {
      vigente = false
    }
  }, [filtros, intento])

  const recargar = useCallback(() => setIntento((n) => n + 1), [])
  const cargando = resultado.para?.filtros !== filtros || resultado.para?.intento !== intento

  return { datos: resultado.datos, error: cargando ? '' : resultado.error, cargando, recargar }
}
