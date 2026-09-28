import { Link, useNavigate } from 'react-router-dom'
import BuscadorLugar from '../components/BuscadorLugar.jsx'
import { IconoItinerario, IconoReporte, IconoRuta } from '../components/Iconos.jsx'
import Pagina from '../components/Pagina.jsx'
import { ZONA } from '../config/zona.js'
import { useAuth } from '../context/auth.js'
import useLugares from '../hooks/useLugares.js'

const ACCESOS = [
  {
    a: '/buscar',
    titulo: '¿Cómo llego?',
    texto: 'Compara ir a pie, en autobús, taxi o app: línea, dónde subir, dónde bajar y tiempos estimados.',
    Icono: IconoRuta,
  },
  {
    a: '/itinerarios',
    titulo: 'Armar una salida',
    texto: 'Hasta 3 itinerarios para cita, amigos, familia o lo cotidiano, según tu tiempo, presupuesto y gustos.',
    Icono: IconoItinerario,
  },
  {
    a: '/reportar',
    titulo: 'Reportar',
    texto: 'Avisa de afluencia, accidentes, manifestaciones o cierres para ayudar a otros usuarios.',
    Icono: IconoReporte,
  },
]

export default function Inicio() {
  const { usuario } = useAuth()
  const navigate = useNavigate()
  const lugares = useLugares()

  return (
    <Pagina
      titulo={`Hola, ${usuario?.nombre ?? 'viajero'}`}
      descripcion={`¿A dónde vas hoy? Cobertura: ${ZONA.nombre}.`}
      ancho="max-w-5xl"
    >
      <div className="mb-6 max-w-2xl">
        <BuscadorLugar
          etiqueta="Buscar destino"
          ocultarEtiqueta
          grande
          placeholder="¿A dónde quieres ir?"
          valor={null}
          onElegir={(destino) => destino && navigate('/buscar', { state: { destino } })}
          lugares={lugares}
          incluirMiUbicacion={false}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {ACCESOS.map(({ a, titulo, texto, Icono }) => (
          <Link
            key={a}
            to={a}
            className="tarjeta group flex flex-col gap-3 transition hover:border-primario hover:shadow-md"
          >
            <span className="grid size-12 place-items-center rounded-xl bg-primario-claro text-primario-oscuro transition group-hover:bg-primario group-hover:text-sobre-primario">
              <Icono />
            </span>
            <span className="text-lg font-semibold">{titulo}</span>
            <span className="text-sm text-texto-suave">{texto}</span>
          </Link>
        ))}
      </div>

      <section className="tarjeta mt-6 space-y-2 text-sm text-texto-suave">
        <h2 className="font-semibold text-texto">Antes de empezar</h2>
        <ul className="list-disc space-y-1 pl-5">
          <li>Los tiempos son estimaciones; siempre indicamos la fuente y la fecha de cada dato.</li>
          <li>Si no hay información verificada de una ruta, te lo decimos en lugar de inventarla.</li>
          <li>La contratación y el cobro del transporte los hace cada proveedor.</li>
        </ul>
      </section>
    </Pagina>
  )
}
