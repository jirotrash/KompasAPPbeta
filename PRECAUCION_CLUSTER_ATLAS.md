# Precaución al conectar el cluster real

> Actualizado: 21 de noviembre de 2026

## Aviso

Con `MONGO_DESTINO=atlas`, todo lo que escriba la API o cualquier script del backend queda guardado en el cluster real (base `kompasbd` en MongoDB Atlas), que comparte todo el equipo. Esa base tiene datos reales y no hay papelera: lo que se inserte o sobrescriba ahí no se puede deshacer.

Al solo cambiar la conexión, la API no inserta nada: se conecta y lee y escribe lo que hacen los usuarios en la app. El riesgo está en los scripts y endpoints de abajo.

## No correr con el cluster conectado

Estos scripts y endpoints escriben en la base a la que apunta la API. Con el cluster conectado, meten datos de prueba o sobrescriben datos reales.

| Qué | Qué hace en el cluster | Gravedad |
| --- | --- | --- |
| `backend/scripts/copiar_a_atlas.py` | Sobrescribe por `_id` los documentos del cluster con los de la base local. Las dos bases usan los mismos `_id` para registros distintos: pisaría 81 usuarios, 592 planes y 470 recorridos, y los planes quedarían asignados a otra persona | Crítica |
| `backend/sembrar_datos_ml.py` | Inserta recorridos inventados con otro formato (`usuario_id` de texto y `_id` automático). Daña el contador de `historial_rutas` y después guardar recorridos falla con error 500 | Crítica |
| `backend/scripts/sembrar_actividad_demo.py` | Inserta usuarios, planes y bitácora inventados | Alta |
| `backend/scripts/sembrar_habitos_demo.py` | Inserta usuarios, rutas y recorridos inventados | Alta |
| `demostrar_ia.bat` y Spark (P20 a P22) | Guardan resultados de prácticas y métricas masivas (`metricas_bigdata_kompas`) | Media |
| `POST /api/ia/motor-recomendacion-integral` | Cada llamada guarda un registro en `evaluaciones_ia_kompas`. Probarlo en `/docs` o desde el dashboard acumula registros de prueba | Media |

Nota: `sembrar_datos_ml.py` hoy escribe siempre en la base local `kompas`, aunque la API apunte al cluster. Si alguien cambia su dirección a la del cluster, el daño pasa ahí.

## Lo que sí es seguro

- **Usar la app normalmente.** Solo se guardan los datos reales de los usuarios: registros, planes, recorridos y reportes.
- **Encender o reiniciar el backend.** Al arrancar, la API solo se conecta; no inserta ni borra nada.
- **Correr las pruebas (`pytest`).** Siempre usan la base local `kompas_test`, aunque el `.env` apunte al cluster.
- **`backend/scripts/preparar_bd.py` sin opciones.** Como el cluster ya tiene usuarios, solo revisa colecciones, validadores e índices. Nunca con `--recrear`: esa opción borra la base completa.
- **Los endpoints de consulta** de `/api/ia` (los `GET`): leen datos, no los guardan.

## Antes de correr un script

1. Abre `backend/.env` y revisa `MONGO_DESTINO`.
2. Si dice `atlas`, cámbialo a `local` y reinicia el backend.
3. Corre el script contra tu base local.
4. Regresa `MONGO_DESTINO=atlas` y reinicia el backend.
5. Si dudas de lo que hace un script, pregúntalo en el equipo antes de correrlo.

Configuración del cluster en `backend/.env` (deja `MONGO_URI` apuntando a tu base local):

```
MONGO_DESTINO=atlas
MONGO_URI_ATLAS=mongodb+srv://<usuario>:<contraseña>@<cluster>.mongodb.net/
MONGO_DB_ATLAS=kompasbd
```

- No reemplaces `MONGO_URI` con la dirección del cluster: la API usaría la base `kompas`, que ahí no existe, y crearía una base vacía.
- La contraseña va solo en el `.env`, que no se sube a GitHub. Nunca en documentos, chats ni commits.
