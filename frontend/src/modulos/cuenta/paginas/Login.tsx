import { useState, type ChangeEvent, type FormEvent } from 'react'
import type { Location } from 'react-router-dom'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { MensajeError } from '../../../compartido/componentes/Avisos.tsx'
import PantallaAcceso from '../componentes/PantallaAcceso.tsx'
import { useAuth } from '../contexto/auth.ts'
import { USA_MOCK } from '../../../compartido/api/cliente.ts'

export default function Login() {
  const { usuario, login, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [datos, setDatos] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  if (usuario) return <Navigate to="/" replace />

  async function enviar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError('')
    setEnviando(true)
    try {
      const sesion = await login(datos)
      // El panel es solo para administradores: no se deja abierta la sesión de otros roles
      if (sesion?.usuario.rol !== 'admin') {
        logout()
        setError('Esta cuenta no es de administrador. El panel de Kompás solo lo pueden abrir administradores.')
        setEnviando(false)
        return
      }
      const desde = (location.state as { desde?: Location } | null)?.desde
      navigate(desde ? `${desde.pathname}${desde.search ?? ''}` : '/', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo iniciar sesión.')
      setEnviando(false)
    }
  }

  const cambiar = (e: ChangeEvent<HTMLInputElement>) => setDatos({ ...datos, [e.target.name]: e.target.value })

  return (
    <PantallaAcceso titulo="Inicia sesión">
      <form onSubmit={enviar} className="space-y-4" noValidate>
        <div>
          <label htmlFor="email" className="etiqueta">
            Correo electrónico
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            className="campo"
            value={datos.email}
            onChange={cambiar}
          />
        </div>
        <div>
          <label htmlFor="password" className="etiqueta">
            Contraseña
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            className="campo"
            value={datos.password}
            onChange={cambiar}
          />
        </div>
        <MensajeError>{error}</MensajeError>
        <button type="submit" className="boton-primario w-full" disabled={enviando}>
          {enviando ? 'Entrando…' : 'Entrar'}
        </button>
        {USA_MOCK && (
          <p className="text-center text-xs text-texto-suave">
            Modo demostración: cualquier correo y una contraseña de 6 o más caracteres.
          </p>
        )}
      </form>
    </PantallaAcceso>
  )
}
