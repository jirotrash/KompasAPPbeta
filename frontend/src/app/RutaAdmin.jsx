import Logo from '../compartido/componentes/Logo.jsx'
import { useAuth } from '../modulos/cuenta'

/** Solo para rol admin. Una sesión de otro rol ve un aviso y puede cerrar sesión; la API también responde 403. */
export default function RutaAdmin({ children }) {
  const { usuario, logout } = useAuth()
  if (usuario?.rol === 'admin') return children
  return (
    <div className="grid min-h-dvh place-items-center px-4">
      <div className="tarjeta w-full max-w-sm space-y-4 text-center">
        <Logo className="mx-auto size-12" />
        <h1 className="text-xl font-bold">Sin acceso al panel</h1>
        <p className="text-sm text-texto-suave">
          La cuenta {usuario?.email} no es de administrador. El panel de Kompás solo lo pueden abrir administradores.
        </p>
        <button type="button" onClick={logout} className="boton-primario w-full">
          Cerrar sesión
        </button>
      </div>
    </div>
  )
}
