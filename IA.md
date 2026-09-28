# Kompás — Integración del sistema experto de Einar con la API

> Einar ya tiene el motor (`evaluar(entrada, base)`), las 20 reglas R01–R20 en `reglas.json` y las 36 comprobaciones.
> **Esas reglas se quedan como están.** Este documento solo dice cómo se conectan con la API.
> Los lugares vienen de **Google Places**. Detalle completo en `BACKEND.md`, secciones 6 y 7.

## 1. Qué no cambia (Einar)
- `evaluar(entrada, base)`, `--json` y `--verificar`.
- `docs/sistema-experto/reglas.json` y `casos.json`.
- Lógica de tres valores (true / false / null), estados y puntuación 0–6.

## 2. Cómo corre dentro de la app

```
App: "Crear mi plan"
  │  contexto, intereses, tiempo, presupuesto, movilidad, origen, hora
  ▼
API  POST /api/itinerarios                              (Jesús)
  ├─ 1. Busca lugares cercanos en Google Places          (Jesús)
  │      nombre, ubicación, tipo, horario, nivel de precio, calificación
  ├─ 2. planificador.py arma hasta 3 itinerarios          (Jesús)
  ├─ 3. hechos.py → proposiciones true/false/null         (Einar)
  ├─ 4. evaluar() aplica R01–R20 → estado, puntos, traza  (Einar, ya hecho)
  └─ 5. Respuesta para "Tus planes"                       (Jesús)
```

## 3. Archivos

```
backend/app/ia/
├── motor.py         # Einar: evaluar() importable (la demo lo importa desde aquí)
├── hechos.py        # Einar: itinerario + solicitud → proposiciones de entrada
├── planificador.py  # Jesús
└── servicio.py      # Jesús: recomendar(solicitud, lugares) → llama a evaluar() por candidato
```

- `motor.py` se importa sin ejecutar la demo: `from app.ia.motor import evaluar, cargar_base`.
- `herramientas/sistema_experto_demo.py` importa el motor desde `app/ia/motor.py`: **la demo y la API corren el mismo código**. `--verificar` sigue dando `36 comprobaciones; 20/20 reglas`.

## 4. Lo que recibe `hechos.py` por cada itinerario

```python
{
  "solicitud": {
    "contexto": "pareja", "intereses": ["comer", "cafe"],
    "presupuesto_por_persona": 300, "tiempo_minutos": 240,
    "movilidad": ["caminando"], "fecha_hora_salida": "2026-09-30T18:00:00-06:00"
  },
  "itinerario": {
    "visitas": [
      {
        "place_id": "ChIJ…", "nombre": "…", "categoria": "cafe",
        "llegada_estimada": "2026-09-30T18:12:00-06:00", "estancia_minutos": 40,
        "horario": [{"dia": 3, "abre": "08:00", "cierra": "21:00"}],   # de Google; None si no trae
        "nivel_precio": "MODERATE",                                     # de Google; None si no trae
        "rango_precio": {"min": 100, "max": 200, "moneda": "MXN"},      # de Google; casi siempre None
        "consultado_en": "2026-09-30T17:59:40-06:00"
      }
    ],
    "tramos": [{"modo": "caminando", "km": 0.9, "minutos": 12, "estimado": True}],
    "regreso_incluido": False
  }
}
```

## 5. Proposiciones: de dónde sale cada una

| Proposición | Cómo |
|---|---|
| `datos_usuario_validos` | validación de la solicitud |
| `modo_disponible` | a pie / taxi `true` en la zona · transporte público `null` |
| `ruta_calculada` | **decide Einar**: distancia estimada → `true` con advertencia, o `null` |
| `abierto` | cada visita cabe completa en su horario del día de Google · sin horario → `null` |
| `dentro_presupuesto` | `rango_precio` si viene · si solo hay `nivel_precio`, **Einar define** una tabla ($ → MXN) o lo deja `null` |
| `cabe_en_tiempo` | suma de tramos + estancias ≤ tiempo disponible |
| `datos_vigentes` | `true`: consultado a Google en ese momento |
| `requiere_accesibilidad`, `control_cierres_habilitado` | `false` (MVP) |
| `accesibilidad_verificada`, `cierre_vigente` | `null` |
| `contexto_compatible`, `intereses_compatibles` | tabla categoría ↔ contexto · categoría ∈ intereses |
| `poca_caminata`, `pocos_transbordos` | caminata total ≤ 2 km · a pie o taxi = sin transbordos |

Con horario y precio de Google, un itinerario **sí puede llegar a `recomendable`** (R15 → R16 → R17–R20).

## 6. Decisiones que le tocan a Einar
1. ¿Una ruta estimada por distancia cuenta como `ruta_calculada = true` con advertencia?
2. ¿Cómo se traduce el nivel de precio de Google ($, $$, $$$, $$$$) a pesos para `dentro_presupuesto`, o se deja `null`?
3. Estancia estimada por categoría (propuesta: comer 60, café 40, cultura 60, entretenimiento 90, aire libre 60 min).
