"""Ejecuta un caso en Prolog y en Laya y los compara (Persona 2).

Desde la carpeta raíz del repositorio:
    python -m laya_agent.ejecutar_caso C09
    python -m laya_agent.ejecutar_caso C09 --criterios v2
    python -m laya_agent.ejecutar_caso C09 --solo-prolog
    python -m laya_agent.ejecutar_caso --estado mi_estado.json
"""

import argparse
import json
import sys

from laya_agent.agente_laya import ejecutar_laya, registrar
from laya_agent.agente_prolog import ejecutar_prolog
from laya_agent.casos import buscar_caso
from laya_agent.preguntas import ACCIONES, VERSION_POR_DEFECTO


def comparar(esperada, prolog: dict | None, laya: dict | None) -> dict:
    """Resumen de la comparación: aciertos de cada agente y si coinciden entre sí."""
    def acierto(r):
        if esperada is None or r is None or r.get("accion") is None:
            return None
        return r["accion"] == esperada

    coinciden = None
    if prolog and laya and prolog.get("accion") and laya.get("accion"):
        coinciden = prolog["accion"] == laya["accion"]
    return {
        "esperada": esperada,
        "prolog_correcto": acierto(prolog),
        "laya_correcto": acierto(laya),
        "coinciden": coinciden,
    }


def ejecutar_ambos(estado: dict, esperada=None, version=VERSION_POR_DEFECTO,
                   con_prolog=True, con_laya=True) -> dict:
    prolog = ejecutar_prolog(estado) if con_prolog else None
    laya = ejecutar_laya(estado, version) if con_laya else None
    return {"prolog": prolog, "laya": laya, "comparacion": comparar(esperada, prolog, laya)}


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Ejecuta un caso en Prolog y Laya")
    parser.add_argument("caso", nargs="?", help="id del caso, por ejemplo C09")
    parser.add_argument("--estado", help="archivo JSON con un estado nuevo")
    parser.add_argument("--criterios", default=VERSION_POR_DEFECTO, choices=("v1", "v2"))
    parser.add_argument("--solo-prolog", action="store_true")
    parser.add_argument("--solo-laya", action="store_true")
    args = parser.parse_args()

    if args.estado:
        with open(args.estado, encoding="utf-8") as f:
            id_caso, estado, esperada = "nuevo", json.load(f), None
    elif args.caso:
        caso = buscar_caso(args.caso)
        id_caso, estado, esperada = caso["id"], caso["estado"], caso["decision_esperada"]
        print(f"{id_caso} · {caso['categoria']} · {caso['descripcion']}")
    else:
        parser.error("indica un caso (por ejemplo C09) o --estado archivo.json")

    r = ejecutar_ambos(estado, esperada, args.criterios,
                       con_prolog=not args.solo_laya, con_laya=not args.solo_prolog)

    if r["prolog"]:
        p = r["prolog"]
        print("\n--- Prolog ---")
        if p["error"]:
            print(f"Error: {p['error']}")
        else:
            print(f"Decisión: {p['accion']}   candidatas: {', '.join(p['candidatas'])}")
            if p["faltantes"]:
                print(f"Datos faltantes: {', '.join(p['faltantes'])}")
            if p["contradicciones"]:
                print(f"Contradicciones: {', '.join(p['contradicciones'])}")
            print("Justificación:")
            for linea in p["justificacion"]:
                print("  " + linea)
    if r["laya"]:
        l = r["laya"]
        print(f"\n--- Laya (criterios {l['version_criterios']}) ---")
        if l["error"]:
            print(f"Error: {l['error']}")
        else:
            print(f"Decisión: {l['accion']}   confianza {l['confianza']}   concentración {l['concentracion']}")
            for accion in ACCIONES:
                prob = l["probabilidades"][accion]
                print(f"  {accion:<13}{prob:6.3f}  {'#' * round(prob * 30)}")
            registrar(l, id_caso)
    c = r["comparacion"]
    print("\n--- Comparación ---")
    print(f"Esperada: {c['esperada']} · Prolog correcto: {c['prolog_correcto']} · "
          f"Laya correcto: {c['laya_correcto']} · Coinciden: {c['coinciden']}")


if __name__ == "__main__":
    main()
