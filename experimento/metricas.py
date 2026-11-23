import json
from pathlib import Path


def mostrar_aciertos(nombre, casos):
    total = len(casos)
    prolog = sum(caso["comparacion"]["prolog_correcto"] is True for caso in casos)
    laya = sum(caso["comparacion"]["laya_correcto"] is True for caso in casos)

    print(
        f"{nombre}: Prolog {prolog}/{total} ({prolog / total:.0%}) | "
        f"Laya {laya}/{total} ({laya / total:.0%})"
    )


def main():
    archivo = Path(__file__).resolve().parent / "resultados" / "resultados.json"
    if not archivo.is_file():
        raise SystemExit("Primero ejecuta python experimento/runner.py")

    corrida = json.loads(archivo.read_text(encoding="utf-8"))
    casos = corrida["casos"]
    if not casos:
        raise SystemExit("La corrida guardada no contiene casos.")

    categorias = {}
    desacuerdos = []
    baja_confianza = []

    for caso in casos:
        categorias.setdefault(caso["categoria"], []).append(caso)

        if caso["comparacion"]["coinciden"] is False:
            desacuerdos.append(caso["id"])

        confianza = caso["laya"]["confianza"]
        if confianza is not None and confianza < 0.60:
            baja_confianza.append(f"{caso['id']} ({confianza:.4f})")

    print(f"Criterios de Laya: {corrida['version_criterios']}")
    print(f"Fallos de ejecución: {corrida['fallos_ejecucion']}")
    mostrar_aciertos("Total", casos)

    print("\nAciertos por categoría")
    for categoria, grupo in categorias.items():
        mostrar_aciertos(categoria, grupo)

    print(f"\nDesacuerdos ({len(desacuerdos)}): {', '.join(desacuerdos) or 'ninguno'}")
    print(f"Confianza de Laya menor a 0.60: {', '.join(baja_confianza) or 'ninguno'}")


if __name__ == "__main__":
    main()