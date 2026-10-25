// Logotipo oficial de Kompás (public/logo-kompas.png). Va sobre un contenedor claro para que no se corte
// el contraste en modo oscuro (COLORIMETRIA.md §5).
export default function Logo({ className = 'size-9', alt = '' }) {
  return (
    <span className={`relative inline-block shrink-0 rounded-xl bg-white shadow-sm ring-1 ring-black/5 ${className}`}>
      <img src="/logo-kompas.png" alt={alt} className="absolute inset-[12%] size-[76%] object-contain" />
    </span>
  )
}
