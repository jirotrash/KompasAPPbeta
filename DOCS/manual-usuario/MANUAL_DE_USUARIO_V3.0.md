# Manual de Usuario - Kompás App Móvil
## Versión 3.0 (Edición Noviembre 2026)

> **Fecha de Actualización:** 18 de noviembre de 2026  
> **Plataforma:** Android (instalador APK; requiere el servidor de Kompás encendido)  
> **Versión de la App:** v0.7.0 / Manual v3.0  
> **Versión Previa:** v2.0 (27 de octubre de 2026)  

---

## Antes de empezar: Descargar e instalar la app (Android)

### Descarga
Descarga el instalador desde este enlace (siempre apunta a la versión más reciente):

**https://github.com/jirotrash/KompasAPPbeta/releases/latest/download/kompas.apk**

### Instalación
1. Abre el archivo `kompas.apk` descargado desde las notificaciones o desde la carpeta **Descargas**.
2. Si Android muestra *"Por tu seguridad, tu teléfono no puede instalar apps desconocidas"*, toca **Configuración** y activa **Permitir de esta fuente** para el navegador o el administrador de archivos que usaste.
3. Toca **Instalar**. Si aparece un aviso de Play Protect, elige **Instalar de todas formas** (la app no viene de la Play Store, por eso aparece el aviso).
4. Abre **Kompás App** y acepta el permiso de ubicación.

### Requisito: el servidor de Kompás debe estar encendido
La app no guarda los datos en el teléfono: lugares, planes, recomendaciones y tu cuenta viven en el servidor de Kompás (una PC del equipo). Por eso:

- La app **funciona solo mientras el servidor está encendido**.
- El celular debe estar conectado a la **misma red WiFi** que la PC del servidor.
- Si el servidor está apagado, la app muestra el mensaje **"No hay conexión con el servidor"**. No es una falla del teléfono: espera a que el servidor se encienda y vuelve a intentarlo.

### Conectar la app con el servidor
1. En la PC del servidor, ejecuta `iniciar_backend.bat` desde la carpeta raíz del proyecto. La ventana muestra la dirección, por ejemplo `http://192.168.1.50:8000`. Deja la ventana abierta.
2. En el celular, en la pantalla **Iniciar sesión**, escribe esa IP en el campo **Dirección del servidor** (basta con `192.168.1.50`; la app agrega `http://` y el puerto `:8000`).
3. Escribe tu correo y contraseña y toca **Iniciar sesión**, o toca **Regístrate** para crear una cuenta. La app comprueba primero que el servidor responda.

La app recuerda la última dirección que funcionó. **Si la PC se conecta a otra WiFi, su IP cambia:** cierra sesión en **Perfil**, escribe la IP nueva en **Dirección del servidor** y vuelve a entrar.

> **Si no conecta aunque el servidor esté encendido:** revisa que el celular y la PC estén en la misma WiFi y que el Firewall de Windows permita a Python en redes privadas (puerto 8000). Algunas redes públicas o escolares bloquean la comunicación entre dispositivos; en ese caso usa el punto de acceso (hotspot) de un celular para ambos.

> **iPhone:** por ahora no hay instalador para iOS.

---

## 1. Novedades y Evolución: ¿Qué Cambió desde el 27 de Octubre?

Desde la versión 2.0 (lanzada el 27 de octubre de 2026), Kompás transformó radicalmente su experiencia de usuario, sustituyendo componentes pesados y lentos por **modelos de Inteligencia Artificial y Machine Learning nativos y ultrarrápidos**:

