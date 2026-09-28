import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { MensajeError } from '../components/Avisos.jsx'
import PantallaAcceso from '../components/PantallaAcceso.jsx'
import { useAuth } from '../context/auth.js'
import { USA_MOCK } from '../services/api.js'

export default function Login() {
  const { usuario, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [datos, setDatos] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  if (usuario) return <Navigate to="/" replace />

  async function enviar(e) {
    e.preventDefault()
    setError('')
    setEnviando(true)
    try {
      await login(datos)
      const desde = location.state?.desde
      navigate(desde ? `${desde.pathname}${desde.search ?? ''}` : '/', { replace: true })
    } catch (err) {
      setError(err.message)
      setEnviando(false)
    }
  }

  const cambiar = (e) => setDatos({ ...datos, [e.target.name]: e.target.value })

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
      <p className="mt-6 text-center text-sm text-texto-suave">
        ¿No tienes cuenta?{' '}
        <Link to="/registro" className="font-semibold text-primario hover:underline">
          Regístrate
        </Link>
      </p>
    </PantallaAcceso>
  )
}
