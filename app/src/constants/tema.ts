// Se definio la paleta de colores para Kompas App basada en el logotipo oficial.
// Se establecieron esquemas para modo claro y modo oscuro para la integracion con Tamagui y el contexto de la app.

export const PALETAS = {
  claro: {
    // Se agrego el color azul Kompas del logotipo para botones principales, enlaces y encabezados
    primario: '#1A62A5',
    // Se agrego variante oscura para el estado presionado del boton primario
    primarioPresionado: '#134B80',
    // Se agrego color blanco para texto e iconos sobre fondo primario garantizando contraste WCAG AA
    sobrePrimario: '#FFFFFF',
    // Se agrego el color rojo autobus del logotipo para botones de accion clave y alertas destacadas
    acento: '#D7000C',
    // Se agrego variante oscura para el estado presionado del color de acento
    acentoPresionado: '#B0000A',
    // Se agrego color blanco para elementos sobre fondo de acento
    sobreAcento: '#FFFFFF',
    // Se agrego color coral del logotipo para figuras e iconos secundarios
    coral: '#F5364A',
    // Se agrego tinte azul tenue para fondos de chips y estados de seleccion suave
    suave: '#E8F0F8',
    // Se agrego gris muy claro para el fondo base de la aplicacion
    fondo: '#F7F8FA',
    // Se agrego blanco puro para la superficie de tarjetas y modales
    tarjeta: '#FFFFFF',
    // Se agrego blanco puro para superficies elevadas
    superficieElevada: '#FFFFFF',
    // Se agrego gris neutro para la delimitacion de bordes
    borde: '#E2E6EC',
    // Se agrego gris oscuro casi negro para texto principal de alto contraste
    texto: '#1B1F27',
    // Se agrego gris medio para texto secundario y marcadores de posicion en inputs
    textoSuave: '#5B6472',
    // Se agrego color oscuro para los marcadores en el mapa
    marcador: '#1B1F27',
    // Se agrego el color azul de marca para el trazado de rutas
    ruta: '#1A62A5',
    // Se agrego el color dorado del logotipo para valoraciones y estrellas
    estrella: '#DFAB36',
    // Se agrego el color verde del logotipo para confirmaciones y estados correctos
    ok: '#198754',
    // Se agrego fondo verde tenue para cajas de mensaje de exito
    okFondo: '#EAF7EE',
    // Se agrego color dorado para advertencias y avisos
    aviso: '#DFAB36',
    // Se agrego fondo ambar suave para cajas de aviso
    avisoFondo: '#FDF6E7',
    // Se agrego color rojo autobus para estados de error y peligro
    peligro: '#D7000C',
    // Se agrego fondo rojo tenue para cajas de mensaje de error
    peligroFondo: '#FEECEB',
    // Se agrego color frambuesa del logotipo para insignias y detalles visuales
    detalle: '#C43D69',
    // Se asigno el verde del logotipo para el modo de transporte caminando
    transporteCaminando: '#198754',
    // Se asigno el azul del logotipo para el modo de transporte publico
    transportePublico: '#1A62A5',
    // Se asigno el dorado del logotipo para el modo de transporte taxi y aplicacion
    transporteTaxi: '#DFAB36',
    // Se asigno el frambuesa del logotipo para el modo de transporte combinado
    transporteCombinado: '#C43D69',
  },
  oscuro: {
    // Se aclaro el azul de marca a #5BA3E6 para mantener contraste y legibilidad sobre fondo oscuro
    primario: '#5BA3E6',
    // Se agrego variante aclarada para estado presionado en modo oscuro
    primarioPresionado: '#7AB8EE',
    // Se asigno texto oscuro sobre fondo primario aclarado para alcanzar contraste optimo
    sobrePrimario: '#0E1420',
    // Se aclaro el rojo a #FF6B6B para fondos oscuros
    acento: '#FF6B6B',
    // Se agrego variante para estado presionado del acento
    acentoPresionado: '#FF8F8F',
    // Se asigno texto oscuro sobre fondo de acento aclarado
    sobreAcento: '#0E1420',
    // Se agrego coral adaptado para modo oscuro
    coral: '#FF6B6B',
    // Se agrego azul oscuro para estados de seleccion y chips
    suave: '#1A283D',
    // Se agrego azul muy oscuro como fondo base para evitar el negro puro y disminuir el cansancio visual
    fondo: '#0E1420',
    // Se agrego superficie azul oscura diferenciada del fondo para tarjetas
    tarjeta: '#172030',
    // Se agrego superficie elevada mas clara para separar modales y paneles inferiores
    superficieElevada: '#1F2A3D',
    // Se agrego borde azul grisaceo para separar planos sin depender de sombras
    borde: '#2B3750',
    // Se agrego blanco azulado para lectura de texto principal
    texto: '#E8ECF3',
    // Se agrego gris azulado claro para texto secundario
    textoSuave: '#A3ADBD',
    // Se agrego color claro para marcadores en el mapa
    marcador: '#E8ECF3',
    // Se agrego trazo azul claro para rutas sobre fondo de mapa oscuro
    ruta: '#5BA3E6',
    // Se agrego dorado claro para estrellas y calificaciones
    estrella: '#F2C14E',
    // Se agrego verde claro para estados de confirmacion
    ok: '#3DBE82',
    // Se agrego fondo verde oscuro para alertas de confirmacion
    okFondo: '#132B1F',
    // Se agrego amarillo dorado para advertencias
    aviso: '#F2C14E',
    // Se agrego fondo ambar oscuro para cajas de advertencia
    avisoFondo: '#2E2510',
    // Se agrego rojo claro para estados de peligro
    peligro: '#FF6B6B',
    // Se agrego fondo vino oscuro para alertas de peligro
    peligroFondo: '#381618',
    // Se agrego frambuesa claro para elementos de detalle
    detalle: '#E56B93',
    // Se asigno verde claro para el transporte caminando en modo oscuro
    transporteCaminando: '#3DBE82',
    // Se asigno azul claro para el transporte publico en modo oscuro
    transportePublico: '#5BA3E6',
    // Se asigno dorado claro para el transporte taxi y app en modo oscuro
    transporteTaxi: '#F2C14E',
    // Se asigno frambuesa claro para el transporte combinado en modo oscuro
    transporteCombinado: '#E56B93',
  },
} as const;

export type Esquema = keyof typeof PALETAS;
export type Paleta = (typeof PALETAS)[Esquema];

/** Ancho máximo del contenido en tablets y web, para que no se estire de más. */
export const ANCHO_MAXIMO = 720;
/** A partir de este ancho la app usa diseño de tablet (columnas, panel lateral en el mapa). */
export const ANCHO_TABLET = 768;
/** A partir de este ancho (tablet horizontal, web) las pestañas pasan a una barra lateral. */
export const ANCHO_BARRA_LATERAL = 1000;
