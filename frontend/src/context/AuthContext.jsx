import { useCallback, useMemo, useState } from 'react'
import * as api from '../services/api.js'
import { AuthContext } from './auth.js'

export function AuthProvider({ children }) {
  const [sesion, setSesion] = useState(() => api.leerSesion())

  const iniciar = useCallback((nueva) => {
    api.guardarSesion(nueva)
    setSesion(nueva)
  }, [])

  const valor = useMemo(
    () => ({
      usuario: sesion?.usuario ?? null,
      login: async (datos) => iniciar(await api.login(datos)),
      registrar: async (datos) => iniciar(await api.registrar(datos)),
      logout: () => iniciar(null),
    }),
    [sesion, iniciar],
  )

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}
