"""Diseño de la pregunta de Laya, medido en el conjunto de desarrollo (no en los 20 casos).

Laya no se entrena: lo único que el grupo decide es CÓMO se le pregunta. Para elegir con
evidencia y sin mirar los 20 casos de evaluación, se comparan cinco diseños en 200 estados
sintéticos (experimento/desarrollo.jsonl, generado por laya_agent/generador.py):

  1. JSON crudo, alternativas en un solo orden   (lo que se usó en el avance)
  2. Texto campo por campo, un solo orden
  4. Texto + las reglas de la central como contexto (laya_agent/contexto.py)
  5. Texto + observaciones calculadas por caso (laya_agent/contexto.py)
  3. Texto campo por campo + 5 órdenes promediados (el diseño final)

También mide las preguntas de diagnóstico (score y noul) y la proporción de "sí" de cada una,
para saber si Laya realmente lee el dato o responde siempre lo mismo.

    python -m laya_agent.generador            (si no existe experimento/desarrollo.jsonl)
    python -m experimento.disenio_pregunta    escribe experimento/disenio_pregunta.md
"""

import sys
from collections import Counter
from datetime import datetime

from laya_agent.agente_laya import MODELO, AgenteLaya, combinar_rotaciones, leer_diagnostico
from laya_agent.agente_prolog import AgenteProlog
from laya_agent.casos import RAIZ
from laya_agent.comparacion import comparar_diagnostico
from laya_agent.contexto import con_observaciones, con_reglas
from laya_agent.estado_texto import estado_a_texto
from laya_agent.generador import ARCHIVO_DESARROLLO, leer
from laya_agent.pregunta import ACCIONES, DIAGNOSTICO, pregunta_decision, preguntas, rotaciones


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if not ARCHIVO_DESARROLLO.exists():
        sys.exit("Falta experimento/desarrollo.jsonl: ejecuta  python -m laya_agent.generador")
    datos = leer(ARCHIVO_DESARROLLO)
    agente = AgenteLaya()
    agente.cargar()
    router = agente._router
    prolog = AgenteProlog()

    disenos = {
        "1. JSON crudo, un orden": lambda f: router.predict(f["estado"], {"accion": pregunta_decision()}, model=MODELO),
        "2. Texto, un orden": lambda f: router.predict(estado_a_texto(f["estado"]), {"accion": pregunta_decision()}, model=MODELO),
    }
    filas = []
    for nombre, llamar in disenos.items():
        elegidas, ok, conf = Counter(), 0, []
        for f in datos:
            a = llamar(f)["answers"]["accion"]
            elegidas[a["choice"]] += 1
            ok += a["choice"] == f["accion"]
            conf.append(a["answer_confidence"])
        filas.append((nombre, ok, elegidas, sum(conf) / len(conf), None))
        print(nombre, ok, dict(elegidas), flush=True)

    # Más contexto (laya_agent/contexto.py), con los mismos 5 órdenes que el diseño final.
    con_contexto = {
        "4. Texto + reglas de la central como contexto, 5 órdenes (descartado)": con_reglas,
        "5. Texto + observaciones calculadas por caso, 5 órdenes (descartado)": con_observaciones,
    }
    for nombre, armar in con_contexto.items():
        elegidas, ok, conf = Counter(), 0, []
        for f in datos:
            r = combinar_rotaciones(router.predict(armar(f["estado"]), rotaciones(), model=MODELO)["answers"])
            elegidas[r["accion"]] += 1
            ok += r["accion"] == f["accion"]
            conf.append(r["confianza"])
        filas.append((nombre, ok, elegidas, sum(conf) / len(conf), None))
        print(nombre, ok, dict(elegidas), flush=True)

    # Diseño final: texto + 5 órdenes, con el diagnóstico en la misma llamada.
    elegidas, ok, conf, estables = Counter(), 0, [], 0
    diag_ok, diag_n, diag_si_laya, diag_si_ref = Counter(), Counter(), Counter(), Counter()
    for f in datos:
        respuestas = router.predict(estado_a_texto(f["estado"]), preguntas(), model=MODELO)["answers"]
        r = combinar_rotaciones(respuestas)
        elegidas[r["accion"]] += 1
        ok += r["accion"] == f["accion"]
        conf.append(r["confianza"])
        estables += r["estabilidad"]["coinciden"] == r["estabilidad"]["total"]
        laya = {"diagnostico": leer_diagnostico(respuestas), "error": None}
        for qid, d in comparar_diagnostico(f["estado"], prolog.decidir(f["estado"]), laya).items():
            if d["coincide"] is None:
                continue
            diag_n[qid] += 1
            diag_ok[qid] += d["coincide"]
            diag_si_laya[qid] += d["laya"] is True
            diag_si_ref[qid] += d["prolog"] is True
    nombre_final = "3. Texto, 5 órdenes promediados (final)"
    filas.append((nombre_final, ok, elegidas, sum(conf) / len(conf), estables))
    print(nombre_final, ok, dict(elegidas), flush=True)
    prolog.cerrar()

    n = len(datos)
    l = ["# Diseño de la pregunta de Laya (conjunto de desarrollo)\n",
         f"Generado por `python -m experimento.disenio_pregunta` el {datetime.now():%Y-%m-%d %H:%M}. "
         f"{n} estados sintéticos ({n // len(ACCIONES)} por acción) etiquetados con la política de la "
         "central (reglas de Prolog). **Laya no se entrena:** estos estados solo sirven para elegir cómo "
         "preguntar sin mirar los 20 casos de evaluación. Al azar se espera 20 % de aciertos.\n",
         "## Decisión (pregunta choice)\n",
         "| Diseño | Aciertos | Confianza media | Acciones que elige |", "|---|---|---|---|"]
    for nombre, ok_, eleg, c, _ in filas:
        l.append(f"| {nombre} | {ok_}/{n} ({ok_ / n:.0%}) | {c:.2f} | "
                 + ", ".join(f"{a} {eleg.get(a, 0)}" for a in ACCIONES) + " |")
    l += ["", f"Con el diseño final, en {filas[-1][4]} de {n} estados los 5 órdenes eligen la misma acción.\n",
          "## Preguntas de diagnóstico (score y noul)\n",
          "| Pregunta | Tipo | Coincide con Prolog | Laya dice \"sí\" | Respuesta correcta \"sí\" |",
          "|---|---|---|---|---|"]
    for qid, info in DIAGNOSTICO.items():
        k = diag_n[qid] or 1
        es_noul = info["pregunta"]["type"] == "noul"
        l.append(f"| {info['pregunta']['instructions']} | {info['pregunta']['type']} | "
                 f"{diag_ok[qid]}/{diag_n[qid]} ({diag_ok[qid] / k:.0%}) | "
                 + (f"{diag_si_laya[qid] / k:.0%} | {diag_si_ref[qid] / k:.0%} |" if es_noul else "— | — |"))
    l += ["", "Si Laya dice \"sí\" casi siempre, su porcentaje de coincidencia es solo la proporción de "
          "\"sí\" correctos: no está leyendo el dato. Ver la interpretación en `docs/agente_laya.md`."]
    (RAIZ / "experimento" / "disenio_pregunta.md").write_text("\n".join(l), encoding="utf-8")
    print("Escrito: experimento/disenio_pregunta.md")


if __name__ == "__main__":
    main()
