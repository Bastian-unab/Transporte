"""Compara a los agentes con la decisión esperada y entre sí (lo usan el servidor y el experimento)."""

from laya_agent.agente_laya import AgenteLaya
from laya_agent.agente_prolog import AgenteProlog
from laya_agent.pregunta import DIAGNOSTICO


def comparar(esperada, prolog: dict | None, laya: dict | None) -> dict:
    """Aciertos de cada agente frente a la decisión esperada y si coinciden entre sí."""
    def acierto(r):
        if not esperada or r is None or r.get("accion") is None:
            return None
        return r["accion"] == esperada

    coinciden = None
    if prolog and laya and prolog.get("accion") and laya.get("accion"):
        coinciden = prolog["accion"] == laya["accion"]
    return {"esperada": esperada, "prolog_correcto": acierto(prolog),
            "laya_correcto": acierto(laya), "coinciden": coinciden}


def comparar_diagnostico(estado: dict, prolog: dict, laya: dict) -> dict:
    """Cada pregunta de diagnóstico de Laya frente al hecho o la regla de Prolog equivalente.

      urgencia        <-> urgencia/2 (hecho del estado)
      falta_dato      <-> falta_dato_critico/2 (¿hay al menos uno?)
      contradiccion   <-> contradiccion/2 (¿hay al menos una?)
      asignado_sirve  <-> vehiculo_apto/2 con el vehículo asignado
    """
    if prolog.get("error") or laya.get("error"):
        return {}
    referencia = {
        "urgencia": estado.get("urgencia"),
        "falta_dato": bool(prolog.get("faltantes")),
        "contradiccion": bool(prolog.get("contradicciones")),
        "asignado_sirve": prolog.get("asignado_apto"),
    }
    salida = {}
    for qid, info in DIAGNOSTICO.items():
        d = laya.get("diagnostico", {}).get(qid)
        ref = referencia.get(qid)
        salida[qid] = {
            "instruccion": info["pregunta"]["instructions"],
            "tipo": info["pregunta"]["type"],
            "nivel": info["nivel"],
            "prolog_predicado": info["prolog"],
            "laya": None if d is None else d["valor"],
            "laya_p_si": None if d is None else d.get("p_si"),
            "prolog": ref,
            "coincide": None if d is None or ref is None else d["valor"] == ref,
        }
    return salida


def ejecutar_ambos(estado: dict, prolog: AgenteProlog, laya: AgenteLaya,
                   esperada: str | None = None) -> dict:
    """Mismo estado para los dos agentes. Ninguno recibe la decisión esperada."""
    r_prolog = prolog.decidir(estado)
    r_laya = laya.decidir(estado)
    return {"prolog": r_prolog, "laya": r_laya,
            "comparacion": comparar(esperada, r_prolog, r_laya),
            "diagnostico": comparar_diagnostico(estado, r_prolog, r_laya)}
