import { Image } from 'expo-image';

/** Logotipo de Kompás App (assets/images/logo-kompas.png, fondo transparente). */
export default function Logo({ tamano = 40 }: { tamano?: number }) {
  return (
    <Image
      source={require('@/assets/images/logo-kompas.png')}
      style={{ width: tamano, height: tamano }}
      contentFit="contain"
      accessibilityLabel="Logotipo de Kompás App"
    />
  );
}
