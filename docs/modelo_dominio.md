# Modelo del dominio: despacho de vehículos y carga local

Responsable: Persona 1 · Modelo y Prolog. Cubre G1 y G2 de la presentación grupal e I1 e I2
de la defensa individual.

## 1. Problema real y relevancia

Una empresa de reparto de carga local tiene una **central de despacho**. La planificación
asigna cada pedido a un vehículo, pero antes de que salga alguien tiene que confirmar que esa
asignación sirve: el vehículo puede estar en el taller, no tener capacidad, no ser apto para el
tipo de carga o no poder entrar a la zona de destino, y la ruta puede estar cortada. La central
tiene que decidir rápido qué hacer con cada pedido.

Por qué el problema sirve para el proyecto:

- es una situación real, comprensible y **no informática**, sin datos privados (los casos son
  inventados) y sin decisiones que requieran autoridad profesional;
- la decisión tiene **cinco alternativas acotadas**;
- todo lo que se usa es **observable**: kilos, tipo de vehículo, estado del taller, ruta;
- tiene reglas explícitas (capacidad, compatibilidad de la carga, zonas restringidas), que
  encajan con Prolog, y también datos que faltan o se contradicen, que permiten analizar cómo
  responde Laya ante la incertidumbre.

## 2. Decisión principal

> **¿Qué acción de despacho debe ejecutarse primero para un pedido?**

Cada caso describe un pedido, su vehículo asignado y los vehículos alternativos disponibles.
El agente elige exactamente una acción.

## 3. Alternativas

Las mismas cinco, en el mismo orden, en Prolog (`accion/1`) y en Laya.

| Acción | Cuándo corresponde | Prioridad |
|---|---|---|
| `despachar` | El vehículo asignado sirve, la ruta está despejada y conviene salir ya | 4 |
| `reasignar` | El asignado no sirve, pero un alternativo sí | 3 |
| `esperar` | No hay urgencia, y la ruta está cortada, no hay vehículo libre todavía o el vehículo iría casi vacío | 5 (mínima) |
| `inspeccionar` | Faltan datos necesarios, los datos se contradicen o ninguna regla aplica | 1 (máxima) |
| `alertar` | El pedido es urgente y no puede salir (sin vehículo apto o con la ruta cortada) | 2 |

Si más de una acción se puede demostrar, gana la de **menor número de prioridad**. La política
es: primero asegurar que los datos sean confiables, luego atender lo urgente que no puede
resolverse solo, luego corregir la asignación y por último operar normalmente.

## 4. Entidades, propiedades y relaciones

| Entidad | Propiedades | Relaciones |
|---|---|---|
| Pedido | carga (kg), tipo de carga, destino, urgencia | *está asignado a* un vehículo; *tiene* vehículos alternativos; *va por* una ruta |
| Vehículo | tipo, capacidad (kg), disponible, en mantención, combustible | *es conducido por* un conductor; *puede o no entrar a* una zona |
| Conductor | disponible | *conduce* un vehículo |
| Ruta | despejada o no | *lleva al* destino del pedido |
| Zona de destino | centro o zona norte, sur, oriente o poniente | *restringe* ciertos tipos de vehículo |
| Central de despacho | — | *decide* la acción para el pedido |

En Prolog, las relaciones son hechos con dos entidades: `asignado(p05, v50)`,
`alternativo(p05, v51)`. Las propiedades son hechos con la entidad y un valor:
`capacidad_kg(v50, 1000)`. Gracias a eso, la misma regla `vehiculo_apto(P, V)` sirve para el
asignado y para cualquier alternativo: basta con unificar `V` con uno u otro.

## 5. Estado común

Está definido en [`estado_canonico.md`](estado_canonico.md): 6 campos del pedido y 7 por
vehículo, con un vehículo asignado y una lista de alternativos. Solo contiene observaciones,
nunca conclusiones. Ambos agentes reciben el mismo JSON: Prolog lo convierte en hechos de forma
mecánica (`prolog/estado_json.pl`) y Laya lo lee como texto. Por eso la comparación es justa:
si los agentes difieren, la diferencia está en **cómo razonan**, no en lo que recibieron.

