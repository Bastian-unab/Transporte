"""Convierte el estado canónico (JSON) en el texto que lee Laya.

Es una traducción mecánica, campo por campo, igual que prolog/estado_json.pl lo es para
Prolog: no calcula nada ni agrega conclusiones. No dice si la carga cabe, si el vehículo
sirve ni qué porcentaje ocupa; eso tiene que deducirlo cada agente.

Por qué texto y no el JSON crudo: Laya es un modelo de lenguaje. En el JSON los datos
negativos aparecen como `"en_mantencion": false`, y la documentación de Laya advierte que la
negación no se maneja bien; escrito como "En mantención: no", cada dato queda como una frase
corta en español, igual para todos los casos.

Un dato vacío (null) se escribe "sin dato", la misma palabra que usa la pregunta.
"""

NOMBRES = {
    "zona_norte": "zona norte", "zona_sur": "zona sur", "zona_oriente": "zona oriente",
    "zona_poniente": "zona poniente", "centro": "centro",
    "camioneta": "camioneta", "furgon": "furgón", "furgon_refrigerado": "furgón refrigerado",
    "camion": "camión", "general": "general", "refrigerada": "refrigerada",
    "alta": "alta", "media": "media", "baja": "baja",
    "suficiente": "suficiente", "bajo": "bajo",
}

SIN_DATO = "sin dato"


def _valor(v, unidad: str = "") -> str:
    if v is None:
        return SIN_DATO
    if v is True:
        return "sí"
    if v is False:
        return "no"
    if isinstance(v, (int, float)):
        return f"{v:g} {unidad}".strip()
    return NOMBRES.get(str(v), str(v).replace("_", " "))


def _vehiculo(etiqueta: str, v: dict | None) -> str:
    if v is None:
        return f"{etiqueta}: {SIN_DATO}."
    return (
        f"{etiqueta} {v.get('id', '?')}. "
        f"Tipo: {_valor(v.get('tipo_vehiculo'))}. "
        f"Capacidad: {_valor(v.get('capacidad_kg'), 'kg')}. "
        f"Disponible: {_valor(v.get('disponible'))}. "
        f"En mantención: {_valor(v.get('en_mantencion'))}. "
        f"Combustible: {_valor(v.get('combustible'))}. "
        f"Conductor disponible: {_valor(v.get('conductor_disponible'))}."
    )


def estado_a_texto(estado: dict) -> str:
    lineas = [
        f"Pedido {estado.get('pedido', '?')}. "
        f"Carga: {_valor(estado.get('carga_kg'), 'kg')}. "
        f"Tipo de carga: {_valor(estado.get('tipo_carga'))}. "
        f"Destino: {_valor(estado.get('destino'))}. "
        f"Urgencia: {_valor(estado.get('urgencia'))}. "
        f"Ruta despejada: {_valor(estado.get('ruta_despejada'))}.",
        _vehiculo("Vehículo asignado", estado.get("vehiculo_asignado")),
    ]
    alternativos = estado.get("vehiculos_alternativos")
    if alternativos is None:
        lineas.append(f"Vehículos alternativos: {SIN_DATO}.")
    elif not alternativos:
        lineas.append("Vehículos alternativos: ninguno.")
    else:
        for alt in alternativos:
            lineas.append(_vehiculo("Vehículo alternativo", alt))
    return "\n".join(lineas)
