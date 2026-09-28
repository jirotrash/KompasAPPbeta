import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { MensajeError } from '../components/Avisos.jsx'
import PantallaAcceso from '../components/PantallaAcceso.jsx'
import { useAuth } from '../context/auth.js'

const CAMPOS = [
  { name: 'nombre', etiqueta: 'Nombre', type: 'text', autoComplete: 'name' },
  { name: 'email', etiqueta: 'Correo electrónico', type: 'email', autoComplete: 'email' },
  { name: 'password', etiqueta: 'Contraseña', type: 'password', autoComplete: 'new-password' },
  { name: 'confirmar', etiqueta: 'Confirmar contraseña', type: 'password', autoComplete: 'new-password' },
]

export default function Registro() {
  const { usuario, registrar } = useAuth()
  const navigate = useNavigate()
  const [datos, setDatos] = useState({ nombre: '', email: '', password: '', confirmar: '' })
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  if (usuario) return <Navigate to="/" replace />

  async function enviar(e) {
    e.preventDefault()
    if (!datos.nombre.trim() || !datos.email.trim()) return setError('Escribe tu nombre y tu correo.')
    if (datos.password.length < 6) return setError('La contraseña necesita al menos 6 caracteres.')
    if (datos.password !== datos.confirmar) return setError('Las contraseñas no coinciden.')
    setError('')
    setEnviando(true)
    try {
      await registrar({ nombre: datos.nombre.trim(), email: datos.email.trim(), password: datos.password })
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.message)
      setEnviando(false)
    }
  }

  const cambiar = (e) => setDatos({ ...datos, [e.target.name]: e.target.value })

  return (
    <PantallaAcceso titulo="Crea tu cuenta">
      <form onSubmit={enviar} className="space-y-4" noValidate>
        {CAMPOS.map(({ name, etiqueta, ...resto }) => (
          <div key={name}>
            <label htmlFor={name} className="etiqueta">
              {etiqueta}
            </label>
            <input id={name} name={name} required className="campo" value={datos[name]} onChange={cambiar} {...resto} />
          </div>
        ))}
        <MensajeError>{error}</MensajeError>
        <button type="submit" className="boton-primario w-full" disabled={enviando}>
          {enviando ? 'Creando cuenta…' : 'Crear cuenta'}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-texto-suave">
        ¿Ya tienes cuenta?{' '}
        <Link to="/login" className="font-semibold text-primario hover:underline">
          Inicia sesión
        </Link>
      </p>
    </PantallaAcceso>
  )
}
