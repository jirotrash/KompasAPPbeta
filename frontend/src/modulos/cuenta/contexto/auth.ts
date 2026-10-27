import { createContext, useContext } from 'react'
import type { Credenciales, NuevoUsuario, Sesion, Usuario } from '../../../compartido/tipos/dominio.ts'

export type ValorAuth = {
  usuario: Usuario | null
  login: (datos: Credenciales) => Promise<Sesion | null>
  registrar: (datos: NuevoUsuario) => Promise<Sesion | null>
  logout: () => void
}

export const AuthContext = createContext<ValorAuth | null>(null)

export function useAuth(): ValorAuth {
  const valor = useContext(AuthContext)
  if (!valor) throw new Error('useAuth debe usarse dentro de <AuthProvider>')
  return valor
}
