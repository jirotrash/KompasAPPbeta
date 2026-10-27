import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../modulos/cuenta'

/** Solo con sesión iniciada; si no, manda a /login y recuerda a dónde quería ir. */
export default function RutaPrivada({ children }: { children: ReactNode }) {
  const { usuario } = useAuth()
  const location = useLocation()
  if (!usuario) return <Navigate to="/login" replace state={{ desde: location }} />
  return children
}
