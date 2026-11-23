"""Genera el CONJUNTO DE DESARROLLO: estados sintéticos para diseñar la pregunta de Laya.

Laya NO se entrena (no se cambian sus pesos). Pero la pregunta (instrucción, descripciones,
orden de las alternativas, formato del estado) sí hay que diseñarla, y diseñarla mirando los
20 casos de evaluación sería hacer trampa: la pregunta quedaría ajustada a esos 20 casos.

Por eso se generan estados nuevos con los mismos campos del estado canónico y se etiquetan con
la política de la central (las reglas de Prolog). Sirven solo para COMPARAR diseños de pregunta
(experimento/disenio_pregunta.py). Los 20 casos se miden una vez, al final.

Cómo se arma un estado:
  1. un pedido al azar (carga, tipo de carga, destino, urgencia, ruta);
  2. un vehículo asignado que sirve o que falla por UNA razón (capacidad, refrigeración,
     zona restringida, taller, ocupado, combustible, conductor);
  3. de 0 a 3 alternativos, cada uno apto o con alguna falla;
  4. a veces se borra un dato (null) o se introduce una contradicción.
Después Prolog decide, y se toma la misma cantidad de estados por acción.
Se descartan los estados iguales a un caso de evaluación (comparando todo menos los ids).

    python -m laya_agent.generador          escribe experimento/desarrollo.jsonl (40 por acción)
"""

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

from laya_agent.agente_prolog import AgenteProlog
from laya_agent.casos import RAIZ, cargar_casos
from laya_agent.pregunta import ACCIONES

ARCHIVO_DESARROLLO = RAIZ / "experimento" / "desarrollo.jsonl"

ZONAS = ["centro", "zona_norte", "zona_sur", "zona_oriente", "zona_poniente"]
TIPOS = ["camioneta", "furgon", "furgon_refrigerado", "camion"]
RANGO_CAPACIDAD = {"camioneta": (600, 1500), "furgon": (1500, 3500),
                   "furgon_refrigerado": (1000, 3000), "camion": (5000, 12000)}
CAPACIDAD_MAXIMA = {"camioneta": 1500, "furgon": 3500, "furgon_refrigerado": 3000, "camion": 12000}
CAMPOS_PEDIDO = ["carga_kg", "tipo_carga", "destino", "urgencia", "ruta_despejada"]
CAMPOS_VEHICULO = ["tipo_vehiculo", "capacidad_kg", "disponible", "en_mantencion",
                   "combustible", "conductor_disponible"]
FALLAS = ["capacidad", "refrigeracion", "zona", "taller", "ocupado", "combustible", "conductor"]


def _redondear(x: float, paso: int = 50) -> int:
    return max(paso, int(round(x / paso)) * paso)


def firma(estado: dict) -> str:
    """El estado sin identificadores, para detectar duplicados."""
    def sin_id(v):
        return None if v is None else {k: x for k, x in v.items() if k != "id"}
    e = {k: v for k, v in estado.items() if k != "pedido"}
    e["vehiculo_asignado"] = sin_id(e.get("vehiculo_asignado"))
    alts = e.get("vehiculos_alternativos")
    e["vehiculos_alternativos"] = None if alts is None else [sin_id(a) for a in alts]
    return json.dumps(e, sort_keys=True, ensure_ascii=False)


