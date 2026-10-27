import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { guardarSesion, leerSesion } from '../../../compartido/api/cliente.ts'
import type { Sesion } from '../../../compartido/tipos/dominio.ts'
import * as api from '../api.ts'
import { AuthContext, type ValorAuth } from './auth.ts'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [sesion, setSesion] = useState<Sesion | null>(() => leerSesion())

  const iniciar = useCallback((nueva: Sesion | null) => {
    guardarSesion(nueva)
    setSesion(nueva)
    return nueva
  }, [])

  const valor = useMemo<ValorAuth>(
    () => ({
      usuario: sesion?.usuario ?? null,
      login: async (datos) => iniciar(await api.login(datos)),
      registrar: async (datos) => iniciar(await api.registrar(datos)),
      logout: () => {
        iniciar(null)
      },
    }),
    [sesion, iniciar],
  )

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}
