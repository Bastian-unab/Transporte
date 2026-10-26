"""Puente Python -> Prolog (Persona 2): llama a decidir/3 de Persona 1 sin conocer las reglas.

Ejecuta  swipl prolog/ejecutar.pl estado.json  y devuelve un dict con el mismo formato
que ejecutar_laya(), para que el front y el runner traten a ambos agentes igual.
"""

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from laya_agent.casos import RAIZ

EJECUTAR_PL = RAIZ / "prolog" / "ejecutar.pl"

# Rutas típicas de instalación si swipl no quedó en el PATH.
RUTAS_SWIPL = [
    r"C:\Program Files\swipl\bin\swipl.exe",
    r"C:\Program Files (x86)\swipl\bin\swipl.exe",
    "/Applications/SWI-Prolog.app/Contents/MacOS/swipl",
]


def buscar_swipl() -> str:
    """Busca swipl: variable SWIPL, luego el PATH, luego las rutas típicas."""
    candidato = os.environ.get("SWIPL") or shutil.which("swipl")
    if candidato:
        return candidato
    for ruta in RUTAS_SWIPL:
        if Path(ruta).exists():
            return ruta
    raise RuntimeError(
        "No se encontró SWI-Prolog. Instálalo desde https://www.swi-prolog.org/download/stable "
        "y marca la opción de agregarlo al PATH (o define la variable de entorno SWIPL)."
    )


def ejecutar_prolog(estado: dict) -> dict:
    """Envía el estado a Prolog y devuelve su decisión y justificación."""
    resultado = {
        "agente": "prolog",
        "accion": None,
        "candidatas": [],
        "contradicciones": [],
        "faltantes": [],
        "justificacion": [],
        "probabilidades": None,   # Prolog no da probabilidades: demuestra o no demuestra
        "confianza": None,
        "estado_enviado": estado,
        "tiempo_ms": None,
        "error": None,
    }
    inicio = time.perf_counter()
    try:
        swipl = buscar_swipl()
        with tempfile.TemporaryDirectory() as carpeta:
            archivo = Path(carpeta) / "estado.json"
            archivo.write_text(json.dumps(estado, ensure_ascii=False), encoding="utf-8")
            proceso = subprocess.run(
                [swipl, str(EJECUTAR_PL), str(archivo)],
                cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", timeout=60,
            )
        if proceso.returncode != 0 or not proceso.stdout.strip():
            raise RuntimeError((proceso.stderr or "Prolog no devolvió resultado").strip())
        salida = json.loads(proceso.stdout.strip().splitlines()[-1])
    except Exception as error:  # el error queda registrado y el resto del programa sigue
        resultado["error"] = f"{type(error).__name__}: {error}"
        return resultado
    resultado.update({
        "accion": salida["accion"],
        "candidatas": salida.get("candidatas", []),
        "contradicciones": salida.get("contradicciones", []),
        "faltantes": salida.get("faltantes", []),
        "justificacion": salida.get("justificacion", []),
        "tiempo_ms": round((time.perf_counter() - inicio) * 1000, 1),
    })
    return resultado
