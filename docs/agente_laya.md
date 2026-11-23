# Agente Laya: fundamentos, entrada, preguntas, salida y correspondencia con Prolog

Cubre G3 y G5 de la presentación grupal e I3 e I4 de la defensa individual.

## 1. Qué es Laya y qué no es

Laya es un **modelo estadístico de decisiones tipadas**: recibe un estado (texto) y preguntas
con tipo, y para cada pregunta devuelve una **distribución de probabilidad** sobre las respuestas
posibles. Es un modelo de lenguaje (un encoder) con una cabeza de decisión, no un motor de reglas:

- no ejecuta reglas ni encadena condiciones de forma explícita;
- no demuestra nada ni explica por qué eligió;
- siempre responde algo, aunque no "sepa".

Por eso su salida se registra como **resultado experimental**, nunca como una prueba.

Se usa **sin entrenar** (sin cambiar sus pesos) y con el checkpoint **multilingüe** de forma
explícita, como pide el enunciado:

```python
from laya import Router
router = Router(default="multilingual")
salida = router.predict(texto, preguntas, model="multilingual")
```

Checkpoint: `convaiinnovations/laya`, subcarpeta `multilingual` (encoder mmBERT-base), laya 0.5.0.
Código: `laya_agent/agente_laya.py` y `laya_agent/pregunta.py`.

## 2. Los tres tipos de pregunta

| Tipo | Qué responde | Qué devuelve | Uso en el proyecto |
|---|---|---|---|
| `choice` | una alternativa entre varias con nombre | `choice` y `probabilities` (una por alternativa, suman 1) | **la decisión**: 1 de las 5 acciones |
| `score` | un nivel de una escala ordenada | `probabilities` por nivel y `score` (valor esperado) | diagnóstico: urgencia baja / media / alta |
| `noul` | sí o no | `noul` = probabilidad de "sí" | diagnóstico: ¿falta un dato?, ¿hay contradicción?, ¿el asignado sirve? |

Todas van **en una sola llamada** a `predict`: el modelo lee el estado una vez y responde todas.

## 3. Entrada: el mismo estado que Prolog, como texto

Laya recibe el objeto `estado` del caso, el mismo JSON que Prolog convierte en hechos,
traducido a texto por `laya_agent/estado_texto.py`:

```
Pedido P05. Carga: 1200 kg. Tipo de carga: general. Destino: zona norte. Urgencia: media. Ruta despejada: sí.
Vehículo asignado V50. Tipo: camioneta. Capacidad: 1000 kg. Disponible: sí. En mantención: no. Combustible: suficiente. Conductor disponible: sí.
Vehículo alternativo V51. Tipo: furgón. Capacidad: 3500 kg. Disponible: sí. En mantención: no. Combustible: suficiente. Conductor disponible: sí.
```

- Es una traducción **mecánica**, campo por campo: no dice si la carga cabe, ni porcentajes, ni
  si el vehículo sirve.
- Un `null` se escribe `sin dato`, la misma expresión que usa la descripción de `inspeccionar`.
- **Nunca** recibe `decision_esperada` ni `criterio_esperada` (lo verifica `tests/test_agentes.py`).

**Por qué texto.** Laya es un modelo de lenguaje: lee texto. Con el JSON crudo lee llaves, comillas
y `true`/`false`; escrito como frases, cada dato queda igual en todos los casos. En el conjunto
de desarrollo (§7), el texto acierta 22 % y el JSON 19 %. La diferencia es chica: el formato
solo no resuelve el problema.

## 4. La pregunta de decisión (`choice`)

> ¿Qué acción debe ejecutar primero la central de despacho con este pedido?