class Generador:
    def __init__(self, semilla: int):
        self.r = random.Random(semilla)
        self.usados = set()

    def _id(self, letra: str) -> str:
        """Identificador al azar, distinto de los demás del MISMO estado (si dos vehículos
        de un caso tuvieran el mismo id, Prolog mezclaría sus hechos)."""
        while True:
            nuevo = f"{letra}{self.r.randint(100, 9999)}"
            if nuevo not in self.usados:
                self.usados.add(nuevo)
                return nuevo

    # ---- pedido ----------------------------------------------------------
    def pedido(self) -> dict:
        r = self.r
        tipo_carga = "refrigerada" if r.random() < 0.25 else "general"
        tope = 2900 if tipo_carga == "refrigerada" else 9000
        carga = _redondear(min(tope, 100 * (60 ** r.random())))   # entre 100 y ~6000, más chicas
        return {
            "pedido": self._id("P"),
            "carga_kg": carga,
            "tipo_carga": tipo_carga,
            "destino": r.choice(ZONAS),
            "urgencia": r.choice(["alta", "media", "baja"]),
            "ruta_despejada": r.random() > 0.2,
        }

    # ---- vehículos -------------------------------------------------------
    def _base(self, tipo: str, capacidad: int) -> dict:
        return {"id": self._id("V"), "tipo_vehiculo": tipo, "capacidad_kg": capacidad,
                "disponible": True, "en_mantencion": False, "combustible": "suficiente",
                "conductor_disponible": True}

    def vehiculo_apto(self, p: dict) -> dict:
        r = self.r
        carga = p["carga_kg"]
        if p["tipo_carga"] == "refrigerada":
            posibles = ["furgon_refrigerado"]
        else:
            posibles = [t for t in TIPOS if not (p["destino"] == "centro" and t == "camion")]
        posibles = [t for t in posibles if CAPACIDAD_MAXIMA[t] >= carga] or ["furgon_refrigerado"]
        tipo = r.choice(posibles)
        minimo, maximo = RANGO_CAPACIDAD[tipo]
        # Aprovechamiento entre 5 % y 100 %, con más estados cerca del umbral de 80 %: son los
        # casos difíciles, donde la decisión depende de una cuenta (carga / capacidad).
        uso = r.choice([r.uniform(0.05, 1.0), r.uniform(0.6, 1.0), r.uniform(0.72, 0.88)])
        capacidad = _redondear(carga / uso)
        capacidad = max(carga, minimo, min(capacidad, maximo))
        capacidad = min(_redondear(capacidad, 50), maximo)
        if capacidad < carga:           # carga mayor que el máximo del tipo: va justo
            capacidad = carga
        return self._base(tipo, capacidad)

    def vehiculo_con_falla(self, p: dict, falla: str) -> dict:
        r = self.r
        carga = p["carga_kg"]
        if falla == "capacidad":
            tipos = [t for t in TIPOS if RANGO_CAPACIDAD[t][0] < carga]
            if not tipos:
                return self.vehiculo_con_falla(p, "combustible")
            tipo = r.choice(tipos)
            minimo, maximo = RANGO_CAPACIDAD[tipo]
            capacidad = _redondear(r.uniform(minimo, min(maximo, carga - 50)))
            if capacidad >= carga:
                capacidad = carga - 50
            return self._base(tipo, max(50, capacidad))
        if falla == "refrigeracion":
            if p["tipo_carga"] != "refrigerada":
                return self.vehiculo_con_falla(p, "taller")
            tipo = r.choice(["camioneta", "furgon", "camion"])
            minimo, maximo = RANGO_CAPACIDAD[tipo]
            return self._base(tipo, _redondear(r.uniform(max(minimo, carga), maximo)))
        if falla == "zona":
            if p["destino"] != "centro":
                return self.vehiculo_con_falla(p, "ocupado")
            return self._base("camion", _redondear(r.uniform(max(5000, carga), 12000)))
        v = self.vehiculo_apto(p)
        if falla == "taller":
            v["disponible"], v["en_mantencion"] = False, True
        elif falla == "ocupado":
            v["disponible"] = False
        elif falla == "combustible":
            v["combustible"] = "bajo"
        elif falla == "conductor":
            v["conductor_disponible"] = False
        return v

    def vehiculo(self, p: dict, prob_apto: float) -> dict:
        if self.r.random() < prob_apto:
            return self.vehiculo_apto(p)
        return self.vehiculo_con_falla(p, self.r.choice(FALLAS))

    # ---- estado completo -------------------------------------------------
    def estado(self) -> dict:
        r = self.r
        self.usados = set()          # los ids solo tienen que ser únicos dentro del estado
        e = self.pedido()
        e["vehiculo_asignado"] = self.vehiculo(e, prob_apto=0.45)
        n_alt = r.choices([0, 1, 2, 3], weights=[3, 4, 2, 1])[0]
        e["vehiculos_alternativos"] = [self.vehiculo(e, prob_apto=0.5) for _ in range(n_alt)]

        sorteo = r.random()
        if sorteo < 0.14:
            self._borrar_dato(e)
        elif sorteo < 0.24:
            self._contradiccion(e)
        return e

    def _borrar_dato(self, e: dict) -> None:
        r = self.r
        donde = r.choice(["pedido", "asignado", "asignado", "alternativo", "lista"])
        if donde == "pedido":
            e[r.choice(CAMPOS_PEDIDO)] = None
        elif donde == "asignado":
            e["vehiculo_asignado"][r.choice(CAMPOS_VEHICULO)] = None
        elif donde == "alternativo" and e["vehiculos_alternativos"]:
            r.choice(e["vehiculos_alternativos"])[r.choice(CAMPOS_VEHICULO)] = None
        else:
            e["vehiculos_alternativos"] = None

    def _contradiccion(self, e: dict) -> None:
        r = self.r
        # La capacidad imposible pesa más: es la contradicción que exige saber el máximo por tipo.
        tipo = r.choice(["disponible_y_mantencion", "disponible_y_mantencion",
                         "capacidad_imposible", "capacidad_imposible", "capacidad_imposible",
                         "carga_no_positiva"])
        vehiculos = [e["vehiculo_asignado"]] + (e["vehiculos_alternativos"] or [])
        v = r.choice(vehiculos) if r.random() < 0.3 else e["vehiculo_asignado"]
        if tipo == "disponible_y_mantencion":
            v["disponible"], v["en_mantencion"] = True, True
        elif tipo == "capacidad_imposible":
            v["capacidad_kg"] = _redondear(CAPACIDAD_MAXIMA[v["tipo_vehiculo"]] * r.uniform(1.15, 6))
        else:
            e["carga_kg"] = r.choice([0, 0, -100, -500])