## 6. Restricciones

| # | Restricción | Regla de Prolog |
|---|---|---|
| R1 | La carga no puede superar la capacidad del vehículo | `tiene_capacidad/2` |
| R2 | La carga refrigerada solo puede ir en furgón refrigerado | `tipo_compatible/2` |
| R3 | Los camiones no pueden entrar al centro | `zona_restringida(centro, camion)` y `puede_ingresar/2` |
| R4 | Un vehículo solo sale si está libre, fuera del taller, con combustible y con conductor | `operativo/1` |
| R5 | No se despacha con la ruta cortada | `accion_candidata(P, despachar)` exige `ruta_despejada(P, si)` |
| R6 | No se actúa con datos faltantes o contradictorios | `accion_candidata(P, inspeccionar)` con prioridad 1 |
| R7 | Se ejecuta una sola acción por pedido | `decidir/3` toma la candidata de mayor prioridad |

## 7. Supuestos

| # | Supuesto |
|---|---|
| S1 | Cada pedido se decide por separado; no se optimiza la flota completa ni el orden de varios pedidos. |
| S2 | Un vehículo alternativo de la lista está asignable: si es apto, se le puede pasar el pedido. |
| S3 | Sin urgencia, un vehículo que iría con menos del 80 % de su capacidad espera para juntar más carga (consolidación). |
| S4 | Con urgencia media o alta, se sale aunque el vehículo vaya casi vacío. |
| S5 | Si un pedido urgente no puede salir, siempre se avisa al supervisor; si no es urgente, se espera. |
| S6 | Los datos de los alternativos solo importan cuando el asignado no sirve. |
| S7 | Las capacidades máximas por tipo (camioneta 1500 kg, furgón 3500 kg, furgón refrigerado 3000 kg, camión 12000 kg) y el umbral de 80 % son definiciones del grupo, no normas oficiales. |

## 8. Información que puede faltar y contradicciones

Prolog trabaja con el **supuesto de mundo cerrado**: lo que no puede demostrar lo trata como
falso (negación por falla, `\+`). Si un dato vacío simplemente no se escribiera, Prolog
podría concluir, por ejemplo, que el pedido "no es urgente" cuando en realidad *no se sabe*.
Por eso:

1. cada `null` se registra como `desconocido(Entidad, Campo)`;
2. `falta_dato_critico/2` detecta cuándo ese dato vacío **importa** para la decisión, y entonces
   `inspeccionar` pasa a ser candidata con la prioridad más alta.

| Dato que falta | ¿Es crítico? | Por qué |
|---|---|---|
| Cualquier campo del pedido | Sí | sin carga, tipo, destino, urgencia o ruta no se puede decidir |
| Cualquier campo del vehículo asignado | Sí | no se puede saber si sirve |
| La lista de alternativos (`null`) | Solo si el asignado no sirve | si el asignado sirve, no hace falta un reemplazo |
| Un campo de un alternativo | Solo si el asignado no sirve | ídem |

| Contradicción | Cuándo se produce |
|---|---|
| `disponible_y_en_mantencion(V)` | el sistema de flota dice que V está libre y el taller dice que está en mantención |
| `capacidad_imposible(V)` | la capacidad declarada supera el máximo del tipo de vehículo (p. ej., camioneta de 9000 kg) |
| `carga_no_positiva` | el pedido declara 0 kg o menos |

Si ninguna acción se puede demostrar (por ejemplo, el pedido existe pero no tiene vehículo
asignado registrado), `decidir/3` **cae en `inspeccionar` por defecto** e indica en la
justificación que ninguna regla aplicó.

## 9. Representación en Prolog

| Archivo | Contenido |
|---|---|
| `prolog/reglas.pl` | conocimiento general: alternativas, prioridades, restricciones, reglas, `decidir/3` y la justificación |
| `prolog/hechos.pl` | datos concretos de seis pedidos de ejemplo escritos a mano (p01, p02, p05, p90, p91, p92) |
| `prolog/consultas.pl` | 12 consultas comentadas; `swipl prolog/consultas.pl` las ejecuta todas |
| `prolog/estado_json.pl` | lee el estado canónico en JSON y lo convierte en hechos |
| `prolog/ejecutar.pl` | ejecuta el agente desde la terminal (salida en JSON para Python o en texto) |
| `prolog/verificar_casos.pl` | compara la decisión de Prolog con la esperada en todos los casos |
| `tests/test_reglas.pl` | 13 pruebas automáticas (plunit) |

