import { useState } from 'react'

/** Ejecuta una llamada a la API guardando si está en curso y el error que regrese (para mostrarlo). */
export default function useAccion() {
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState('')

  async function ejecutar<T>(accion: () => Promise<T>): Promise<T | undefined> {
    setOcupado(true)
    setError('')
    try {
      return await accion()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
      return undefined
    } finally {
      setOcupado(false)
    }
  }

  return { ocupado, error, setError, ejecutar }
}
