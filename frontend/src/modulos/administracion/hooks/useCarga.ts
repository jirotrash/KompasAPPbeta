import { useCallback, useEffect, useState } from 'react'

type Consulta<T> = { cargar: () => Promise<T>; intento: number }
type Resultado<T> = { para: Consulta<T> | null; datos: T | null; error: string }

/**
 * Carga una lista del panel y la vuelve a pedir con `recargar()` (después de guardar o borrar).
 * `cargar` debe ser estable (useCallback) o cambiar solo cuando cambian sus filtros.
 * Mientras recarga se conservan los datos anteriores para que la lista no parpadee.
 */
export default function useCarga<T>(cargar: () => Promise<T>) {
  const [intento, setIntento] = useState(0)
  // `para` recuerda qué consulta respondió: si no coincide con la actual, se está cargando
  const [resultado, setResultado] = useState<Resultado<T>>({ para: null, datos: null, error: '' })

  useEffect(() => {
    let vigente = true
    const consulta = { cargar, intento }
    cargar()
      .then((datos) => vigente && setResultado({ para: consulta, datos, error: '' }))
      .catch((e: unknown) => vigente && setResultado((previo) => ({ ...previo, para: consulta, error: e instanceof Error ? e.message : String(e) })))
    return () => {
      vigente = false
    }
  }, [cargar, intento])

  const recargar = useCallback(() => setIntento((n) => n + 1), [])
  const cargando = resultado.para?.cargar !== cargar || resultado.para?.intento !== intento

  return { datos: resultado.datos, error: cargando ? '' : resultado.error, cargando, recargar }
}
