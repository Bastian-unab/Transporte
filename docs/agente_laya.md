# Agente Laya: entrada, pregunta, salida y correspondencia con Prolog

Responsable: Persona 2 · Laya y front. Cubre G3 y G5 de la presentación grupal e I3 e I4 de la
defensa individual.

## 1. Qué es Laya en este proyecto

Laya es un modelo estadístico de decisión: recibe un **estado** y una **pregunta tipada**, y
responde con una **distribución de probabilidad** sobre las alternativas. No ejecuta reglas, no
demuestra nada y no explica en lenguaje natural por qué eligió. Su salida se registra como
resultado experimental y se compara con la decisión esperada y con Prolog.

Se usa el checkpoint **multilingüe** de forma explícita, porque el estado y la pregunta están en
español:

```python
from laya import Router
router = Router(default="multilingual")
salida = router.predict(estado, preguntas, model="multilingual")
```

Código: `laya_agent/agente_laya.py` (función `ejecutar_laya(estado, version)`).

## 2. Entrada: el mismo estado que Prolog

Laya recibe el objeto `estado` del caso, exactamente el mismo JSON que Prolog lee con
`prolog/estado_json.pl` (ver `docs/estado_canonico.md`). Si se le pasa un diccionario, Laya lo
convierte a texto JSON y lee ese texto.

- **Nunca** recibe `decision_esperada` ni `criterio_esperada` (lo verifica `tests/test_laya.py`).
- Un dato que falta llega como `null`, igual que a Prolog.

## 3. La pregunta

Una sola pregunta de tipo **`choice`** (`laya_agent/preguntas.py`):

> ¿Qué acción de despacho debe ejecutarse primero para este pedido?

Las alternativas son **las mismas cinco acciones de Prolog, en el mismo orden**: despachar,
reasignar, esperar, inspeccionar, alertar. En Laya el orden es parte de la pregunta.

Cada alternativa lleva una descripción (`criteria`) que el modelo lee junto con el estado. Hay
dos versiones:

| Acción | v1 (texto acordado por el grupo) | v2 (con las palabras del estado JSON) |
|---|---|---|
| despachar | hay vehículo adecuado y disponible | el vehículo asignado está disponible, no está en mantención, tiene combustible suficiente y capacidad para la carga, y la ruta está despejada |
| reasignar | el vehículo asignado no sirve, pero hay otro apto | el vehículo asignado no puede llevar el pedido, pero uno de los vehículos alternativos sí puede |
| esperar | no hay urgencia o no hay vehículo libre todavía | la urgencia es baja y la ruta no está despejada, el vehículo iría casi vacío o no hay vehículo libre |
| inspeccionar | faltan datos o hay contradicción | faltan datos (valores null) o los datos se contradicen, por ejemplo disponible y en mantención al mismo tiempo |
| alertar | requiere intervención del supervisor | la urgencia es alta y el pedido no puede salir: no hay vehículo apto o la ruta no está despejada |

Según la documentación de Laya, las descripciones que usan el mismo vocabulario del estado ayudan
al modelo a distinguir las alternativas. Comparar v1 y v2 muestra cuánto depende la decisión de
la redacción, algo que en Prolog no pasa.

**¿Por qué no `score` ni `noul`?** El enunciado pide principalmente `choice`. La decisión es elegir
una de cinco acciones, que es exactamente lo que hace `choice`:

- `noul` responde sí/no con la probabilidad de "sí"; serviría para una pregunta auxiliar, como
  "¿el vehículo asignado sirve?";
- `score` da un nivel ordenado, como una urgencia de 0 a 4.

Ninguna de las dos es necesaria para comparar la decisión principal.

## 4. Salida y cómo leerla

`ejecutar_laya()` devuelve (y `registrar()` guarda en `registros/laya.jsonl`):

| Campo | Viene de | Cómo interpretarlo |
|---|---|---|
| `accion` | `choice` | la alternativa con mayor probabilidad |
| `probabilidades` | `probabilities` | probabilidad de cada una de las 5 acciones; suman 1 |
| `confianza` | `answer_confidence` = max(p) | probabilidad de la acción elegida |
| `concentracion` | `confidence` = 1 − H(p)/log(k) | qué tan concentrada está la distribución: cerca de 1, casi toda en una acción; cerca de 0, repartida |
| `act_probability` | otra cabeza del modelo | "¿conviene actuar?"; se registra pero no se usa |
| `estado_enviado`, `pregunta`, `modelo`, `version_laya`, `version_criterios` | — | lo que se envió exactamente, para poder reproducirlo |

Tres advertencias de la documentación oficial de Laya, útiles para la defensa:

1. **La confianza no garantiza acierto.** Laya 0.4.12 dice entregar confianza calibrada, pero su
   documentación reconoce un defecto de calibración (issue #1245). En nuestra primera ejecución
   (`registros/laya.jsonl`) eligió `despachar` en 16 de 20 casos con confianza de 0,43 a 0,82 y
   solo acertó 2 de esos 16.
2. **La negación no se maneja de forma confiable** en preguntas `choice`. Nuestro estado tiene
   muchos `false` (`en_mantencion: false`), así que es un riesgo concreto.
3. **Una probabilidad alta no es una demostración.** Laya no puede decir por qué eligió algo;
   Prolog sí (la justificación de `decidir/3`).

## 5. Correspondencia con Prolog

| | Prolog | Laya |
|---|---|---|
| Entrada | el estado JSON convertido en hechos | el mismo estado JSON, leído como texto |
| Conocimiento | reglas explícitas en `prolog/reglas.pl` | solo las descripciones de las cinco alternativas |
| Alternativas | `accion/1`: 5 acciones | `criteria`: las mismas 5, en el mismo orden |
| Cómo decide | demuestra las acciones posibles y elige por prioridad | elige la alternativa más probable |
| Salida | una acción + derivación (hechos y reglas usados) | una acción + probabilidades + confianza |
| Datos que faltan | detectados con `desconocido/2` y `falta_dato_critico/2` | depende de que el modelo interprete `null` |
| Si cambia la redacción | no cambia nada | la decisión puede cambiar (v1 vs v2) |

**Se conserva:** el estado, las alternativas y la intención de cada acción.

**Se adapta:**
- las reglas se resumen en una frase por alternativa;
- los umbrales (capacidades máximas, 80 % de aprovechamiento) y las restricciones (refrigerado, zona centro) no se le dicen a Laya;
- la prioridad entre acciones no existe en Laya;
- no hay justificación.

**No es equivalente:** Prolog da una conclusión demostrada o no da ninguna; Laya siempre elige
algo, aunque los datos no alcancen.

## 6. Cómo modificar en vivo (defensa, I6)

| Qué piden | Dónde | Comando para probar |
|---|---|---|
| Cambiar la redacción de una alternativa | `CRITERIOS` en `laya_agent/preguntas.py` | `python -m laya_agent.ejecutar_caso C09` |
| Cambiar la pregunta | `INSTRUCCION` en `laya_agent/preguntas.py` | ídem |
| Usar la otra versión de criterios | — | `python -m laya_agent.ejecutar_caso C09 --criterios v2` |
| Agregar una alternativa | `ACCIONES` y `CRITERIOS` en `preguntas.py`, y `accion/1` y `prioridad/2` en Prolog (con Persona 1) | `python -m unittest tests.test_laya` |
| Agregar un campo al estado | el JSON del caso (Laya lo lee solo) y `prolog/estado_json.pl` para Prolog (con Persona 1) | `python -m laya_agent.ejecutar_caso --estado nuevo.json` |
