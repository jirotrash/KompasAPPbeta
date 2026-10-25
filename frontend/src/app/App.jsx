import { Navigate, Route, Routes } from 'react-router-dom'
import { Login } from '../modulos/cuenta'
import { Dashboard } from '../modulos/dashboard'
import Layout from './Layout.jsx'
import RutaAdmin from './RutaAdmin.jsx'
import RutaPrivada from './RutaPrivada.jsx'

// La web es solo el panel de administración: login y dashboard. Las funciones para usuarios viven en la app móvil.
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
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
