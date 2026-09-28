import { SymbolView, type SymbolViewProps } from 'expo-symbols';
import type { ColorValue } from 'react-native';

// Catálogo de íconos de la app: SF Symbols en iPhone y Material Symbols en Android y web.
// Valentín puede cambiar aquí cualquier ícono sin tocar las pantallas.
const ICONOS = {
  inicio: { ios: 'house.fill', android: 'home', web: 'home' },
  planificar: { ios: 'slider.horizontal.3', android: 'tune', web: 'tune' },
  mapa: { ios: 'map.fill', android: 'map', web: 'map' },
  perfil: { ios: 'person.crop.circle', android: 'account_circle', web: 'account_circle' },
  buscar: { ios: 'magnifyingglass', android: 'search', web: 'search' },
  filtros: { ios: 'slider.horizontal.3', android: 'tune', web: 'tune' },
  ubicacion: { ios: 'mappin.and.ellipse', android: 'location_on', web: 'location_on' },
  miUbicacion: { ios: 'location.fill', android: 'my_location', web: 'my_location' },
  brujula: { ios: 'safari.fill', android: 'explore', web: 'explore' },
  estrella: { ios: 'star.fill', android: 'star', web: 'star' },
  regla: { ios: 'ruler', android: 'straighten', web: 'straighten' },
  reloj: { ios: 'clock', android: 'schedule', web: 'schedule' },
  dinero: { ios: 'banknote', android: 'payments', web: 'payments' },
  bandera: { ios: 'flag', android: 'flag', web: 'flag' },
  pie: { ios: 'figure.walk', android: 'directions_walk', web: 'directions_walk' },
  autobus: { ios: 'bus.fill', android: 'directions_bus', web: 'directions_bus' },
  taxi: { ios: 'car.fill', android: 'local_taxi', web: 'local_taxi' },
  combinado: { ios: 'arrow.triangle.swap', android: 'swap_horiz', web: 'swap_horiz' },
  comer: { ios: 'fork.knife', android: 'restaurant', web: 'restaurant' },
  cafe: { ios: 'cup.and.saucer.fill', android: 'local_cafe', web: 'local_cafe' },
  cultura: { ios: 'building.columns.fill', android: 'museum', web: 'museum' },
  entretenimiento: { ios: 'film.fill', android: 'movie', web: 'movie' },
  aireLibre: { ios: 'tree.fill', android: 'park', web: 'park' },
  compras: { ios: 'bag.fill', android: 'shopping_bag', web: 'shopping_bag' },
  atras: { ios: 'chevron.left', android: 'arrow_back', web: 'arrow_back' },
  derecha: { ios: 'chevron.right', android: 'chevron_right', web: 'chevron_right' },
  cerrar: { ios: 'xmark', android: 'close', web: 'close' },
  aviso: { ios: 'exclamationmark.triangle.fill', android: 'warning', web: 'warning' },
  info: { ios: 'info.circle', android: 'info', web: 'info' },
  salir: { ios: 'rectangle.portrait.and.arrow.right', android: 'logout', web: 'logout' },
  sol: { ios: 'sun.max.fill', android: 'light_mode', web: 'light_mode' },
  luna: { ios: 'moon.fill', android: 'dark_mode', web: 'dark_mode' },
  sistema: { ios: 'iphone', android: 'smartphone', web: 'smartphone' },
  check: { ios: 'checkmark', android: 'check', web: 'check' },
  reporte: { ios: 'megaphone.fill', android: 'campaign', web: 'campaign' },
  ruta: { ios: 'point.topleft.down.to.point.bottomright.curvepath', android: 'route', web: 'route' },
  intercambiar: { ios: 'arrow.up.arrow.down', android: 'swap_vert', web: 'swap_vert' },
  ojo: { ios: 'eye', android: 'visibility', web: 'visibility' },
  ojoTachado: { ios: 'eye.slash', android: 'visibility_off', web: 'visibility_off' },
  apple: { ios: 'apple.logo', android: 'phone_iphone', web: 'phone_iphone' },
  documento: { ios: 'doc.text', android: 'description', web: 'description' },
} as const satisfies Record<string, SymbolViewProps['name']>;

export type NombreIcono = keyof typeof ICONOS;

type Props = { nombre: NombreIcono; color: ColorValue; tamano?: number };

export default function Icono({ nombre, color, tamano = 22 }: Props) {
  return <SymbolView name={ICONOS[nombre]} tintColor={color} size={tamano} />;
}
