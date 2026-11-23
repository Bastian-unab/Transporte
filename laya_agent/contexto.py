"""Contexto adicional para Laya: probado en el conjunto de desarrollo y DESCARTADO.

Se probaron dos formas de darle a Laya más contexto que el estado:

1. CONTEXTO_REGLAS: el conocimiento general de la central (lo mismo que Prolog tiene en
   prolog/reglas.pl, escrito como texto). Es igual para todos los casos y no menciona nada de
   un caso concreto, así que no entrega ninguna conclusión.

2. observaciones(estado): frases calculadas para el caso ("la carga no cabe: 1200 kg de
   1000 kg, ocupa el 120 %"). No dicen qué acción tomar, pero le hacen a Laya un paso de la
   inferencia que Prolog hace solo; por eso, si se usaran, habría que declararlo.

Resultado (experimento/disenio_pregunta.md): con el checkpoint multilingüe, ninguna de las dos
mejora; con las reglas, Laya elige `esperar` en todos los estados. Laya clasifica el texto
completo: no ejecuta las reglas que lee, y el texto extra compite con los datos del caso.
Por eso el agente final NO usa este contexto. Se deja aquí para poder reproducir la prueba.
"""

from laya_agent.estado_texto import NOMBRES, estado_a_texto

CAPACIDAD_MAXIMA = {"camioneta": 1500, "furgon": 3500, "furgon_refrigerado": 3000, "camion": 12000}

CONTEXTO_REGLAS = """Reglas de la central de despacho:
- Un vehículo sirve para un pedido si está disponible, no está en mantención, tiene combustible suficiente, tiene conductor disponible, la carga cabe en su capacidad, es compatible con el tipo de carga y puede entrar a la zona de destino.
- La carga refrigerada solo puede ir en furgón refrigerado; la carga general puede ir en cualquier vehículo.
- Los camiones no pueden entrar al centro.
- Capacidad máxima real: camioneta 1500 kg, furgón 3500 kg, furgón refrigerado 3000 kg, camión 12000 kg. Una capacidad mayor es un error en los datos.
- Un vehículo disponible y en mantención al mismo tiempo es una contradicción. Una carga de 0 kg o menos es un error.
- Si falta un dato necesario (sin dato) o hay una contradicción, primero se inspecciona.
- Si el pedido es urgente y no puede salir porque la ruta está cortada o ningún vehículo sirve, se alerta al supervisor.
- Si el vehículo asignado no sirve pero un alternativo sí, se reasigna.
- Si el asignado sirve y la ruta está despejada, se despacha; pero si la urgencia es baja y la carga ocupa menos del 80 % de la capacidad, se espera para juntar más carga.
- Si el pedido no es urgente y no puede salir, se espera.
- Los datos de los alternativos solo importan si el vehículo asignado no sirve."""


def con_reglas(estado: dict) -> str:
    """Las reglas generales + el estado del caso."""
    return CONTEXTO_REGLAS + "\n\nCaso:\n" + estado_a_texto(estado)


def _observaciones_vehiculo(e: dict, v: dict | None, etiqueta: str) -> list[str]:
    if v is None:
        return []
    o = []
    carga, cap, tipo = e.get("carga_kg"), v.get("capacidad_kg"), v.get("tipo_vehiculo")
    if carga is not None and cap:
        cabe = "cabe" if carga <= cap else "no cabe"
        o.append(f"en el {etiqueta} {v.get('id')} la carga {cabe} ({carga} kg de {cap} kg, "
                 f"ocupa el {round(100 * carga / cap)} %)")
    if tipo is not None and e.get("tipo_carga") == "refrigerada":
        o.append(f"el {etiqueta} {v.get('id')} {'sí' if tipo == 'furgon_refrigerado' else 'no'} es refrigerado")
    if tipo == "camion" and e.get("destino") == "centro":
        o.append(f"el {etiqueta} {v.get('id')} es un camión y no puede entrar al centro")
    if tipo in CAPACIDAD_MAXIMA and cap is not None and cap > CAPACIDAD_MAXIMA[tipo]:
        o.append(f"la capacidad de {cap} kg del {etiqueta} {v.get('id')} supera el máximo de "
                 f"{NOMBRES.get(tipo, tipo)} ({CAPACIDAD_MAXIMA[tipo]} kg)")
    if v.get("disponible") is True and v.get("en_mantencion") is True:
        o.append(f"el {etiqueta} {v.get('id')} figura disponible y en mantención a la vez")
    return o


def con_observaciones(estado: dict) -> str:
    """El estado + observaciones calculadas para el caso (un paso de inferencia ya hecho)."""
    o = _observaciones_vehiculo(estado, estado.get("vehiculo_asignado"), "vehículo asignado")
    for alt in estado.get("vehiculos_alternativos") or []:
        o += _observaciones_vehiculo(estado, alt, "vehículo alternativo")
    texto = estado_a_texto(estado)
    return texto + ("\nObservaciones: " + "; ".join(o) + "." if o else "")
