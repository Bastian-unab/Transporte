import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from laya_agent.casos import cargar_casos
from laya_agent.ejecutar_caso import ejecutar_ambos
from laya_agent.preguntas import VERSION_POR_DEFECTO
import laya_agent.agente_laya as agente_laya

def main():
    print("Cargando modelo Laya en memoria...\n")
    agente_laya.precargar_laya()
    
    casos = cargar_casos()
    if not casos:
        print("No se encontraron casos en la carpeta 'casos/'.")
        return
        
    print(f"{'ID':<4} | {'Estado_Pedido':<14} | {'Esperada':<12} | {'Prolog (Decisión/Justificación)':<42} | {'Laya (Acción/Confianza)':<25} | {'¿Correctos? (P/L)':<17} | {'Observación (Faltante/Contradicción)'}")
    print("-" * 165)

    for caso in casos:
        id_caso = caso["id"]
        estado = caso["estado"]
        esperada = caso.get("decision_esperada", "N/A")
        
        resultado = ejecutar_ambos(estado, esperada, VERSION_POR_DEFECTO, con_prolog=True, con_laya=True)
        
        prolog_data = resultado["prolog"]
        if prolog_data and not prolog_data["error"]:
            accion_p = prolog_data["accion"]
            justif_p = prolog_data["justificacion"][-1][:30] + "..." if prolog_data["justificacion"] else "sin regla"
            obs_p = ", ".join(prolog_data["faltantes"] + prolog_data["contradicciones"]) or "Normal"
        else:
            accion_p = "ERROR"
            justif_p = prolog_data["error"][:30] if prolog_data else "Fallo puente"
            obs_p = "-"

        laya_data = resultado["laya"]
        if laya_data and not laya_data["error"]:
            accion_l = laya_data["accion"]
            confianza = f"{laya_data['confianza']:.2f}"
        else:
            accion_l = "ERROR"
            confianza = "-"

        comp = resultado["comparacion"]
        p_corr = "Sí" if comp["prolog_correcto"] else "No"
        l_corr = "Sí" if comp["laya_correcto"] else "No"

        fila = f"{id_caso:<4} | {estado.get('pedido', 'N/A'):<14} | {esperada:<12} | {accion_p:<12} (Justif: {justif_p:<17}) | {accion_l:<10} (Conf: {confianza:<4}) | {p_corr:<7} / {l_corr:<7} | {obs_p}"
        print(fila)

if __name__ == "__main__":
    main()