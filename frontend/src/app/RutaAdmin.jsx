import { Navigate } from 'react-router-dom'
import { useAuth } from '../modulos/cuenta'

/** Solo para rol admin (dashboard). Un usuario normal regresa al inicio; la API también responde 403. */
export default function RutaAdmin({ children }) {
  const { usuario } = useAuth()
  if (usuario?.rol !== 'admin') return <Navigate to="/" replace />
  return children
}
