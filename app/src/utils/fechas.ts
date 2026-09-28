// Fecha de nacimiento: se escribe como DD/MM/AAAA y viaja a la API como AAAA-MM-DD.

/** Pone las diagonales mientras se escribe: "2709199" → "27/09/199". */
export function formatoFechaEscrita(texto: string) {
  const d = texto.replace(/\D/g, '').slice(0, 8);
  if (d.length <= 2) return d;
  if (d.length <= 4) return `${d.slice(0, 2)}/${d.slice(2)}`;
  return `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}`;
}

/** "27/09/1998" → "1998-09-27", o null si no es una fecha que exista (p. ej. 31/02/2000). */
export function fechaISO(ddmmaaaa: string): string | null {
  const partes = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(ddmmaaaa);
  if (!partes) return null;
  const [dia, mes, anio] = partes.slice(1).map(Number);
  const fecha = new Date(anio, mes - 1, dia);
  if (fecha.getFullYear() !== anio || fecha.getMonth() !== mes - 1 || fecha.getDate() !== dia) return null;
  return `${partes[3]}-${partes[2]}-${partes[1]}`;
}

/** Años cumplidos a partir de "AAAA-MM-DD". */
export function edad(iso: string, hoy = new Date()) {
  const [anio, mes, dia] = iso.slice(0, 10).split('-').map(Number);
  const cumplioEsteAnio = hoy.getMonth() + 1 > mes || (hoy.getMonth() + 1 === mes && hoy.getDate() >= dia);
  return hoy.getFullYear() - anio - (cumplioEsteAnio ? 0 : 1);
}
