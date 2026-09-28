// Íconos en línea (trazo) para no depender de librerías externas.
// Valentín puede sustituirlos por los íconos definitivos de la app.

function Icono({ children, className = 'size-6', ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
      {...props}
    >
      {children}
    </svg>
  )
}

export const IconoInicio = (p) => (
  <Icono {...p}>
    <path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z" />
  </Icono>
)
export const IconoRuta = (p) => (
  <Icono {...p}>
    <circle cx="6" cy="19" r="2" />
    <circle cx="18" cy="5" r="2" />
    <path d="M8 19h8.5a3.5 3.5 0 0 0 0-7h-9a3.5 3.5 0 0 1 0-7H16" />
  </Icono>
)
export const IconoItinerario = (p) => (
  <Icono {...p}>
    <path d="M12 21s-7-6.1-7-11.5a7 7 0 0 1 14 0C19 14.9 12 21 12 21z" />
    <circle cx="12" cy="9.5" r="2.5" />
  </Icono>
)
export const IconoReporte = (p) => (
  <Icono {...p}>
    <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
    <path d="M12 9v4M12 17h.01" />
  </Icono>
)
export const IconoSalir = (p) => (
  <Icono {...p}>
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />
  </Icono>
)
export const IconoUbicacion = (p) => (
  <Icono {...p}>
    <circle cx="12" cy="12" r="3" />
    <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
    <circle cx="12" cy="12" r="7" />
  </Icono>
)
export const IconoPie = (p) => (
  <Icono {...p}>
    <circle cx="13" cy="4" r="2" />
    <path d="m9 20 3-6 3 3v4M7 12l3-4 4 1 3 3M10 8l-1 5" />
  </Icono>
)
export const IconoBus = (p) => (
  <Icono {...p}>
    <rect x="4" y="3" width="16" height="15" rx="2" />
    <path d="M4 11h16M8 21v-3M16 21v-3" />
    <circle cx="8" cy="15" r=".5" />
    <circle cx="16" cy="15" r=".5" />
  </Icono>
)
export const IconoAuto = (p) => (
  <Icono {...p}>
    <path d="M5 17h14v-5l-2-5H7l-2 5z" />
    <path d="M5 12h14" />
    <circle cx="8" cy="17" r="2" />
    <circle cx="16" cy="17" r="2" />
  </Icono>
)
export const IconoCelular = (p) => (
  <Icono {...p}>
    <rect x="6" y="2" width="12" height="20" rx="2" />
    <path d="M11 18h2" />
  </Icono>
)
export const IconoInfo = (p) => (
  <Icono {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 11v5M12 8h.01" />
  </Icono>
)
export const IconoAtras = (p) => (
  <Icono {...p}>
    <path d="m15 18-6-6 6-6" />
  </Icono>
)
export const IconoSol = (p) => (
  <Icono {...p}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
  </Icono>
)
export const IconoLuna = (p) => (
  <Icono {...p}>
    <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
  </Icono>
)
export const IconoMonitor = (p) => (
  <Icono {...p}>
    <rect x="2" y="3" width="20" height="14" rx="2" />
    <path d="M8 21h8M12 17v4" />
  </Icono>
)
export const IconoBuscar = (p) => (
  <Icono {...p}>
    <circle cx="11" cy="11" r="7" />
    <path d="m20 20-3.5-3.5" />
  </Icono>
)
export const IconoCerrar = (p) => (
  <Icono {...p}>
    <path d="M18 6 6 18M6 6l12 12" />
  </Icono>
)
export const IconoIntercambiar = (p) => (
  <Icono {...p}>
    <path d="M7 4v16M7 4 3 8M7 4l4 4M17 20V4M17 20l-4-4M17 20l4-4" />
  </Icono>
)
