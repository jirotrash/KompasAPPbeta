import { forwardRef, useState } from 'react';
import { TextInput, type TextInputProps } from 'react-native';
import { XStack, YStack } from 'tamagui';

import { useTema } from '@/context/Tema';

import Icono from './Icono';
import { Texto } from './ui';

type Props = TextInputProps & {
  etiqueta: string;
  /** Campo de contraseña con botón de ojo para mostrarla u ocultarla. */
  contrasena?: boolean;
};

/** Campo de texto con etiqueta arriba (como en los mockups de login y registro). */
const CampoTexto = forwardRef<TextInput, Props>(function CampoTexto({ etiqueta, contrasena, style, ...props }, ref) {
  const { paleta } = useTema();
  const [enfocado, setEnfocado] = useState(false);
  const [visible, setVisible] = useState(false);

  return (
    <YStack gap={8}>
      <Texto tam="sm" peso="semi">
        {etiqueta}
      </Texto>
      <XStack
        items="center"
        minH={52}
        rounded={12}
        borderWidth={1}
        borderColor={enfocado ? '$primario' : '$borde'}
        bg="$tarjeta"
        px={14}
        gap={8}
      >
        <TextInput
          ref={ref}
          aria-label={etiqueta}
          placeholderTextColor={paleta.textoSuave}
          secureTextEntry={contrasena && !visible}
          autoCapitalize={contrasena ? 'none' : props.autoCapitalize}
          // En web se quita el contorno del navegador: el borde verde del contenedor ya marca el foco
          style={[{ flex: 1, minHeight: 50, fontSize: 15, color: paleta.texto, outlineStyle: 'none' } as object, style]}
          {...props}
          onFocus={(e) => {
            setEnfocado(true);
            props.onFocus?.(e);
          }}
          onBlur={(e) => {
            setEnfocado(false);
            props.onBlur?.(e);
          }}
        />
        {contrasena && (
          <XStack
            role="button"
            aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
            onPress={() => setVisible((v) => !v)}
            p={4}
            cursor="pointer"
            pressStyle={{ opacity: 0.6 }}
          >
            <Icono nombre={visible ? 'ojo' : 'ojoTachado'} color={paleta.textoSuave} tamano={20} />
          </XStack>
        )}
      </XStack>
    </YStack>
  );
});

export default CampoTexto;
