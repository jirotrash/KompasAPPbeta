import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import { useAuth } from './context/auth.js'
import BuscarDestino from './pages/BuscarDestino.jsx'
import Inicio from './pages/Inicio.jsx'
import Itinerarios from './pages/Itinerarios.jsx'
import Login from './pages/Login.jsx'
import Registro from './pages/Registro.jsx'
import Reportar from './pages/Reportar.jsx'
import ResultadosRuta from './pages/ResultadosRuta.jsx'

function RutaPrivada({ children }) {
  const { usuario } = useAuth()
  const location = useLocation()
  if (!usuario) return <Navigate to="/login" replace state={{ desde: location }} />
  return children
}

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
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
