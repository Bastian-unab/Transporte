"""Comparación experimental: los 20 casos en Prolog y en Laya.

Desde la carpeta raíz, con el entorno virtual activado:

    python -m experimento.ejecutar

Escribe:
    experimento/resultados.md     los 20 casos con los 7 elementos de la rúbrica + métricas
    experimento/resultados.csv    una fila por caso (para planillas o gráficos)
    experimento/resultados.json   todo el detalle (estado, derivación, probabilidades)

Las decisiones esperadas están en casos/casos.json y se escribieron ANTES de ejecutar.
"""

import csv
import json
import sys
from collections import Counter
from datetime import datetime

from laya_agent.agente_laya import AgenteLaya
from laya_agent.agente_prolog import AgenteProlog
from laya_agent.casos import CATEGORIAS, RAIZ, cargar_casos
from laya_agent.comparacion import comparar, comparar_diagnostico
from laya_agent.pregunta import ACCIONES, DIAGNOSTICO

CARPETA = RAIZ / "experimento"


def observacion(caso: dict, prolog: dict, laya: dict) -> str:
    """Nota automática sobre datos faltantes, contradicciones y comportamiento de los agentes."""
    partes = []
    if prolog["faltantes"]:
        partes.append("Falta dato crítico: " + ", ".join(prolog["faltantes"]) + ".")
    if prolog["contradicciones"]:
        partes.append("Contradicción: " + ", ".join(prolog["contradicciones"]) + ".")
    if len(prolog["candidatas"]) > 1:
        partes.append(f"Varias acciones demostrables ({', '.join(prolog['candidatas'])}); "
                      "Prolog elige por prioridad.")
    if not prolog["candidatas"]:
        partes.append("Ninguna regla aplica; Prolog inspecciona por defecto.")
    if laya.get("accion"):
        e = laya["estabilidad"]
        if laya["accion"] != caso["decision_esperada"]:
            p_esperada = laya["probabilidades"].get(caso["decision_esperada"], 0)
            partes.append(f"Laya eligió {laya['accion']} ({laya['confianza']:.2f}); "
                          f"a la esperada le dio {p_esperada:.2f}.")
        else:
            partes.append(f"Laya acierta con confianza {laya['confianza']:.2f}.")
        if e["coinciden"] < e["total"]:
            partes.append(f"La respuesta de Laya depende del orden de las alternativas "
                          f"({e['coinciden']} de {e['total']} órdenes eligen lo mismo).")
    return " ".join(partes) or "Sin datos faltantes ni contradicciones."


def metricas(filas: list[dict]) -> dict:
    n = len(filas)
    ok_p = sum(f["comparacion"]["prolog_correcto"] is True for f in filas)
    ok_l = sum(f["comparacion"]["laya_correcto"] is True for f in filas)
    acuerdo = sum(f["comparacion"]["coinciden"] is True for f in filas)

    def conf(correcto):
        v = [f["laya"]["confianza"] for f in filas
             if f["comparacion"]["laya_correcto"] is correcto and f["laya"]["confianza"] is not None]
        return round(sum(v) / len(v), 3) if v else None

    por_categoria = {}
    for clave in CATEGORIAS:
        fc = [f for f in filas if f["categoria"] == clave]
        por_categoria[clave] = {"n": len(fc),
                                "prolog": sum(f["comparacion"]["prolog_correcto"] is True for f in fc),
                                "laya": sum(f["comparacion"]["laya_correcto"] is True for f in fc)}
    confusion = {a: Counter() for a in ACCIONES}
    for f in filas:
        confusion[f["esperada"]][f["laya"]["accion"] or "error"] += 1
    diagnostico = {}
    for qid in DIAGNOSTICO:
        con = [f for f in filas if f["diagnostico"].get(qid, {}).get("coincide") is not None]
        diagnostico[qid] = {"n": len(con), "coinciden": sum(f["diagnostico"][qid]["coincide"] for f in con)}
    estables = sum(f["laya"]["estabilidad"]["coinciden"] == f["laya"]["estabilidad"]["total"] for f in filas)
    return {
        "n": n, "prolog_aciertos": ok_p, "laya_aciertos": ok_l, "acuerdo": acuerdo,
        "laya_confianza_aciertos": conf(True), "laya_confianza_errores": conf(False),
        "laya_estables": estables, "elecciones_laya": dict(Counter(f["laya"]["accion"] for f in filas)),
        "por_categoria": por_categoria, "confusion_laya": {a: dict(c) for a, c in confusion.items()},
        "diagnostico": diagnostico,
    }


