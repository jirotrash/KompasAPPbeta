import { XStack, YStack } from 'tamagui';

import { MODOS, TIPOS_PLAN } from '@/constants/catalogos';
import { useTema } from '@/context/Tema';
import type { Plan } from '@/types/dominio';

import ExplicacionReglas from './ExplicacionReglas';
import Icono, { type NombreIcono } from './Icono';
import { Pildora, Recuadro, Tarjeta, Texto } from './ui';

function Dato({ icono, texto, extra }: { icono: NombreIcono; texto: string; extra?: NombreIcono[] }) {
  const { paleta } = useTema();
  return (
    <XStack width="50%" items="center" gap={6} py={4}>
      <Icono nombre={icono} color={paleta.textoSuave} tamano={16} />
      <Texto tam="sm">{texto}</Texto>
      {extra?.map((i) => (
        <Icono key={i} nombre={i} color={paleta.primario} tamano={15} />
      ))}
    </XStack>
  );
}

type Props = { plan: Plan; onPress: () => void };

const pesos = (n: number) => `$${Math.round(n).toLocaleString('es-MX')}`;

/** Costo exacto si lo hay; si no, el rango estimado de Google; si tampoco, "sin dato" (no se inventa). */
function textoCosto(plan: Plan) {
  if (plan.costo != null) return `${pesos(plan.costo)} MXN`;
  const r = plan.rango_costo;
  if (r?.max != null) return r.min != null && r.min !== r.max ? `${pesos(r.min)}–${pesos(r.max)} MXN` : `${pesos(r.max)} MXN`;
  return 'Costo: sin dato';
}

/** Tarjeta de "Tus planes": costo, duración, km, paradas, "Mejor opción" y explicación. */
export default function TarjetaPlan({ plan, onPress }: Props) {
  const modos = [...new Set((plan.tramos ?? []).map((t) => t.modo))].map((m) => MODOS[m].icono);
  const horas = Number.isInteger(plan.duracion_horas) ? plan.duracion_horas : plan.duracion_horas.toFixed(1);

  return (
    <Tarjeta destacada={plan.mejor_opcion} style={{ boxShadow: '0 1px 3px rgba(18,48,71,0.06)' }}>
      {/* Toda la tarjeta abre el mapa, menos la lista de reglas (que se despliega aparte) */}
      <YStack
        gap={12}
        role="button"
        aria-label={`${TIPOS_PLAN[plan.tipo]}. Ver en el mapa`}
        onPress={onPress}
        cursor="pointer"
        pressStyle={{ opacity: 0.75 }}
      >
        <XStack items="center" justify="space-between" gap={8}>
          <Texto flex={1} tam="lg" peso="fuerte">
            {TIPOS_PLAN[plan.tipo]}
          </Texto>
          {plan.mejor_opcion && (
            <Pildora tono="primario">
              <Texto tam="xs" peso="fuerte" color="$sobrePrimario">
                Mejor opción
              </Texto>
            </Pildora>
          )}
        </XStack>

        <XStack flexWrap="wrap">
          <Dato icono="dinero" texto={textoCosto(plan)} />
          <Dato icono="reloj" texto={`${horas} hrs`} />
          <Dato icono="mapa" texto={`${plan.distancia_km.toFixed(1)} km`} />
          <Dato
            icono="bandera"
            texto={`${plan.paradas.length} ${plan.paradas.length === 1 ? 'parada' : 'paradas'}`}
            extra={modos}
          />
        </XStack>

        <Recuadro>
          <Texto tam="sm" suave>
            {plan.explicacion}
          </Texto>
          <Texto tam="xs" suave>
            Paradas: {plan.paradas.map((p) => p.nombre).join(' → ')}
          </Texto>
        </Recuadro>
      </YStack>

      <ExplicacionReglas reglas={plan.reglas_cumplidas} titulo="Reglas que se cumplieron" />
    </Tarjeta>
  );
}
