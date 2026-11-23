"""Lectura de los 20 casos de evaluación (casos/casos.json).

Cada caso tiene: id, categoria, descripcion, estado, decision_esperada, criterio_esperada.
Los agentes reciben SOLO `estado`; la decisión esperada se usa únicamente para comparar.
"""

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO_CASOS = RAIZ / "casos" / "casos.json"

CATEGORIAS = {
    "directa": "Información directa",
    "un_paso": "Inferencia de un paso",
    "encadenada": "Inferencia encadenada",
    "incompleta": "Información incompleta",
    "contradiccion": "Contradicción o ambigüedad",
}


def cargar_casos(archivo: Path = ARCHIVO_CASOS) -> list[dict]:
    with open(archivo, encoding="utf-8") as f:
        return json.load(f)


def buscar_caso(id_caso: str, archivo: Path = ARCHIVO_CASOS) -> dict:
    for caso in cargar_casos(archivo):
        if caso["id"].upper() == id_caso.upper():
            return caso
    raise KeyError(f"No existe el caso {id_caso} en {archivo.name}")
