import { useSyncExternalStore } from 'react'

const consulta = window.matchMedia('(max-width: 767px)')
const suscribir = (avisar) => {
  consulta.addEventListener('change', avisar)
  return () => consulta.removeEventListener('change', avisar)
}

/** true cuando la pantalla es de celular (menor que el breakpoint md de Tailwind). */
export default function useEsMovil() {
  return useSyncExternalStore(suscribir, () => consulta.matches)
}
