"""Agente Laya (Persona 2): decide con el modelo multilingüe a partir del estado canónico.

Uso desde Python:
    from laya_agent.agente_laya import ejecutar_laya
    resultado = ejecutar_laya(caso["estado"])            # criterios v1
    resultado = ejecutar_laya(caso["estado"], "v2")      # criterios v2

Uso desde la terminal (carpeta raíz del repositorio):
    python -m laya_agent.agente_laya C01            un caso
    python -m laya_agent.agente_laya --todos        todos los casos de casos/
    python -m laya_agent.agente_laya C01 --criterios v2

Cada ejecución se agrega a registros/laya.jsonl (estado enviado, pregunta, respuesta,
probabilidades y confianza).
"""

import argparse
import json
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from laya_agent.casos import RAIZ, buscar_caso, cargar_casos
from laya_agent.preguntas import ACCIONES, VERSION_POR_DEFECTO, pregunta

MODELO = "multilingual"
REGISTRO = RAIZ / "registros" / "laya.jsonl"

_router = None
_version_laya = None
_candado = threading.Lock()
estado_carga = {"listo": False, "error": None}   # lo consulta el front


def cargar_router():
    """Crea el Router de Laya una sola vez (cargar el modelo es lo que más demora)."""
    global _router, _version_laya
    with _candado:
        if _router is None:
            try:
                import laya
                from laya import Router
            except ImportError as error:
                raise RuntimeError(
                    "Laya no está instalado. Activa el entorno virtual y ejecuta: "
                    "python -m pip install -r requirements.txt"
                ) from error
            _version_laya = getattr(laya, "__version__", None)
            _router = Router(default=MODELO)
    return _router


def precargar_laya() -> None:
    """Carga el modelo antes de la primera consulta (el front lo llama al iniciar)."""
    try:
        router = cargar_router()
        if hasattr(router, "preload"):
            router.preload([MODELO])
        estado_carga.update(listo=True, error=None)
    except Exception as error:
        estado_carga.update(listo=False, error=f"{type(error).__name__}: {error}")


def ejecutar_laya(estado: dict, version: str = VERSION_POR_DEFECTO, router=None) -> dict:
    """Envía el estado y la pregunta choice a Laya y devuelve la respuesta completa.

    Laya recibe el mismo estado que Prolog (un dict: Laya lo convierte a texto JSON).
    Nunca se le envía la decisión esperada ni el criterio del caso.
    """
    preguntas = pregunta(version)
    resultado = {
        "agente": "laya",
        "accion": None,
        "probabilidades": {},
        "confianza": None,
        "concentracion": None,
        "act_probability": None,
        "justificacion": [],
        "modelo": MODELO,
        "version_laya": _version_laya,
        "version_criterios": version,
        "estado_enviado": estado,
        "pregunta": preguntas,
        "tiempo_ms": None,
        "error": None,
    }
    inicio = time.perf_counter()
    try:
        router = router or cargar_router()
        salida = router.predict(estado, preguntas, model=MODELO)
    except Exception as error:  # el error queda registrado y el resto del programa sigue
        resultado["error"] = f"{type(error).__name__}: {error}"
        return resultado
    respuesta = salida["answers"]["accion"]
    resultado.update({
        "accion": respuesta["choice"],
        # Probabilidad de cada una de las 5 acciones (suman 1).
        "probabilidades": {a: round(float(respuesta["probabilities"].get(a, 0.0)), 4) for a in ACCIONES},
        # answer_confidence = max(p): probabilidad de la acción elegida.
        "confianza": respuesta.get("answer_confidence"),
        # confidence = 1 - H(p)/log(k): qué tan concentrada está la distribución (0 a 1).
        "concentracion": respuesta.get("confidence"),
        "act_probability": (respuesta.get("action") or {}).get("act_probability"),
        "modelo": (salida.get("routing") or {}).get("model", MODELO),
        "version_laya": _version_laya,
        "tiempo_ms": round((time.perf_counter() - inicio) * 1000, 1),
    })
    return resultado


def registrar(resultado: dict, id_caso: str = "nuevo", ruta: Path = REGISTRO) -> None:
    """Agrega una línea JSON con la ejecución al registro."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    linea = {"fecha": datetime.now().isoformat(timespec="seconds"), "caso": id_caso, **resultado}
    with open(ruta, "a", encoding="utf-8") as f:
        f.write(json.dumps(linea, ensure_ascii=False) + "\n")


def mostrar(id_caso: str, esperada, resultado: dict) -> None:
    print(f"\n{id_caso}  esperada={esperada}")
    if resultado["error"]:
        print(f"  Error: {resultado['error']}")
        return
    print(f"  Laya elige: {resultado['accion']}  (confianza {resultado['confianza']}, "
          f"concentración {resultado['concentracion']}, {resultado['tiempo_ms']} ms)")
    for accion in ACCIONES:
        p = resultado["probabilidades"][accion]
        print(f"    {accion:<13}{p:6.3f}  {'#' * round(p * 30)}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Ejecuta Laya sobre uno o todos los casos")
    parser.add_argument("caso", nargs="?", help="id del caso, por ejemplo C01")
    parser.add_argument("--todos", action="store_true", help="ejecuta todos los casos de casos/")
    parser.add_argument("--criterios", default=VERSION_POR_DEFECTO, choices=("v1", "v2"))
    parser.add_argument("--no-registrar", action="store_true")
    args = parser.parse_args()

    if args.todos:
        casos = cargar_casos()
    elif args.caso:
        casos = [buscar_caso(args.caso)]
    else:
        parser.error("indica un caso (por ejemplo C01) o --todos")

    print("Cargando Laya (la primera vez descarga el modelo multilingüe; puede tardar varios minutos)...")
    registradas = 0
    for caso in casos:
        resultado = ejecutar_laya(caso["estado"], args.criterios)
        mostrar(caso["id"], caso.get("decision_esperada"), resultado)
        if not args.no_registrar and not resultado["error"]:
            registrar(resultado, caso["id"])
            registradas += 1
    if registradas:
        print(f"\n{registradas} ejecuciones guardadas en {REGISTRO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
