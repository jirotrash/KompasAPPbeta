import { useEffect, useState } from 'react'
import { buscarLugares } from '../services/api.js'

/** Lista de lugares de la zona para los selectores (vacía si la API falla). */
export default function useLugares() {
  const [lugares, setLugares] = useState([])

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
