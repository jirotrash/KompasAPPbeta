import { Navigate, Route, Routes } from 'react-router-dom'
import { Administracion } from '../modulos/administracion'
import { Login } from '../modulos/cuenta'
import { Dashboard } from '../modulos/dashboard'
import Layout from './Layout.tsx'
import RutaAdmin from './RutaAdmin.tsx'
import RutaPrivada from './RutaPrivada.tsx'

// La web es solo el panel de administración: login, dashboard y administración (altas, cambios y bajas).
// Las funciones para usuarios viven en la app móvil.
export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <RutaPrivada>
            <RutaAdmin>
              <Layout />
            </RutaAdmin>
          </RutaPrivada>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="administrar" element={<Administracion />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