Las **variables** empiezan con mayúscula (`P`, `V`, `W`, `Carga`); los **átomos** con
minúscula (`p05`, `camioneta`, `reasignar`). Por convención, `P` es siempre un pedido y `V` o
`W` un vehículo.

### 9.1 Hechos

**Hechos del estado** (cambian en cada caso): `pedido/1`, `carga_kg/2`, `tipo_carga/2`,
`destino/2`, `urgencia/2`, `ruta_despejada/2`, `asignado/2`, `alternativo/2`, `vehiculo/1`,
`tipo_vehiculo/2`, `capacidad_kg/2`, `disponible/2`, `en_mantencion/2`, `combustible/2`,
`conductor_disponible/2` y `desconocido/2`. Su significado está en
[`estado_canonico.md`](estado_canonico.md).

**Hechos generales del dominio** (no cambian):

| Hecho | Qué significa | Ejemplo |
|---|---|---|
| `accion(A)` | A es una de las cinco alternativas | `accion(reasignar).` |
| `prioridad(A, N)` | si hay empate, gana la acción con menor N | `prioridad(inspeccionar, 1).` |
| `capacidad_maxima(Tipo, Kg)` | carga máxima real de un tipo de vehículo | `capacidad_maxima(camioneta, 1500).` |
| `zona_restringida(Zona, Tipo)` | ese tipo de vehículo no puede entrar a esa zona | `zona_restringida(centro, camion).` |
| `umbral(Nombre, Valor)` | límite numérico usado por una regla | `umbral(aprovechamiento_alto, 0.8).` |

### 9.2 Reglas

| Regla | Qué significa | Variables | Ejemplo |
|---|---|---|---|
| `urgente(P)` | el pedido tiene urgencia alta | P: pedido | `urgente(p01)` es verdadero |
| `operativo(V)` | V está libre, fuera del taller, con combustible y con conductor | V: vehículo | `operativo(v901)` falla: combustible bajo |
| `tiene_capacidad(P, V)` | la carga de P cabe en V | P, V; internas: `Carga`, `Capacidad` | `tiene_capacidad(p05, v50)` falla: 1200 > 1000 |
| `tipo_compatible(P, V)` | V puede llevar el tipo de carga de P (dos cláusulas: general o refrigerada) | P, V | `tipo_compatible(p90, v900)` falla: refrigerada en camión |
| `puede_ingresar(P, V)` | V puede entrar a la zona de destino de P | P, V; internas: `Zona`, `Tipo` | `puede_ingresar(p90, v900)` falla: camión al centro |
| `aprovechamiento_alto(P, V)` | la carga ocupa al menos el 80 % de V | P, V; internas: `Carga`, `Capacidad`, `U` | C07: 1350/1500 = 0,9 |
| `vehiculo_apto(P, V)` | V sirve para P: operativo + capacidad + tipo + zona | P, V | `vehiculo_apto(p05, v51)` |
| `alternativa_apta(P, W)` | algún alternativo W de P es apto | P, W | `alternativa_apta(p90, W)` da `W = v902` |
| `sin_vehiculo_apto(P)` | ni el asignado ni ningún alternativo sirven | P; interna: `V` | C06 |
| `conviene_salir(P, V)` | vale la pena salir ya: urgencia alta, media, o baja con aprovechamiento alto | P, V | C08 falla: baja y 13 % |
| `vehiculo_relevante(P, V)` | V es un vehículo cuyos datos importan | P, V | los alternativos solo si el asignado no sirve |
| `falta_dato_critico(P, dato(E, C))` | falta el campo C de la entidad E y es necesario | P, E, C | `dato(p01, urgencia)` |
| `contradiccion(P, Tipo)` | los datos de P no pueden ser verdad a la vez | P, Tipo | `disponible_y_en_mantencion(v920)` |
| `accion_candidata(P, A)` | A se puede demostrar para P (puede haber varias) | P, A | p92: `inspeccionar` y `reasignar` |
| `acciones_candidatas(P, L)` | lista de candidatas ordenada por prioridad | P, L | `[inspeccionar, reasignar]` |
| `decidir(P, A, J)` | **predicado de entrada**: acción elegida A y justificación J | P, A, J | `decidir(p05, reasignar, J)` |