```text
+---------------------------------------------------------------------------------------------------+
|                           EVOLUCIÓN CLAVE DE KOMPÁS (v2.0 ──► v3.0)                               |
+---------------------------------------------------------------------------------------------------+
|  CARACTERÍSTICA          | VERSIÓN 2.0 (27 OCTUBRE 2026)      | VERSIÓN 3.0 (18 NOVIEMBRE 2026)   |
|--------------------------+------------------------------------+-----------------------------------|
| Pestaña "Asistente"      | Chat de texto con Ollama (LLM).    | ASISTENTE AUTÓNOMO DE HÁBITOS     |
|                          | Lento (~4 seg), requería servidor. | (Machine Learning KNN instantáneo)|
|--------------------------+------------------------------------+-----------------------------------|
| Predicción de Destinos   | No existía en la pantalla inicial. | Tarjeta inteligente en Inicio:    |
|                          |                                    | "A esta hora sueles ir a..."      |
|--------------------------+------------------------------------+-----------------------------------|
| Clima y Consejos         | No integrado con IA.               | Widget en vivo + consejos de IA   |
|                          |                                    | (lluvia, calor, frío y paraguas). |
|--------------------------+------------------------------------+-----------------------------------|
| Recomendación de Modo    | Rutas estándar por distancia.      | MOTOR MULTIMODELO (P14):          |
|                          |                                    | Clasifica tu Perfil de Viajero y  |
|                          |                                    | sugiere el modo óptimo.           |
|--------------------------+------------------------------------+-----------------------------------|
| Monitoreo en Trayecto    | Estimación estática de tiempo.     | DEEP LEARNING CNN 1D:             |
|                          |                                    | Detección de cuellos de botella   |
|                          |                                    | y ETA continuo recalculado en min.|
|--------------------------+------------------------------------+-----------------------------------|
| Respaldo de Historial    | Almacenamiento local temporal.     | Triple colección en MongoDB Atlas |
|                          |                                    | con sincronización en la nube.    |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Pantalla de Inicio ("Home"): Tu Centro de Movilidad Inteligente

Al abrir Kompás v3.0, la app detecta tu ubicación y la hora exacta de tu dispositivo para prepararte el viaje antes de que escribas una sola palabra.

```text
┌────────────────────────────────────────────────────────┐
│  KOMPÁS                     [Clima: 14°C Nublado ☁️]   │
│  Hola, Carlos                                          │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 💡 A esta hora sueles ir a:                      │  │
│  │    UTVT - Universidad Tecnológica               │  │
│  │    Ruta habitual: Centro ➔ Lerma (35 min)        │  │
│  │    [ Iniciar viaje ]      [ Ver alternativas ]   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  🌧️ Consejo del día:                                   │
│  "Lleva paraguas o impermeable. Alta probabilidad      │
│   de lluvia en la tarde."                              │
│                                                        │
│  ¿A dónde vas hoy? [ Buscar destino...            🔍 ] │
│                                                        │
│  Accesos rápidos:                                      │
│  [ ☕ Cafeterías ]  [ 🍔 Comer ]  [ 🏛️ Trámites ]      │
└────────────────────────────────────────────────────────┘
```

### Elementos Principales:
1. **Tarjeta de Predicción de Destino:**  
   Si sueles tomar la misma ruta los martes a las 7:00 AM, Kompás te sugiere directamente tu destino frecuente con un solo toque.
2. **Widget del Clima en Tiempo Real:**  
   Conectado al observatorio meteorológico local sin inventar datos. Te muestra temperatura y alertas de lluvia.
3. **Consejo Climático Inteligente:**  
   - Si llueve: *"Lleva paraguas o impermeable"*.
   - Si la temperatura supera 26°C: *"Usa bloqueador solar"*.
   - Si la temperatura baja de 15°C: *"Lleva suéter o chamarra"*.
4. **Buscador Universal:**  
   Permite ingresar cualquier dirección, negocio, escuela o parada de autobús de la zona metropolitana.

---

## 3. El Nuevo "Asistente Inteligente" (Machine Learning Autónomo)

En versiones anteriores, el asistente era un chat que a menudo fallaba si la computadora del servidor estaba apagada. En la versión 3.0, el Asistente se convirtió en un **módulo inteligente autónomo que aprende de tus propios recorridos**.

### ¿Cómo Aprende la App? (En 3 Fases Automáticas)
No necesitas configurar nada; Kompás aprende solo a medida que viajas:

* **Fase 1: Aprendiendo tus hábitos (0 a 4 viajes)**  
  La app te informa que está reuniendo tus primeros recorridos.
* **Fase 2: Frecuencia por Franja Horaria (5 a 19 viajes)**  
  La app clasifica tus viajes por mañana (06:00 a 12:00), tarde (12:00 a 19:00) y noche (19:00 a 24:00) y te sugiere la ruta más tomada en esa franja.
* **Fase 3: Inteligencia Predictiva KNN (20 o más viajes)**  
  Se activa el modelo matemático **K-Nearest Neighbors (K-Vecinos más Cercanos)**:
  - Modela las 24 horas del día como un círculo continuo (para que las 23:55 hrs estén junto a las 00:05 hrs).
  - Compara la hora actual con tus 7 viajes históricos más similares.
  - Muestra tu nivel de certidumbre en pantalla: *"Exactitud del modelo: 96% vs opción simple: 39%"*.

### Pantalla "Mis Hábitos":
Dentro del Asistente puedes consultar tu radiografía de movilidad:
- **Tus rutas más tomadas:** Conteo exacto de cuántas veces has subido a cada línea.
- **Distribución de transporte:** Porcentaje de uso de autobús vs caminar vs auto.
- **Reparto por día:** Qué días te trasladas más y tus horarios pico personales.

---

## 4. Búsqueda de Rutas y Recomendador Multimodal (P14)

Cuando buscas un destino, Kompás no solo te da la ruta más corta, sino que evalúa **qué medio de transporte te conviene más en ese momento exacto**.

```text
┌────────────────────────────────────────────────────────┐
│  OPCIONES DE TRASLADO                       [ Filtrar ]│
│                                                        │
│  ⭐ RECOMENDACIÓN INTELIGENTE (IA):                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 🚌 Autobús Línea 2 + Caminata                    │  │
│  │    Tiempo: 38 min  ·  Costo: $12.00 MXN          │  │
│  │    Perfil asignado: "Viajero Económico"          │  │
│  │                                                  │  │
│  │ 💡 Consejo de movilidad:                         │  │
│  │ "Hora pico detectada: Se sugiere abordar en      │  │
│  │  parada Pino Suárez para evitar transbordo."    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  OTRAS ALTERNATIVAS:                                   │
│  🚶 Caminando: 1 hr 15 min · $0.00 MXN                 │
│  🚗 Auto por aplicación: 24 min · $75.00 MXN           │
│     (Alerta: Tarifa dinámica por lluvia)               │
└────────────────────────────────────────────────────────┘
```

### Tu Perfil de Viajero (K-Means):
El recomendador identifica a cuál de los 4 arquetipos de movilidad perteneces:
1. **Viajero Económico / Rutinario:** Prioriza rutas de bajo costo y tarifas integradas.
2. **Viajero Exprés / Ejecutivo:** Prioriza el menor tiempo de traslado y menor caminata.
3. **Viajero Interurbano / Larga Distancia:** Viajes extensos que conectan municipios.
4. **Viajero Multimodal / Flexible:** Combina bicicleta, caminata y transporte masivo.

---

## 5. El Mapa Interactivo: Lectura de Colores y Marcadores

En la versión 3.0, el mapa de Kompás utiliza una simbología visual estandarizada para que nunca te equivoques de parada:

| Marcador / Línea | Color | Significado |
| :--- | :--- | :--- |
| **Marcador Verde ↑** | Verde Esmeralda | **Punto de Abordaje:** Exactamente dónde debes esperar y subir a la unidad. |
| **Marcador Dorado ↓** | Amarillo Dorado | **Punto de Descenso:** Dónde debes solicitar la bajada del autobús. |
| **Marcador Rojo ⇄** | Rojo Coral | **Punto de Transbordo:** Cruce donde caminas de una ruta a otra. |
| **Línea Sólida Gruesa** | Azul Eléctrico | **Tramo en Transporte:** La trayectoria que harás a bordo del autobús o tren. |
| **Línea Punteada** | Gris / Azul Tenue | **Tramo a Pie:** Caminata hacia la parada o desde la bajada a tu destino. |
| **Puntos Intermedios** | Círculos Blancos | **Paradas intermedias:** Para que cuentes cuántas estaciones te faltan. |

---

## 6. Monitoreo en Vivo y Detección de Congestión (Deep Learning CNN 1D)

Cuando tocas el botón **"Iniciar Viaje"**, la app entra en modo navegación activa:

1. **Alerta Temprana de Cuellos de Botella (P24):**  
   Una Red Neuronal Convolucional 1D analiza la velocidad de las últimas paradas. Si detecta que el tráfico colapsó más adelante, la app te muestra un aviso preventivo:  
   > ⚠️ *"Tráfico pesado detectado en los próximos 2 km. Retraso estimado: +12 minutos."*
2. **ETA Continuo de Llegada (P27):**  
   El tiempo restante de viaje ya no es fijo; se recalcula en segundos adaptándose a las condiciones reales del trayecto.

---

## 7. Armar Salidas y Rutas con Múltiples Paradas ("Mis Planes")

Si quieres salir con amigos o visitar varios lugares en una sola tarde (por ejemplo: Banco $\to$ Comer $\to$ Café):

1. Ve a la pestaña **Planificar**.
2. Selecciona tu presupuesto máximo, tiempo disponible y tus intereses.
3. **Optimización con Algoritmo Genético:**  
   Kompás calcula el orden matemático más corto para visitar todos los puntos sin dar vueltas innecesarias en la ciudad.
4. **Filtro de Sistema Experto:**  
   Verifica que los lugares elegidos estén abiertos a la hora estimada de llegada y respeten tu presupuesto.
5. Guarda el plan en **"Mis Planes"** para abrirlo cuando salgas.

---

## 8. Preguntas Frecuentes (FAQ)

### ¿Por qué ya no puedo chatear con el asistente?
Porque el chat anterior dependía de un programa externo (Ollama) que tardaba mucho y fallaba con frecuencia. Ahora el asistente es un motor de aprendizaje automático local: responde al instante, no gasta tus datos móviles y predice con precisión a dónde vas sin que tengas que escribir.

### ¿Kompás comparte mi ubicación con otras personas?
**No.** Tu historial de viajes se utiliza exclusivamente para que tu modelo de hábitos personal aprenda tus horarios. Los datos se guardan de forma encriptada y anónima en MongoDB Atlas.

### ¿Qué pasa si tomo una ruta nueva por primera vez?
La app te sugerirá la ruta óptima mediante el **Recomendador Multimodal (Random Forest)** y guardará ese nuevo recorrido. Cuando lo repitas un par de veces, se integrará automáticamente a tus hábitos habituales.

### ¿La app funciona sin conexión a internet?
**No.** Kompás necesita internet y que el servidor de Kompás esté encendido: tu cuenta, tus planes guardados, las recomendaciones y el mapa se cargan desde internet. Sin conexión, o con el servidor apagado, la app muestra el mensaje *"No hay conexión con el servidor"*. Revisa tu internet y vuelve a intentarlo más tarde.

### Olvidé mi contraseña, ¿cómo la recupero?
1. En **Iniciar sesión**, toca **¿Olvidaste tu contraseña?**
2. Escribe el correo de tu cuenta y toca **Enviar código**.
3. Revisa tu correo (también la carpeta de spam) y escribe el **código de 6 dígitos**. Vence en 15 minutos y tienes 5 intentos.
4. Escribe tu contraseña nueva dos veces y toca **Cambiar contraseña**. La app entra a tu cuenta.

Si no te llega el código, toca **Enviar otro código** (puedes pedir uno nuevo cada minuto).

### La app dice "No hay conexión con el servidor", ¿qué hago?
1. Revisa que tengas internet (abre cualquier página web).
2. Revisa que estés en la misma WiFi que la PC del servidor.
3. Si la PC cambió de red, su IP también cambió: cierra sesión y escribe la IP nueva en **Dirección del servidor**.
4. Si todo lo anterior está bien, el servidor está apagado. Avisa al equipo de Kompás o intenta más tarde.
