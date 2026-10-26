"""Pregunta tipada que recibe Laya (Persona 2).

Las alternativas son las mismas cinco acciones de Prolog (accion/1 en prolog/reglas.pl),
en el mismo orden. En Laya el orden de las alternativas es parte de la pregunta, así que
no conviene cambiarlo sin anotarlo.

Hay dos versiones de las descripciones (criterios):
  v1  el texto acordado por el grupo en el documento de reparto;
  v2  descripciones más específicas, con las mismas palabras que aparecen en el estado JSON.
Cambiar de versión sirve para el experimento ("¿cambia la decisión si cambia la redacción?")
y para la modificación en vivo de la defensa.
"""

# Mismo orden que accion/1 en prolog/reglas.pl.
ACCIONES = ("despachar", "reasignar", "esperar", "inspeccionar", "alertar")

INSTRUCCION = "¿Qué acción de despacho debe ejecutarse primero para este pedido?"

CRITERIOS = {
    "v1": {
        "despachar": "hay vehículo adecuado y disponible",
        "reasignar": "el vehículo asignado no sirve, pero hay otro apto",
        "esperar": "no hay urgencia o no hay vehículo libre todavía",
        "inspeccionar": "faltan datos o hay contradicción",
        "alertar": "requiere intervención del supervisor",
    },
    "v2": {
        "despachar": "el vehículo asignado está disponible, no está en mantención, tiene "
                     "combustible suficiente y capacidad para la carga, y la ruta está despejada",
        "reasignar": "el vehículo asignado no puede llevar el pedido, pero uno de los "
                     "vehículos alternativos sí puede",
        "esperar": "la urgencia es baja y la ruta no está despejada, el vehículo iría casi "
                   "vacío o no hay vehículo libre",
        "inspeccionar": "faltan datos (valores null) o los datos se contradicen, por ejemplo "
                        "disponible y en mantención al mismo tiempo",
        "alertar": "la urgencia es alta y el pedido no puede salir: no hay vehículo apto o "
                   "la ruta no está despejada",
    },
}

VERSION_POR_DEFECTO = "v1"

for _version, _criterios in CRITERIOS.items():
    assert tuple(_criterios) == ACCIONES, f"criterios {_version}: deben ser las mismas acciones de Prolog"


def pregunta(version: str = VERSION_POR_DEFECTO) -> dict:
    """Devuelve las preguntas en el formato que espera Router.predict de Laya."""
    if version not in CRITERIOS:
        raise ValueError(f"versión desconocida {version!r}; opciones: {', '.join(CRITERIOS)}")
    return {
        "accion": {
            "type": "choice",
            "instructions": INSTRUCCION,
            "criteria": dict(CRITERIOS[version]),
        }
    }
