import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Cargando } from '../compartido/componentes/Avisos.jsx'
import { Login, Registro } from '../modulos/cuenta'
import { Inicio } from '../modulos/inicio'
import { Itinerarios } from '../modulos/itinerarios'
import { Reportar } from '../modulos/reportes'
import { BuscarDestino, ResultadosRuta } from '../modulos/rutas'
import Layout from './Layout.jsx'
import RutaAdmin from './RutaAdmin.jsx'
import RutaPrivada from './RutaPrivada.jsx'

// El dashboard (con Recharts) se descarga solo cuando un admin lo abre
const Dashboard = lazy(() => import('../modulos/dashboard').then((m) => ({ default: m.Dashboard })))

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/registro" element={<Registro />} />
      <Route
        element={
          <RutaPrivada>
            <Layout />
          </RutaPrivada>
        }
      >
        <Route index element={<Inicio />} />
        <Route path="buscar" element={<BuscarDestino />} />
        <Route path="resultados" element={<ResultadosRuta />} />
        <Route path="itinerarios" element={<Itinerarios />} />
        <Route path="reportar" element={<Reportar />} />
        <Route
          path="dashboard"
          element={
            <RutaAdmin>
              <Suspense fallback={<Cargando texto="Cargando dashboard…" />}>
                <Dashboard />
              </Suspense>
            </RutaAdmin>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