def ejecutar() -> dict:
    prolog = AgenteProlog()
    laya = AgenteLaya()
    filas = []

    try:
        prolog.iniciar()
        print("Cargando Laya (checkpoint multilingüe)...")
        laya.cargar()

        for caso in cargar_casos():
            estado = caso["estado"]
            esperada = caso["decision_esperada"]
            r_prolog = prolog.decidir(estado)
            r_laya = laya.decidir(estado)

            for agente, respuesta in (("Prolog", r_prolog), ("Laya", r_laya)):
                if respuesta.get("error"):
                    raise RuntimeError(f"{caso['id']} - {agente}: {respuesta['error']}")

            fila = {
                "id": caso["id"],
                "categoria": caso["categoria"],
                "descripcion": caso["descripcion"],
                "estado": estado,
                "esperada": esperada,
                "criterio": caso["criterio_esperada"],
                "prolog": r_prolog,
                "laya": r_laya,
                "comparacion": comparar(esperada, r_prolog, r_laya),
                "diagnostico": comparar_diagnostico(estado, r_prolog, r_laya),
            }
            fila["observacion"] = observacion(caso, r_prolog, r_laya)
            filas.append(fila)
            print(
                f"{caso['id']}  esperada={esperada:<13} prolog={r_prolog['accion']:<13} "
                f"laya={r_laya['accion']} ({r_laya['confianza']})"
            )

        return {
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "version_prolog": prolog.version,
            "version_laya": laya.version_laya,
            "metricas": metricas(filas),
            "casos": filas,
        }
    finally:
        prolog.cerrar()

# ---------------------------------------------------------------------- informes
def _b(v):
    return "sin dato" if v is None else ("sí" if v is True else "no" if v is False else v)


def _estado_corto(e: dict) -> str:
    def veh(v):
        if v is None:
            return "sin dato"
        return (f"{v.get('id')} {v.get('tipo_vehiculo')} {v.get('capacidad_kg')} kg, "
                f"disp={_b(v.get('disponible'))}, taller={_b(v.get('en_mantencion'))}, "
                f"comb={_b(v.get('combustible'))}, cond={_b(v.get('conductor_disponible'))}")
    alts = e.get("vehiculos_alternativos")
    alts_txt = "sin dato" if alts is None else ("ninguno" if not alts else "; ".join(veh(a) for a in alts))
    return (f"{_b(e.get('carga_kg'))} kg {_b(e.get('tipo_carga'))} → {_b(e.get('destino'))}, "
            f"urgencia {_b(e.get('urgencia'))}, ruta despejada {_b(e.get('ruta_despejada'))}. "
            f"Asignado: {veh(e.get('vehiculo_asignado'))}. Alternativos: {alts_txt}")


def _ok(v):
    return "✅" if v is True else "❌" if v is False else "—"