| Alternativa | Descripción (`criteria`) | Regla de Prolog que resume |
|---|---|---|
| `despachar` | el vehículo asignado sirve (disponible, fuera del taller, con combustible, con conductor, con capacidad para la carga, compatible con el tipo de carga y con permiso para entrar al destino), la ruta está despejada y conviene salir ya | `vehiculo_apto/2`, `ruta_despejada/2`, `conviene_salir/2` |
| `reasignar` | el vehículo asignado no sirve para este pedido, pero uno de los vehículos alternativos sí sirve | `\+ vehiculo_apto(P, V)`, `alternativa_apta/2` |
| `esperar` | el pedido no es urgente y todavía no puede o no conviene salir: la ruta está cortada, ningún vehículo sirve o el vehículo iría casi vacío | cláusulas de `esperar` |
| `inspeccionar` | falta un dato necesario (sin dato) o los datos se contradicen, por ejemplo disponible y en mantención a la vez, o una capacidad imposible | `falta_dato_critico/2`, `contradiccion/2` |
| `alertar` | el pedido es urgente y no puede salir: ningún vehículo sirve o la ruta está cortada | cláusulas de `alertar` |

Son **las mismas cinco acciones de Prolog** (`accion/1`), en el mismo orden (un `assert` y una
prueba lo revisan).

## 5. Fundamento 1: el sesgo de posición y la rotación de alternativas

La documentación de Laya muestra que el checkpoint tiene **sesgo de posición**: con cinco
alternativas de texto idéntico, el puntaje cambia solo por el lugar que ocupa cada una. La
mitigación que propone la documentación es hacer la misma pregunta con las alternativas en
distintos órdenes (`option_order`), de modo que cada una pase por cada lugar, y **promediar las
probabilidades**.

Eso hace el agente: envía la pregunta 5 veces (`accion_r0` … `accion_r4`) con el orden rotado,
en la misma llamada, y promedia. No es entrenar: el modelo no cambia, solo se le pregunta de
forma que su respuesta no dependa de qué acción quedó primera.

Además deja una medida nueva, la **estabilidad**: cuántos de los 5 órdenes, por separado,
eligen la misma acción. 5/5 significa que la respuesta no depende del orden; 2/5 o 3/5 significa
que sí.

Resultado medido: en el conjunto de desarrollo solo 12 de 200 estados tienen estabilidad 5/5, y
en los 20 casos, 7 de 20. El sesgo es real y la rotación está justificada.

## 6. Fundamento 2: preguntas de diagnóstico (`score` y `noul`)

La decisión es una cadena de pasos. Para ver **en qué paso** falla Laya, se le hacen preguntas
más simples que corresponden a un hecho o una regla de Prolog. **No influyen en la decisión**:
solo se comparan.

| Pregunta a Laya | Tipo | Se compara con | Nivel |
|---|---|---|---|
| ¿Qué urgencia tiene el pedido? | score | `urgencia/2` (hecho del estado) | información directa |
| ¿Falta algún dato necesario para decidir (aparece sin dato)? | noul | `falta_dato_critico/2` | información incompleta |
| ¿Hay datos que se contradicen…? | noul | `contradiccion/2` | contradicción |
| ¿El vehículo asignado puede llevar este pedido…? | noul | `vehiculo_apto/2` con el asignado | inferencia encadenada |

## 7. Cómo se eligió el diseño: conjunto de desarrollo

Diseñar la pregunta mirando los 20 casos de evaluación sería hacer trampa: quedaría ajustada a
esos casos. Por eso `laya_agent/generador.py` genera **200 estados sintéticos** (40 por acción,
etiquetados con la política de la central) y `experimento/disenio_pregunta.py` compara diseños
en ellos. Los 20 casos se miden una sola vez, al final. Resultados en
[`experimento/disenio_pregunta.md`](../experimento/disenio_pregunta.md):

| Diseño | Aciertos (de 200) | Confianza media |
|---|---|---|
| 1. JSON crudo, un orden (avance) | 19 % | 0,66 |
| 2. Texto, un orden | 22 % | 0,53 |
| 4. Texto + **reglas de la central como contexto**, 5 órdenes | 20 % (elige `esperar` en los 200) | **0,86** |
| 5. Texto + **observaciones calculadas por caso**, 5 órdenes | 18 % | 0,52 |
| **3. Texto, 5 órdenes promediados (final)** | **26 %** | 0,39 |

