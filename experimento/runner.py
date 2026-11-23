import json
import sys
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(raiz))

from laya_agent.casos import cargar_casos
from laya_agent.ejecutar_caso import ejecutar_ambos
from laya_agent.preguntas import VERSION_POR_DEFECTO


def main():
    casos = cargar_casos()
    if not casos:
        raise SystemExit("No se encontraron casos en la carpeta casos/.")

    version = VERSION_POR_DEFECTO
    resultados = []
    fallos = 0

    for caso in casos:
        salida = ejecutar_ambos(
            caso["estado"],
            caso["decision_esperada"],
            version,
            con_prolog=True,
            con_laya=True,
        )

        prolog = salida["prolog"]
        laya = salida["laya"]
        observaciones = []

        for dato in prolog.get("faltantes", []):
            observaciones.append(f"Dato faltante: {dato}")
        for dato in prolog.get("contradicciones", []):
            observaciones.append(f"Contradicción: {dato}")

        for agente, respuesta in (("Prolog", prolog), ("Laya", laya)):
            if respuesta.get("error"):
                fallos += 1
                observaciones.append(f"{agente}: {respuesta['error']}")

        if salida["comparacion"]["coinciden"] is False:
            observaciones.append("Los agentes eligieron acciones distintas.")

        resultados.append({
            "id": caso["id"],
            "categoria": caso["categoria"],
            "descripcion": caso["descripcion"],
            "estado": caso["estado"],
            "decision_esperada": caso["decision_esperada"],
            "criterio_esperada": caso["criterio_esperada"],
            **salida,
            "observaciones": observaciones,
        })

        print(
            f"{caso['id']} | Esperada: {caso['decision_esperada']} | "
            f"Prolog: {prolog['accion'] or 'ERROR'} | "
            f"Laya: {laya['accion'] or 'ERROR'}",
            flush=True,
        )

    archivo = raiz / "experimento" / "resultados" / "resultados.json"
    archivo.parent.mkdir(parents=True, exist_ok=True)
    corrida = {
        "version_criterios": version,
        "total_casos": len(resultados),
        "fallos_ejecucion": fallos,
        "casos": resultados,
    }
    archivo.write_text(
        json.dumps(corrida, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\nCasos guardados: {len(resultados)}")
    print(f"Fallos de ejecución: {fallos}")
    print(f"Archivo: {archivo}")


if __name__ == "__main__":
    main()