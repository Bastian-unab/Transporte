"""Las preguntas tipadas que recibe Laya.

1. La DECISIÓN: una pregunta `choice` con las mismas cinco acciones de Prolog (accion/1 en
   prolog/reglas.pl), en el mismo orden. Cada descripción resume la regla de Prolog que lleva a
   esa acción: es el conocimiento que se conserva al pasar de un agente al otro.

2. ROTACIÓN DEL ORDEN de las alternativas. La documentación de Laya muestra que el checkpoint
   tiene un sesgo de posición: el lugar que ocupa una alternativa cambia la respuesta aunque el
   texto sea el mismo. La solución que propone es preguntar lo mismo con las alternativas
   rotadas (cada una pasa por cada lugar) y promediar las probabilidades. Las cinco rotaciones
   van en la misma llamada (una sola pasada del modelo). No es entrenar: el modelo no cambia.

3. PREGUNTAS DE DIAGNÓSTICO (`score` y `noul`). No deciden nada: se comparan con el hecho o la
   regla de Prolog equivalente para ver en qué nivel acierta o falla Laya (leer un dato directo,
   detectar un dato faltante o una contradicción, inferir si el vehículo sirve).

Si se agrega o cambia una acción, hay que cambiarla también en prolog/reglas.pl
(accion/1, prioridad/2 y sus reglas). tests/test_agentes.py revisa que coincidan.
"""

ACCIONES = ("despachar", "reasignar", "esperar", "inspeccionar", "alertar")

INSTRUCCION = "¿Qué acción debe ejecutar primero la central de despacho con este pedido?"

CRITERIOS = {
    "despachar": "el vehículo asignado sirve (disponible, fuera del taller, con combustible, "
                 "con conductor, con capacidad para la carga, compatible con el tipo de carga y "
                 "con permiso para entrar al destino), la ruta está despejada y conviene salir ya",
    "reasignar": "el vehículo asignado no sirve para este pedido, pero uno de los vehículos "
                 "alternativos sí sirve",
    "esperar": "el pedido no es urgente y todavía no puede o no conviene salir: la ruta está "
               "cortada, ningún vehículo sirve o el vehículo iría casi vacío",
    "inspeccionar": "falta un dato necesario (sin dato) o los datos se contradicen, por ejemplo "
                    "disponible y en mantención a la vez, o una capacidad imposible",
    "alertar": "el pedido es urgente y no puede salir: ningún vehículo sirve o la ruta está cortada",
}

assert tuple(CRITERIOS) == ACCIONES, "los criterios deben tener las mismas acciones que Prolog"

# Preguntas de diagnóstico: id -> (pregunta de Laya, con qué se compara en Prolog)
DIAGNOSTICO = {
    "urgencia": {
        "pregunta": {"type": "score", "instructions": "¿Qué urgencia tiene el pedido?",
                     "criteria": ["urgencia baja", "urgencia media", "urgencia alta"]},
        "prolog": "urgencia/2 (hecho del estado)",
        "nivel": "información directa",
    },
    "falta_dato": {
        "pregunta": {"type": "noul",
                     "instructions": "¿Falta algún dato necesario para decidir (aparece sin dato)?"},
        "prolog": "falta_dato_critico/2",
        "nivel": "información incompleta",
    },
    "contradiccion": {
        "pregunta": {"type": "noul",
                     "instructions": "¿Hay datos que se contradicen, como un vehículo disponible y "
                                     "en mantención a la vez o una capacidad imposible para su tipo?"},
        "prolog": "contradiccion/2",
        "nivel": "contradicción",
    },
    "asignado_sirve": {
        "pregunta": {"type": "noul",
                     "instructions": "¿El vehículo asignado puede llevar este pedido (disponible, fuera "
                                     "del taller, con combustible, con conductor, con capacidad "
                                     "suficiente y compatible con la carga y el destino)?"},
        "prolog": "vehiculo_apto/2 con el vehículo asignado",
        "nivel": "inferencia encadenada",
    },
}

NIVELES_URGENCIA = ("baja", "media", "alta")


def pregunta_decision() -> dict:
    """La pregunta choice tal como se define (sin rotar)."""
    return {"type": "choice", "instructions": INSTRUCCION, "criteria": dict(CRITERIOS)}


def rotaciones() -> dict:
    """La misma pregunta k veces, cada una con las alternativas en otro orden.

    option_order[s] = índice de la alternativa que va en el lugar s. Con k rotaciones cada
    alternativa ocupa cada lugar exactamente una vez. Laya devuelve las probabilidades con las
    claves originales, sin importar el orden en que las mostró.
    """
    k = len(ACCIONES)
    return {f"accion_r{r}": dict(pregunta_decision(), option_order=[(i + r) % k for i in range(k)])
            for r in range(k)}


def preguntas() -> dict:
    """Todo lo que se envía a Laya en UNA llamada: las rotaciones y el diagnóstico."""
    q = rotaciones()
    q.update({qid: d["pregunta"] for qid, d in DIAGNOSTICO.items()})
    return q
