import { YStack } from 'tamagui';

import Pantalla from '@/components/Pantalla';
import { Subtitulo, Tarjeta, Texto, Titulo } from '@/components/ui';

// Condiciones de uso basadas en las delimitaciones del proyecto autorizado (CONTEXTO.md §2).
// Versión provisional del prototipo: el equipo define el texto final.
const PUNTOS = [
  {
    titulo: 'La app orienta, no presta el servicio',
    texto:
      'Kompás App te ayuda a decidir cómo moverte. Contratar, cobrar y prestar el transporte le corresponde a cada proveedor.',
  },
  {
    titulo: 'Los tiempos son estimaciones',
    texto:
      'Los tiempos de caminata, espera y trayecto son aproximados. Siempre indicamos la fuente del dato y si el horario es programado o actualizado por un proveedor.',
  },
  {
    titulo: 'No inventamos rutas',
    texto:
      'Solo mostramos rutas de transporte documentadas y probadas. Si no hay información verificada, la app te lo dice.',
  },
  {
    titulo: 'Afluencia y reseñas',
    texto:
      'La afluencia de un lugar viene de reportes de la comunidad; no es un conteo de personas en vivo ni incluye todas las reseñas del lugar.',
  },
  {
    titulo: 'Tarifas de apps de transporte',
    texto: 'Solo mostramos tarifas de apps como Uber o DiDi si existe una integración autorizada; si no, consúltalas en su app.',
  },
  {
    titulo: 'Los reportes no son un servicio de emergencias',
    texto: 'Si hay personas heridas o en peligro, llama al 911.',
  },
  {
    titulo: 'Tus datos',
    texto:
      'Usamos tu nombre y correo para tu cuenta. Tu ubicación se usa para sugerirte rutas y lugares cercanos: se envía al servidor cuando ves lugares cercanos, buscas una ruta, creas un plan o envías un reporte. Para buscar direcciones y dibujar rutas por calles se consultan servicios de OpenStreetMap (Photon y OSRM), que reciben el texto buscado o las coordenadas.',
  },
];

export default function Terminos() {
  return (
    <Pantalla bordes={['left', 'right', 'bottom']}>
      <YStack gap={8} mb={20}>
        <Titulo>Términos y condiciones</Titulo>
        <Subtitulo>Kompás App es un prototipo escolar (UTVT · ITIID-D71). Este texto es provisional.</Subtitulo>
      </YStack>
      <YStack gap={12}>
        {PUNTOS.map((p) => (
          <Tarjeta key={p.titulo} gap={6}>
            <Texto peso="fuerte">{p.titulo}</Texto>
            <Texto tam="sm" suave>
              {p.texto}
            </Texto>
          </Tarjeta>
        ))}
      </YStack>
    </Pantalla>
  );
}