### 9.3 Herramientas para explicar

| Predicado | Para qué |
|---|---|
| `demostrar(Meta, Arbol)` | meta-intérprete: resuelve Meta como Prolog y guarda el árbol de prueba |
| `explicar(P)` | imprime decisión, candidatas, contradicciones, faltantes y justificación |
| `porque(P, A)` | imprime la derivación de una acción, o dice que no se puede demostrar |
| `por_que_no(Meta)` | explica qué condición falla cuando algo no se puede demostrar |

La justificación que devuelve `decidir/3` es una lista de `paso(Nivel, Tipo, Meta)`, donde Tipo
es `hecho`, `regla`, `calculo`, `no_demostrable(Fallas)` o `sin_regla`.

## 10. Lectura en lógica de primer orden

Cada regla es una implicación con las variables cuantificadas universalmente:

```
∀P ∀V ( operativo(V) ∧ tiene_capacidad(P,V) ∧ tipo_compatible(P,V) ∧ puede_ingresar(P,V) → vehiculo_apto(P,V) )
∀P ∀W ( alternativo(P,W) ∧ vehiculo_apto(P,W) → alternativa_apta(P,W) )
∀P ∀V ( asignado(P,V) ∧ ¬vehiculo_apto(P,V) ∧ ∃W alternativa_apta(P,W) → accion_candidata(P, reasignar) )
```

Las dos cláusulas de `tipo_compatible/2` equivalen a una disyunción:
`∀P ∀V ((tipo_carga(P, general) ∧ vehiculo(V)) ∨ (tipo_carga(P, refrigerada) ∧ tipo_vehiculo(V, furgon_refrigerado)) → tipo_compatible(P, V))`.

**Atención:** el `¬` de la tercera fórmula se implementa con `\+`, que **no** es la negación
lógica: `\+ vehiculo_apto(P, V)` significa "no se pudo demostrar que V sea apto con los hechos
disponibles". Por eso los datos vacíos se marcan con `desconocido/2` (§8).

## 11. Derivación completa de una decisión encadenada: pedido p90

Hechos de p90 (en `prolog/hechos.pl`): carga refrigerada de 900 kg con destino al centro,
urgencia media, ruta despejada. Asignado: `v900`, un camión operativo de 8000 kg. Alternativos:
`v901`, furgón refrigerado de 3000 kg **con combustible bajo**, y `v902`, furgón refrigerado
de 3000 kg operativo.

Consulta: `?- decidir(p90, Accion, J).`

**Paso 1.** La consulta unifica con la cabeza `decidir(P, Accion, Justificacion)` con la
sustitución **{P/p90}**. Se demuestra `pedido(p90)` (hecho) y se buscan todas las
`accion_candidata(p90, A)`.

**Paso 2.** Prolog prueba las cláusulas de `accion_candidata/2` en orden:

| Cláusula | Qué pasa | Resultado |
|---|---|---|
| `inspeccionar` (contradicción) | `vehiculo_relevante` recorre v900, v901 y v902; ninguno está disponible y en mantención a la vez, ninguno supera su capacidad máxima, y 900 > 0 | falla |
| `inspeccionar` (dato faltante) | no hay hechos `desconocido(_, _)` | falla |
| `alertar` (dos cláusulas) | `urgencia(p90, alta)` no unifica con `urgencia(p90, media)` | falla |
| `reasignar` | ver paso 3 | **éxito** |
| `despachar` | exige `vehiculo_apto(p90, v900)`, que falla (paso 3) | falla |
| `esperar` (tres cláusulas) | la 1.ª exige que v900 sea apto; la 2.ª, `ruta_despejada(p90, no)`; la 3.ª, que no haya alternativo apto, pero v902 lo es | falla |

**Paso 3: la cláusula de `reasignar`.**

