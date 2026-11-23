"""Agente Laya: decide con el checkpoint multilingüe, sin entrenar.

Se usa tal como indica el enunciado:
    router = Router(default="multilingual")
    router.predict(estado, preguntas, model="multilingual")

Lo que se diseñó (y se justifica en docs/agente_laya.md) es CÓMO se le pregunta:
  - el estado va como texto (laya_agent/estado_texto.py), traducido campo por campo;
  - la pregunta choice tiene las mismas cinco acciones de Prolog;
  - la pregunta se hace con las alternativas en 5 órdenes distintos y se promedian las
    probabilidades (sesgo de posición, documentado por Laya);
  - se agregan preguntas de diagnóstico score y noul, que no deciden nada.
Todo va en una sola llamada a predict. Los pesos del modelo NO se modifican.

Cada ejecución puede guardarse en registros/laya.jsonl (texto enviado, preguntas, respuesta,
probabilidades y confianza), como pide el enunciado.
"""

import json
import math
import os
import threading
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

from laya_agent.casos import RAIZ
from laya_agent.estado_texto import estado_a_texto
from laya_agent.pregunta import ACCIONES, DIAGNOSTICO, NIVELES_URGENCIA, pregunta_decision, preguntas

REGISTRO = RAIZ / "registros" / "laya.jsonl"
MODELO = "multilingual"


class AgenteLaya:
    """Carga el checkpoint una sola vez (es lo que más demora) y responde casos."""

    def __init__(self, dispositivo: str | None = None):
        # "auto": Laya usa la GPU si hay una disponible y si no la CPU. LAYA_DEVICE=cpu la fuerza.
        self.dispositivo = dispositivo or os.environ.get("LAYA_DEVICE", "auto")
        self._router = None
        self._candado = threading.Lock()
        self._candado_prediccion = threading.Lock()
        self.version_laya = None
        self.cargando = False
        self.error = None

    # ---- carga -----------------------------------------------------------
    def cargar(self) -> None:
        with self._candado:
            if self._router is not None:
                return
            self.cargando, self.error = True, None
            try:
                import laya
                self.version_laya = getattr(laya, "__version__", None)
                dispositivo = None if self.dispositivo == "auto" else self.dispositivo
                self._router = laya.Router(default=MODELO, device=dispositivo)
            except ImportError as error:
                self.error = ("Laya no está instalado. Activa el entorno virtual y ejecuta: "
                              "python -m pip install -r requirements.txt")
                raise RuntimeError(self.error) from error
            except Exception as error:
                self.error = f"{type(error).__name__}: {error}"
                raise
            finally:
                self.cargando = False

    @property
    def listo(self) -> bool:
        return self._router is not None

    # ---- decisión --------------------------------------------------------
    def decidir(self, estado: dict) -> dict:
        """Respuesta de Laya para un estado. Nunca lanza excepción: el error queda en 'error'."""
        texto = estado_a_texto(estado)
        resultado = {
            "agente": "laya", "accion": None, "probabilidades": {}, "confianza": None,
            "margen": None, "concentracion": None, "estabilidad": None, "por_orden": [],
            "diagnostico": {}, "modelo": f"laya {MODELO} (sin entrenar)",
            "version_laya": self.version_laya, "texto_enviado": texto,
            "pregunta": pregunta_decision(), "tiempo_ms": None, "error": None,
        }
        inicio = time.perf_counter()
        try:
            self.cargar()
            with self._candado_prediccion:          # un caso a la vez
                salida = self._router.predict(texto, preguntas(), model=MODELO)
            respuestas = salida["answers"]
        except Exception as error:
            resultado["error"] = f"{type(error).__name__}: {error}"
            return resultado

        resultado.update(combinar_rotaciones(respuestas))
        resultado["diagnostico"] = leer_diagnostico(respuestas)
        resultado["version_laya"] = self.version_laya
        resultado["tiempo_ms"] = round((time.perf_counter() - inicio) * 1000, 1)
        return resultado


def combinar_rotaciones(respuestas: dict) -> dict:
    """Promedia las probabilidades de las 5 rotaciones y elige la acción más probable.

    También cuenta cuántas rotaciones, por sí solas, eligieron esa misma acción (estabilidad):
    5 de 5 = la respuesta no depende del orden; 2 de 5 = depende mucho del orden.
    """
    rotaciones = [respuestas[k] for k in sorted(respuestas) if k.startswith("accion_r")]
    promedio = {a: 0.0 for a in ACCIONES}
    por_orden, votos = [], Counter()
    for r, resp in enumerate(rotaciones):
        p = resp.get("probabilities", {})
        for a in ACCIONES:
            promedio[a] += float(p.get(a, 0.0)) / len(rotaciones)
        votos[resp["choice"]] += 1
        k = len(ACCIONES)
        por_orden.append({"primera": ACCIONES[r % k], "eleccion": resp["choice"],
                          "confianza": _redondear(resp.get("answer_confidence"))})
    accion = max(promedio, key=promedio.get)
    ordenadas = sorted(promedio.values(), reverse=True)
    entropia = -sum(p * math.log(p) for p in promedio.values() if p > 0)
    return {
        "accion": accion,
        "probabilidades": {a: round(v, 4) for a, v in promedio.items()},
        # confianza = probabilidad promedio de la acción elegida
        "confianza": round(ordenadas[0], 4),
        # margen = diferencia con la segunda acción más probable
        "margen": round(ordenadas[0] - ordenadas[1], 4),
        # concentración = 1 - entropía normalizada (1: toda la probabilidad en una acción)
        "concentracion": round(1 - entropia / math.log(len(ACCIONES)), 4),
        "estabilidad": {"coinciden": votos[accion], "total": len(rotaciones), "votos": dict(votos)},
        "por_orden": por_orden,
    }


def leer_diagnostico(respuestas: dict) -> dict:
    """Respuestas de las preguntas score y noul, en un formato simple."""
    diag = {}
    for qid, info in DIAGNOSTICO.items():
        r = respuestas.get(qid)
        if r is None:
            continue
        if info["pregunta"]["type"] == "score":
            p = {k: float(v) for k, v in r.get("probabilities", {}).items()}
            nivel = int(max(p, key=p.get)) if p else None
            diag[qid] = {"tipo": "score", "valor": NIVELES_URGENCIA[nivel] if nivel is not None else None,
                         "probabilidades": {NIVELES_URGENCIA[int(k)]: round(v, 4) for k, v in p.items()},
                         "confianza": _redondear(r.get("answer_confidence"))}
        else:
            p_si = float(r.get("noul", 0.0))
            diag[qid] = {"tipo": "noul", "valor": p_si >= 0.5, "p_si": round(p_si, 4)}
    return diag


def _redondear(x):
    return None if x is None else round(float(x), 4)


def registrar(resultado: dict, id_caso: str = "nuevo", estado: dict | None = None,
              ruta: Path = REGISTRO) -> None:
    """Agrega una línea JSON con la ejecución de Laya al registro."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    linea = {"fecha": datetime.now().isoformat(timespec="seconds"), "caso": id_caso,
             "estado": estado, **resultado}
    with open(ruta, "a", encoding="utf-8") as f:
        f.write(json.dumps(linea, ensure_ascii=False) + "\n")