Al azar se espera 20 %. El diseño final es el mejor, pero queda cerca del azar. Además, la
confianza **baja** al promediar: con un solo orden el modelo aparentaba más seguridad de la que
tenía.

**Más contexto (diseños 4 y 5, `laya_agent/contexto.py`).** Se le dio a Laya:
- el mismo conocimiento general que Prolog tiene en `reglas.pl`, escrito como texto (capacidades
  máximas, refrigeración, zona centro, umbral de 80 %, prioridades). Es igual para todos los
  casos, así que no entrega ninguna conclusión;
- como variante, frases calculadas para cada caso ("la carga no cabe: 1200 kg de 1000 kg").

Ninguna mejora. Con las reglas, Laya elige `esperar` en los 200 estados **con confianza 0,86**:
el contexto la hizo más segura, no más precisa. Laya clasifica el texto completo y no ejecuta las
reglas que lee; el texto extra compite con los datos del caso. Por eso el diseño final no usa
contexto.

Otros diseños probados en desarrollo, que no mejoraron (se dejan registrados):

| Diseño probado | Resultado | Por qué se descartó |
|---|---|---|
| Descripciones sin negaciones, con el vocabulario del estado | 17–18 % | no mejora |
| Estado narrado con antónimos (libre/ocupado, en el taller/fuera del taller) para evitar el "no" | 18–21 % | no mejora |
| Motor por defecto de laya 0.5 (lector LLM de 0.8B), sin entrenar | 20–25 % | no mejora; marcó todos los casos para revisión humana (`route = review`); además el enunciado pide el checkpoint multilingüe |
| Motor por defecto de laya 0.5 + reglas como contexto (± observaciones) | 20–24 % | no mejora: un lector tipo LLM pequeño tampoco aprovecha las reglas |
| Una `noul` por acción ("¿corresponde despachar?") | 12 % | peor: responde "sí" a casi todo |
| Comparaciones por pares (10 pares × 2 órdenes) | 22 % | no mejora |
| Checkpoint oficial `typed-decisions` con el texto **en inglés** | 45 % (9/20 en los casos) | mejora, pero exige pasar el texto a inglés y el enunciado pide el multilingüe para texto en español; con reglas como contexto baja a 32–34 %. Pendiente de consultar al profesor |

## 8. Por qué no se entrena

El enunciado dice que el fine-tuning **no se exige** y la rúbrica no lo pide en ningún criterio.
El grupo probó ajustar el checkpoint con estados sintéticos y lo **descartó**: el profesor indicó
que no corresponde. Además hay una razón de fondo: si las etiquetas de entrenamiento salen de las
reglas de Prolog, Laya aprende a imitar a Prolog y la comparación se vuelve circular. Ya no
compararía "reglas explícitas vs. un modelo estadístico", sino "Prolog vs. una copia aproximada de
Prolog".

Ver la decisión registrada en [`uso_ia.md`](uso_ia.md).

## 9. Salida y cómo interpretarla

| Campo | Cómo se calcula | Cómo leerlo |
|---|---|---|
| `accion` | la de mayor probabilidad promedio | la respuesta de Laya |
| `probabilidades` | promedio de las 5 rotaciones | suman 1; con 5 acciones, 0,20 es "no distingue" |
| `confianza` | probabilidad promedio de la elegida | cuánto peso le da a su respuesta |
| `margen` | diferencia con la segunda | cerca de 0 = empate entre dos acciones |
| `estabilidad` | órdenes que eligen lo mismo (de 5) | 5/5 = no depende del orden |
| `diagnostico` | respuestas `score` y `noul` | ver §6 |

Todo se guarda en `registros/laya.jsonl` con el texto enviado y las preguntas.