```prolog
accion_candidata(P, reasignar) :- asignado(P, V), \+ vehiculo_apto(P, V), alternativa_apta(P, _).
```

1. `asignado(p90, V)` unifica con el hecho `asignado(p90, v900)`: **{V/v900}**.
2. `\+ vehiculo_apto(p90, v900)`: Prolog intenta demostrar `vehiculo_apto(p90, v900)`:
   - `operativo(v900)`: los cuatro hechos se cumplen ✓
   - `tiene_capacidad(p90, v900)`: `carga_kg(p90, 900)`, `capacidad_kg(v900, 8000)`, `900 =< 8000` ✓
   - `tipo_compatible(p90, v900)`: la 1.ª cláusula exige `tipo_carga(p90, general)`, que no unifica
     (la carga es refrigerada); la 2.ª exige `tipo_vehiculo(v900, furgon_refrigerado)`, pero v900 es
     camión ✗. **Falla**, y Prolog ya no evalúa `puede_ingresar` (que también fallaría, porque
     los camiones no entran al centro).

   Como `vehiculo_apto(p90, v900)` no se pudo demostrar, `\+ vehiculo_apto(p90, v900)` **tiene éxito**
   (negación por falla).
3. `alternativa_apta(p90, _)` → `alternativo(p90, W)`, `vehiculo_apto(p90, W)`:
   - El primer hecho `alternativo(p90, v901)` da **{W/v901}**. En `operativo(v901)`,
     `combustible(v901, suficiente)` no unifica con `combustible(v901, bajo)` ✗.
     **Retroceso**: Prolog deshace W = v901 y busca otro hecho `alternativo(p90, W)`.
   - El segundo hecho da **{W/v902}**: `operativo(v902)` ✓; `900 =< 3000` ✓;
     `tipo_compatible`: 2.ª cláusula, `tipo_vehiculo(v902, furgon_refrigerado)` ✓;
     `puede_ingresar`: `destino(p90, centro)`, `tipo_vehiculo(v902, furgon_refrigerado)` y
     `\+ zona_restringida(centro, furgon_refrigerado)` ✓ (solo los camiones están restringidos).
   - `vehiculo_apto(p90, v902)` ✓, así que `alternativa_apta(p90, v902)` ✓.

La cláusula de `reasignar` tiene éxito.

**Paso 4.** La única candidata es `reasignar` (prioridad 3), así que `decidir/3` responde
**Accion = reasignar**. La justificación es el árbol de esa prueba (`?- porque(p90, reasignar).`):

```
accion_candidata(p90,reasignar)   <- regla
    asignado(p90,v900)   <- hecho
    no se puede demostrar vehiculo_apto(p90,v900)   <- negación por falla (falla: tipo_compatible(p90,v900))
    alternativa_apta(p90,v902)   <- regla
        alternativo(p90,v902)   <- hecho
        vehiculo_apto(p90,v902)   <- regla
            operativo(v902)   <- regla
                disponible(v902,si)   <- hecho
                en_mantencion(v902,no)   <- hecho
                combustible(v902,suficiente)   <- hecho
                conductor_disponible(v902,si)   <- hecho
            tiene_capacidad(p90,v902)   <- regla
                carga_kg(p90,900)   <- hecho
                capacidad_kg(v902,3000)   <- hecho
                900=<3000   <- cálculo
            tipo_compatible(p90,v902)   <- regla
                tipo_carga(p90,refrigerada)   <- hecho
                tipo_vehiculo(v902,furgon_refrigerado)   <- hecho
            puede_ingresar(p90,v902)   <- regla
                destino(p90,centro)   <- hecho
                tipo_vehiculo(v902,furgon_refrigerado)   <- hecho
                no se puede demostrar zona_restringida(centro,furgon_refrigerado)   <- negación por falla
```

El árbol muestra solo la rama que tuvo éxito. El intento fallido con v901 se puede ver con
`?- por_que_no(vehiculo_apto(p90, v901)).`

## 12. Casos especiales

