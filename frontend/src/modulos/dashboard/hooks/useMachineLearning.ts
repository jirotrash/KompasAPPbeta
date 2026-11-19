import { useCallback, useEffect, useState } from 'react'
import * as api from '../api.ts'
import type { ComparacionAlgoritmos, DiagnosticoAjuste, OptimizacionHiperparametros } from '../tiposML.ts'

type Estado<T> = { datos: T | null; error: string; cargando: boolean }
type Resultado<T> = { para: number | null; datos: T | null; error: string }
type Cache = { ajuste?: Promise<DiagnosticoAjuste>; comparacion?: Promise<ComparacionAlgoritmos>; optimizacion?: Promise<OptimizacionHiperparametros> }

const mensajeDe = (e: unknown) => (e instanceof Error ? e.message : String(e))

// Los modelos se entrenan en el backend en cada llamada (P06 tarda varios segundos con GridSearchCV).
// Se guardan aquí para no reentrenar cada vez que el admin entra y sale de la sección.
let cache: Cache = {}

function useConsulta<K extends keyof Cache>(clave: K, cargar: () => NonNullable<Cache[K]>, intento: number) {
  type T = Awaited<NonNullable<Cache[K]>>
  // `para` recuerda a qué intento respondió: si no coincide con el actual, se está cargando (como useDashboard)
  const [resultado, setResultado] = useState<Resultado<T>>({ para: null, datos: null, error: '' })

  useEffect(() => {
    let vigente = true
    const promesa = (cache[clave] ??= cargar()) as Promise<T>
    promesa
      .then((datos) => vigente && setResultado({ para: intento, datos, error: '' }))
      .catch((e: unknown) => {
        delete cache[clave]
        if (vigente) setResultado({ para: intento, datos: null, error: mensajeDe(e) })
      })
    return () => {
      vigente = false
    }
  }, [clave, cargar, intento])

  const cargando = resultado.para !== intento
  return { datos: cargando ? null : resultado.datos, error: cargando ? '' : resultado.error, cargando } satisfies Estado<T>
}

/**
 * Carga P04, P05 y P06 en paralelo. P06 (lento) se muestra aparte para que las gráficas
 * principales aparezcan sin esperar a la búsqueda en rejilla.
 */
export default function useMachineLearning() {
  const [intento, setIntento] = useState(0)
  const ajuste = useConsulta('ajuste', api.obtenerDiagnosticoAjuste, intento)
  const comparacion = useConsulta('comparacion', api.obtenerComparacionAlgoritmos, intento)
  const optimizacion = useConsulta('optimizacion', api.obtenerOptimizacionHiperparametros, intento)

  const recargar = useCallback(() => {
    cache = {}
    setIntento((n) => n + 1)
  }, [])

  return { ajuste, comparacion, optimizacion, recargar }
}