**Ejemplo: C05** (1200 kg en una camioneta de 1000 kg; furgón alternativo libre; esperada
`reasignar`). Laya responde `esperar` con 0,32, `inspeccionar` 0,29, `reasignar` 0,18. El margen
es 0,03 y la estabilidad 3/5. Laya no distingue entre tres acciones, y su respuesta cambia según
el orden. En el diagnóstico dice que el asignado sí sirve (P(sí) = 0,99), cuando Prolog demuestra
lo contrario (`1200 =< 1000` falla). **No hizo la comparación de pesos que decide el caso.**

**Ejemplo: C15** (falta la lista de alternativos, pero el asignado sirve; esperada `despachar`).
Laya elige `inspeccionar` con 0,56 y estabilidad 5/5: reacciona a las palabras "sin dato".
Prolog despacha porque `falta_dato_critico/2` sabe que los alternativos solo importan si el
asignado no sirve. **Una respuesta estable y con más confianza que el resto igual puede estar
mal:** estabilidad y confianza no son una demostración.

## 10. Correspondencia con Prolog

| | Prolog | Laya |
|---|---|---|
| Entrada | el estado JSON convertido en hechos | el mismo estado convertido en texto |
| Conocimiento | reglas explícitas en `prolog/reglas.pl` | lo que el checkpoint trae + una frase por acción |
| Alternativas | `accion/1`: 5 acciones | `criteria`: las mismas 5, en el mismo orden |
| Cómo decide | demuestra las acciones posibles y elige por prioridad | elige la alternativa más probable |
| Salida | acción + derivación (hechos y reglas usados) | acción + probabilidades + confianza + estabilidad |
| Datos que faltan | `desconocido/2` y `falta_dato_critico/2`: sabe si el dato importa | ve "sin dato" en el texto, sin saber si importa |
| Aritmética (80 %, capacidad máxima) | exacta (`Carga / Capacidad >= 0.8`) | no la hace |
| Si cambia una regla | cambia la respuesta de inmediato | hay que reescribir la descripción; no hay garantía de que la siga |

**Se conserva:**
- el estado (mismos campos y valores);
- las cinco alternativas y su orden;
- la intención de cada regla, resumida en la descripción de cada acción.

**Se adapta:**
- el estado pasa de JSON a texto;
- las reglas se resumen en una frase por acción;
- la pregunta se repite en 5 órdenes por el sesgo de posición;
- los umbrales, las capacidades máximas y la prioridad entre acciones no tienen equivalente en
  Laya (solo aparecen como palabras dentro de las descripciones).

**No es equivalente:**
- Prolog da una conclusión demostrada o no da ninguna; Laya siempre elige algo.
- La confianza de Laya es una probabilidad, no una prueba.
- Las preguntas de diagnóstico muestran que Laya, sin entrenar, tampoco resuelve los pasos
  simples: responde "sí" a casi todas las `noul`, y la urgencia la acierta como al azar.

## 11. Cómo modificar en vivo

Ver [`guia_defensa.md`](guia_defensa.md) §4. Resumen:

| Qué piden | Dónde | Cómo se prueba |
|---|---|---|
| Cambiar la redacción de una alternativa | `CRITERIOS` en `laya_agent/pregunta.py` | reiniciar la app y ejecutar el caso |
| Cambiar la instrucción | `INSTRUCCION` en `laya_agent/pregunta.py` | ídem |
| Agregar una alternativa | `ACCIONES` y `CRITERIOS` en `pregunta.py` + `accion/1`, `prioridad/2` y reglas en Prolog | `python -m unittest tests.test_agentes` |
| Agregar una pregunta de diagnóstico | `DIAGNOSTICO` en `pregunta.py` y su referencia en `laya_agent/comparacion.py` | app → tabla de diagnóstico |
| Medir un cambio de redacción sin mirar los 20 casos | `python -m experimento.disenio_pregunta` | `experimento/disenio_pregunta.md` |
