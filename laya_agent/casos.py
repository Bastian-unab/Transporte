"""Lectura de los casos de prueba (formato acordado con Persona 3).

Cada archivo de casos/ es una lista de objetos con:
  id, categoria, descripcion, estado, decision_esperada, criterio_esperada
"""

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_CASOS = RAIZ / "casos"


def cargar_casos(carpeta: Path = CARPETA_CASOS) -> list[dict]:
    """Todos los casos de casos/*.json, ordenados por id."""
    casos = []
    for archivo in sorted(Path(carpeta).glob("*.json")):
        with open(archivo, encoding="utf-8") as f:
            for caso in json.load(f):
                caso["archivo"] = archivo.name
                casos.append(caso)
    return sorted(casos, key=lambda c: c["id"])


def buscar_caso(id_caso: str, carpeta: Path = CARPETA_CASOS) -> dict:
    for caso in cargar_casos(carpeta):
        if caso["id"].upper() == id_caso.upper():
            return caso
    raise KeyError(f"No existe el caso {id_caso} en {carpeta}")
