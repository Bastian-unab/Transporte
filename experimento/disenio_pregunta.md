# Diseño de la pregunta de Laya (conjunto de desarrollo)

Generado por `python -m experimento.disenio_pregunta` el 2026-11-19 19:54. 200 estados sintéticos (40 por acción) etiquetados con la política de la central (reglas de Prolog). **Laya no se entrena:** estos estados solo sirven para elegir cómo preguntar sin mirar los 20 casos de evaluación. Al azar se espera 20 % de aciertos.

## Decisión (pregunta choice)

| Diseño | Aciertos | Confianza media | Acciones que elige |
|---|---|---|---|
| 1. JSON crudo, un orden | 38/200 (19%) | 0.66 | despachar 14, reasignar 0, esperar 185, inspeccionar 1, alertar 0 |
| 2. Texto, un orden | 43/200 (22%) | 0.53 | despachar 0, reasignar 0, esperar 190, inspeccionar 10, alertar 0 |
| 4. Texto + reglas de la central como contexto, 5 órdenes (descartado) | 40/200 (20%) | 0.86 | despachar 0, reasignar 0, esperar 200, inspeccionar 0, alertar 0 |
| 5. Texto + observaciones calculadas por caso, 5 órdenes (descartado) | 35/200 (18%) | 0.52 | despachar 0, reasignar 1, esperar 18, inspeccionar 181, alertar 0 |
| 3. Texto, 5 órdenes promediados (final) | 53/200 (26%) | 0.39 | despachar 0, reasignar 1, esperar 148, inspeccionar 51, alertar 0 |

Con el diseño final, en 12 de 200 estados los 5 órdenes eligen la misma acción.

## Preguntas de diagnóstico (score y noul)

| Pregunta | Tipo | Coincide con Prolog | Laya dice "sí" | Respuesta correcta "sí" |
|---|---|---|---|---|
| ¿Qué urgencia tiene el pedido? | score | 63/199 (32%) | — | — |
| ¿Falta algún dato necesario para decidir (aparece sin dato)? | noul | 71/200 (36%) | 74% | 12% |
| ¿Hay datos que se contradicen, como un vehículo disponible y en mantención a la vez o una capacidad imposible para su tipo? | noul | 17/200 (8%) | 99% | 8% |
| ¿El vehículo asignado puede llevar este pedido (disponible, fuera del taller, con combustible, con conductor, con capacidad suficiente y compatible con la carga y el destino)? | noul | 70/200 (35%) | 100% | 35% |

Si Laya dice "sí" casi siempre, su porcentaje de coincidencia es solo la proporción de "sí" correctos: no está leyendo el dato. Ver la interpretación en `docs/agente_laya.md`.