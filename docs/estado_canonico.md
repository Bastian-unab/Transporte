# Estado canónico (contrato común)

Responsable: Persona 1. **Propuesta para aprobar entre los tres.** Si cambia, se avisa al grupo.

El estado canónico es la **única entrada** de ambos agentes. Describe un pedido y los vehículos
que podrían llevarlo, en el momento en que la central debe decidir.

- No incluye la conclusión: no hay campos como `"accion"`, `"apto"` ni `"urgente"`; tampoco
  porcentajes calculados ni nada que ya resuelva la decisión.
- Prolog lo lee con `prolog/estado_json.pl`; Laya recibe el mismo JSON.
- Solo se envía el objeto `estado` de cada caso. **Nunca** se envían `decision_esperada` ni
  `criterio_esperada`.

## Casos C05

```json
{
  "pedido": "P05",
  "carga_kg": 1200,
  "tipo_carga": "general",
  "destino": "zona_norte",
  "urgencia": "media",
  "ruta_despejada": true,
  "vehiculo_asignado": {
    "id": "V50",
    "tipo_vehiculo": "camioneta",
    "capacidad_kg": 1000,
    "disponible": true,
    "en_mantencion": false,
    "combustible": "suficiente",
    "conductor_disponible": true
  },
  "vehiculos_alternativos": [
    {
      "id": "V51",
      "tipo_vehiculo": "furgon",
      "capacidad_kg": 3500,
      "disponible": true,
      "en_mantencion": false,
      "combustible": "suficiente",
      "conductor_disponible": true
    }
  ]
}
```

## Campos del pedido

| Campo | Tipo y valores permitidos | Significado | Hecho en Prolog |
|---|---|---|---|
| `pedido` | texto, p. ej. `"P05"` (obligatorio) | identificador del pedido | `pedido(p05).` |
| `carga_kg` | número | peso de la carga en kilos | `carga_kg(p05, 1200).` |
| `tipo_carga` | `general`, `refrigerada` | si la carga necesita frío | `tipo_carga(p05, general).` |
| `destino` | `centro`, `zona_norte`, `zona_sur`, `zona_oriente`, `zona_poniente` | zona de entrega | `destino(p05, zona_norte).` |
| `urgencia` | `alta`, `media`, `baja` | prioridad comercial del pedido | `urgencia(p05, media).` |
| `ruta_despejada` | `true`, `false` | si la ruta hacia el destino está transitable | `ruta_despejada(p05, si).` |
| `vehiculo_asignado` | objeto vehículo | el vehículo que propuso la planificación | `asignado(p05, v50).` + hechos del vehículo |
| `vehiculos_alternativos` | lista de objetos vehículo (puede ser `[]`) | otros vehículos libres que podrían llevar el pedido | `alternativo(p05, v51).` + hechos de cada uno |

## Campos de cada vehículo

| Campo | Tipo y valores permitidos | Significado | Hecho en Prolog |
|---|---|---|---|
| `id` | texto, p. ej. `"V50"` (obligatorio) | identificador del vehículo | `vehiculo(v50).` |
| `tipo_vehiculo` | `camioneta`, `furgon`, `furgon_refrigerado`, `camion` | tipo de vehículo | `tipo_vehiculo(v50, camioneta).` |
| `capacidad_kg` | número | carga máxima declarada en kilos | `capacidad_kg(v50, 1000).` |
| `disponible` | `true`, `false` | según el sistema de flota, no está ocupado en otro reparto | `disponible(v50, si).` |
| `en_mantencion` | `true`, `false` | según el registro del taller, está en mantención | `en_mantencion(v50, no).` |
| `combustible` | `suficiente`, `bajo` | si tiene combustible para el viaje | `combustible(v50, suficiente).` |
| `conductor_disponible` | `true`, `false` | si hay un conductor asignado y presente | `conductor_disponible(v50, si).` |

`disponible` y `en_mantencion` vienen de **dos sistemas distintos** (flota y taller). Por eso
pueden contradecirse, y esa contradicción es uno de los casos que el modelo detecta.

## Cómo se representa un dato que falta

| En el JSON | Significa | En Prolog |
|---|---|---|
| un campo con `null` (o ausente) | **no se sabe** | `desconocido(Entidad, campo).` |
| `"vehiculo_asignado": null` | no se sabe qué vehículo tiene asignado | `desconocido(p05, vehiculo_asignado).` |
| `"vehiculos_alternativos": []` | se sabe que **no hay** alternativos | ningún hecho `alternativo/2` |
| `"vehiculos_alternativos": null` | no se sabe si hay alternativos | `desconocido(p05, vehiculos_alternativos).` |

La diferencia entre `[]` y `null` importa: Prolog usa la negación por falla (lo que no puede
demostrar lo trata como falso), así que "no se sabe" tiene que quedar escrito de forma
explícita para no confundirse con "no hay".

## Regla de traducción a Prolog

Es mecánica y no agrega conclusiones:

1. Los identificadores se pasan a minúscula: `"P05"` → `p05`, `"V50"` → `v50`.
2. Cada campo con valor produce el hecho `campo(Entidad, valor)`.
3. `true` y `false` se escriben `si` y `no`.
4. Cada `null` produce `desconocido(Entidad, campo)`.

```prolog
?- [prolog/reglas, prolog/estado_json].
?- cargar_estado('mi_estado.json', P), explicar(P).
?- cargar_caso('casos/casos_directa_paso1.json', 'C05', P, Esperada).
```

## Cambios respecto del ejemplo del documento de reparto

El ejemplo inicial tenía un solo vehículo en campos planos (`vehiculo`, `tipo_vehiculo`,
`capacidad_kg`, `disponible`, `combustible`). Se propone:

| Cambio | Motivo |
|---|---|
| El vehículo pasa a un objeto `vehiculo_asignado` | La acción `reasignar` necesita comparar el asignado con **otro** vehículo; ambos se describen con los mismos campos y Prolog usa la misma regla `vehiculo_apto/2` para los dos |
| Se agrega `vehiculos_alternativos` (lista) | Sin alternativos no se puede decidir entre `reasignar`, `esperar` y `alertar` |
| Se agrega `tipo_carga` | Da una regla de compatibilidad (carga refrigerada solo en furgón refrigerado) |
| Se agrega `en_mantencion` | Segunda fuente sobre el vehículo; permite casos de contradicción con `disponible` |
| Se agrega `conductor_disponible` | El documento de reparto nombra al conductor como entidad del dominio |
| `destino` toma valores de zona, incluido `centro` | Da una restricción real: los camiones no entran al centro |

## Para el resto del grupo

**Persona 2 (Laya y front).** Laya recibe este mismo JSON (el objeto `estado`). Para obtener
la salida de Prolog desde Python:

```bash
swipl prolog/ejecutar.pl estado.json
swipl prolog/ejecutar.pl casos/casos_directa_paso1.json C05
```

Ambos imprimen una línea JSON con `pedido`, `accion`, `candidatas`, `contradicciones`,
`faltantes` y `justificacion` (lista de líneas de la derivación). Con el segundo formato se
agregan `caso` y `decision_esperada`.

**Persona 3 (experimento).** Los casos usan el formato acordado (`id`, `categoria`,
`descripcion`, `estado`, `decision_esperada`, `criterio_esperada`). Propuesta de valores para
`categoria`: `directa`, `un_paso`, `encadenada`, `incompleta`, `contradiccion`. Propuesta de
rangos de `id`: C01–C08 Persona 1, C09–C16 Persona 2, C17–C20 Persona 3.
`swipl prolog/verificar_casos.pl` ejecuta Prolog sobre todos los archivos de `casos/`.