def escribir_markdown(res: dict, archivo) -> None:
    m = res["metricas"]
    n = m["n"]
    l = ["# Resultados del experimento: Prolog vs Laya\n",
         f"Generado por `python -m experimento.ejecutar` el {res['fecha']}. "
         f"SWI-Prolog {res['version_prolog']} · laya {res['version_laya']} (checkpoint multilingüe, "
         "sin entrenar). Las decisiones esperadas se definieron antes de ejecutar (casos/casos.json).\n",
         "## Métricas\n",
         "| Métrica | Prolog | Laya |", "|---|---|---|",
         f"| Aciertos | {m['prolog_aciertos']}/{n} | {m['laya_aciertos']}/{n} |",
         f"| Acuerdo entre agentes | — | {m['acuerdo']}/{n} |",
         f"| Confianza media de Laya cuando acierta | — | {m['laya_confianza_aciertos'] or '—'} |",
         f"| Confianza media de Laya cuando falla | — | {m['laya_confianza_errores'] or '—'} |",
         f"| Casos en que los 5 órdenes eligen lo mismo | — | {m['laya_estables']}/{n} |",
         f"| Acciones que eligió Laya | — | {', '.join(f'{a} {c}' for a, c in m['elecciones_laya'].items())} |",
         "", "Referencia: eligiendo al azar entre 5 acciones se esperan 4 aciertos de 20 (20 %).\n",
         "### Aciertos por categoría\n", "| Categoría | Prolog | Laya |", "|---|---|---|"]
    for clave, titulo in CATEGORIAS.items():
        pc = m["por_categoria"][clave]
        l.append(f"| {titulo} | {pc['prolog']}/{pc['n']} | {pc['laya']}/{pc['n']} |")
    l += ["", "### Preguntas de diagnóstico de Laya (score y noul) frente a Prolog\n",
          "| Pregunta | Tipo | Se compara con | Coinciden |", "|---|---|---|---|"]
    for qid, info in DIAGNOSTICO.items():
        d = m["diagnostico"][qid]
        l.append(f"| {info['pregunta']['instructions']} | {info['pregunta']['type']} | "
                 f"`{info['prolog']}` | {d['coinciden']}/{d['n']} |")
    l += ["", "### Matriz de confusión de Laya (filas: esperada · columnas: elegida)\n",
          "| esperada \\ elegida | " + " | ".join(ACCIONES) + " |", "|---|" + "---|" * len(ACCIONES)]
    for a in ACCIONES:
        fila = m["confusion_laya"][a]
        l.append(f"| {a} | " + " | ".join(str(fila.get(c, 0) or "·") for c in ACCIONES) + " |")
    l += ["", "## Los 20 casos\n",
          "Cada caso registra: identificador y descripción, estado común, decisión esperada y criterio, "
          "salida y justificación de Prolog, salida de Laya con probabilidades y confianza, resultado "
          "correcto o incorrecto, y observación.\n"]
    for f in res["casos"]:
        lp = f["laya"]
        probs = ", ".join(f"{a} {lp['probabilidades'].get(a, 0):.2f}" for a in ACCIONES)
        just = [s for s in f["prolog"]["justificacion"] if not s.startswith(" " * 8)]
        e = lp["estabilidad"]
        l += [f"### {f['id']} · {CATEGORIAS[f['categoria']]}\n",
              f"- **Descripción:** {f['descripcion']}",
              f"- **Estado común:** {_estado_corto(f['estado'])}",
              f"- **Esperada:** `{f['esperada']}`. Criterio: {f['criterio']}",
              f"- **Prolog:** `{f['prolog']['accion']}` {_ok(f['comparacion']['prolog_correcto'])} · "
              f"candidatas: {', '.join(f['prolog']['candidatas']) or 'ninguna'}",
              "  ```\n  " + "\n  ".join(just[:12]) + "\n  ```",
              f"- **Laya:** `{lp['accion']}` {_ok(f['comparacion']['laya_correcto'])} · confianza "
              f"{lp['confianza']} · margen {lp['margen']} · estabilidad {e['coinciden']}/{e['total']} · {probs}",
              f"- **Observación:** {f['observacion']}\n"]
    archivo.write_text("\n".join(l), encoding="utf-8")


def escribir_csv(res: dict, archivo) -> None:
    with open(archivo, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "categoria", "esperada", "prolog", "prolog_correcto", "laya", "laya_correcto",
                    "confianza", "margen", "estabilidad", *[f"p_{a}" for a in ACCIONES], "coinciden",
                    *[f"diag_{q}" for q in DIAGNOSTICO], "observacion"])
        for c in res["casos"]:
            lx = c["laya"]
            w.writerow([c["id"], c["categoria"], c["esperada"], c["prolog"]["accion"],
                        c["comparacion"]["prolog_correcto"], lx["accion"], c["comparacion"]["laya_correcto"],
                        lx["confianza"], lx["margen"], f"{lx['estabilidad']['coinciden']}/{lx['estabilidad']['total']}",
                        *[lx["probabilidades"].get(a) for a in ACCIONES], c["comparacion"]["coinciden"],
                        *[c["diagnostico"].get(q, {}).get("coincide") for q in DIAGNOSTICO], c["observacion"]])


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    res = ejecutar()
    (CARPETA / "resultados.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    escribir_csv(res, CARPETA / "resultados.csv")
    escribir_markdown(res, CARPETA / "resultados.md")
    m = res["metricas"]
    print(f"\nProlog {m['prolog_aciertos']}/{m['n']} · Laya {m['laya_aciertos']}/{m['n']} · "
          f"acuerdo {m['acuerdo']}/{m['n']}")
    print("Escrito: experimento/resultados.md, resultados.csv, resultados.json")


if __name__ == "__main__":
    main()
