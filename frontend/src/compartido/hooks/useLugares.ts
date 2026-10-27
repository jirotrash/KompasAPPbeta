import { useEffect, useState } from 'react'
import { buscarLugares } from '../api/lugares.ts'
import type { Lugar } from '../tipos/dominio.ts'

/** Lista de lugares de la zona para los selectores (vacía si la API falla). */
export default function useLugares() {
  const [lugares, setLugares] = useState<Lugar[]>([])

  useEffect(() => {
    let activo = true
    buscarLugares()
      .then((lista) => activo && setLugares(lista ?? []))
      .catch(() => activo && setLugares([]))
    return () => {
      activo = false
    }
  }, [])

  return lugares
}
