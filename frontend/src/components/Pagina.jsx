/** Contenedor estándar de pantalla: márgenes responsivos y título. */
export default function Pagina({ titulo, descripcion, children, ancho = 'max-w-3xl' }) {
  return (
    <div className={`mx-auto w-full ${ancho} px-4 py-5 sm:px-6 md:py-8 lg:px-8`}>
      {titulo && (
        <header className="mb-5 md:mb-6">
          <h1 className="text-2xl font-bold tracking-tight md:text-3xl">{titulo}</h1>
          {descripcion && <p className="mt-1 text-texto-suave">{descripcion}</p>}
        </header>
      )}
      {children}
    </div>
  )
}