def generar(n_por_accion: int, semilla: int, prolog: AgenteProlog,
            excluir: set[str], max_intentos: int = 200_000) -> list[dict]:
    """Estados etiquetados por Prolog, con n_por_accion ejemplos de cada acción."""
    gen = Generador(semilla)
    por_accion = {a: [] for a in ACCIONES}
    vistos = set(excluir)
    for _ in range(max_intentos):
        if all(len(v) >= n_por_accion for v in por_accion.values()):
            break
        estado = gen.estado()
        f = firma(estado)
        if f in vistos:
            continue
        vistos.add(f)
        r = prolog.decidir(estado)
        if r["error"]:
            raise RuntimeError(f"Prolog falló al etiquetar: {r['error']}")
        accion = r["accion"]
        if len(por_accion[accion]) < n_por_accion:
            por_accion[accion].append({"estado": estado, "accion": accion,
                                       "candidatas": r["candidatas"]})
    faltan = {a: n_por_accion - len(v) for a, v in por_accion.items() if len(v) < n_por_accion}
    if faltan:
        raise RuntimeError(f"No se alcanzaron los ejemplos pedidos: faltan {faltan}")
    filas = [fila for a in ACCIONES for fila in por_accion[a]]
    random.Random(semilla).shuffle(filas)
    return filas


def guardar(filas: list[dict], archivo: Path) -> None:
    archivo.parent.mkdir(parents=True, exist_ok=True)
    with open(archivo, "w", encoding="utf-8") as f:
        for fila in filas:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")


def leer(archivo: Path) -> list[dict]:
    with open(archivo, encoding="utf-8") as f:
        return [json.loads(linea) for linea in f if linea.strip()]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Genera el conjunto de desarrollo")
    parser.add_argument("--por-accion", type=int, default=40, help="estados por acción")
    parser.add_argument("--semilla", type=int, default=2026)
    args = parser.parse_args()

    prolog = AgenteProlog()
    prueba = {firma(c["estado"]) for c in cargar_casos()}
    filas = generar(args.por_accion, args.semilla, prolog, excluir=prueba)
    prolog.cerrar()
    guardar(filas, ARCHIVO_DESARROLLO)
    print(f"desarrollo: {len(filas)} estados  {dict(Counter(f['accion'] for f in filas))}")
    print(f"Guardado en {ARCHIVO_DESARROLLO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