| Situación | Consulta | Comportamiento |
|---|---|---|
| Sin solución | `?- accion_candidata(p91, A).` | `false`: p91 no tiene vehículo asignado registrado y ninguna regla aplica |
| Sin solución → valor por defecto | `?- decidir(p91, A, J).` | `A = inspeccionar`, `J = [paso(0, sin_regla, ninguna_accion_demostrable(p91))]` |
| Caso negativo | `?- accion_candidata(p01, reasignar).` | `false`: v10 sí es apto |
| Pedido inexistente | `?- decidir(p99, A, J).` | `false`: no existe `pedido(p99)` |
| Varias soluciones | `?- decidir(P, A, _).` | una respuesta por pedido cargado |
| Varias soluciones | `?- acciones_candidatas(p92, L).` | `[inspeccionar, reasignar]`: se elige `inspeccionar` por prioridad |
| Contradicción | `?- contradiccion(P, T).` | `P = p92, T = disponible_y_en_mantencion(v920)` |
| Dato faltante | prueba `urgencia_desconocida_es_critica` en `tests/test_reglas.pl` | C01 sin urgencia → `inspeccionar` |
| Dato faltante que no importa | prueba `alternativos_desconocidos_no_importan_si_el_asignado_sirve` | C01 con alternativos `null` → sigue siendo `despachar` |

## 13. Casos de prueba de Persona 1

Archivo `casos/casos_directa_paso1.json`. Las decisiones esperadas se escribieron con el
criterio del dominio antes de ejecutar los agentes.

| Id | Categoría | Situación | Esperada |
|---|---|---|---|
| C01 | directa | urgente, camioneta lista, ruta libre | despachar |
| C02 | directa | urgente, vehículo listo, ruta cortada | alertar |
| C03 | directa | sin urgencia, ruta cortada | esperar |
| C04 | directa | asignado en el taller, alternativo listo | reasignar |
| C05 | un_paso | 1200 kg en camioneta de 1000 kg; furgón alternativo | reasignar |
| C06 | un_paso | carga refrigerada en furgón común, sin alternativos, urgente | alertar |
| C07 | un_paso | sin urgencia, 90 % de la capacidad | despachar |
| C08 | un_paso | sin urgencia, 13 % de la capacidad | esperar |

`swipl prolog/verificar_casos.pl` → Prolog coincide en 8 de 8.

## 14. Cómo modificar el modelo en vivo

| Qué piden | Dónde se cambia |
|---|---|
| Un caso nuevo | un JSON con el estado → `swipl prolog/ejecutar.pl nuevo.json --texto` |
| Cambiar un umbral o una capacidad máxima | hechos `umbral/2` o `capacidad_maxima/2` en `prolog/reglas.pl` |
| Una regla nueva | `prolog/reglas.pl`; si agrega un valor nuevo al estado, también `docs/estado_canonico.md` y avisar a Persona 2 (Laya debe recibir el mismo valor) |
| Un campo nuevo en el estado | `campos_pedido/1` o `campos_vehiculo/1` en `prolog/estado_json.pl`, `:- dynamic` en `reglas.pl`, `docs/estado_canonico.md` |
| Una acción nueva | `accion/1`, `prioridad/2` y sus reglas en `reglas.pl`; Persona 2 la agrega a la pregunta de Laya |

Después de cualquier cambio: `swipl prolog/verificar_casos.pl` y
`swipl -g run_tests -t halt tests/test_reglas.pl`.

Ejemplos probados:

1. **Cambiar el umbral de aprovechamiento a 0,95.** C07 (90 %) pasa de `despachar` a `esperar`.
2. **Nueva carga `fragil`, que solo puede ir en furgón.** Agregar la cláusula
   `tipo_compatible(P, V) :- tipo_carga(P, fragil), tipo_vehiculo(V, furgon).` C04 con
   `"tipo_carga": "fragil"` da `esperar` sin la regla (ningún vehículo es compatible) y
   `reasignar` con ella (el furgón alternativo sí lo es).
3. **Nueva contradicción: capacidad cero o negativa.** Agregar
   `contradiccion(P, capacidad_no_positiva(V)) :- vehiculo_relevante(P, V), capacidad_kg(V, K), K =< 0.`
   C01 con `"capacidad_kg": 0` en el asignado pasa a `inspeccionar`.
