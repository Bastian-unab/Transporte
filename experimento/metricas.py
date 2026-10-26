import sys
import pathlib

raiz = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(raiz))

from laya_agent.casos import cargar_casos
from laya_agent.ejecutar_caso import ejecutar_ambos
import laya_agent.agente_laya as laya_mod

def main():
    '''calcula metricas de los agentes'''
    print("midiendo agentes...")
    laya_mod.precargar_laya()
    
    casos = cargar_casos()
    
    total = 0
    ok_p = 0
    ok_l = 0
    cat_p = {}
    cat_l = {}
    dif = []
    dudas = []

    for c in casos:
        total += 1
        id_c = c["id"]
        cat = c.get("categoria", "otra")
        est = c["estado"]
        esp = c.get("decision_esperada", "")
        
        if cat not in cat_p:
            cat_p[cat] = 0
            cat_l[cat] = 0

        res = ejecutar_ambos(est, esp, "v1", con_prolog=True, con_laya=True)
        
        comp = res["comparacion"]
        bien_p = comp["prolog_correcto"]
        bien_l = comp["laya_correcto"]
        
        if bien_p:
            ok_p += 1
            cat_p[cat] += 1
        
        if bien_l:
            ok_l += 1
            cat_l[cat] += 1
            
        if bien_p != bien_l:
            dif.append(id_c)
            
        laya = res["laya"]
        if laya and not laya["error"]:
            conf = laya["confianza"]
            if conf < 0.6:
                dudas.append(id_c)
                
    print("\n--- globales ---")
    print(f"total: {total}")
    print(f"prolog acierta: {ok_p}")
    print(f"laya acierta: {ok_l}")
    
    print("\n--- por categoria ---")
    for k in cat_p:
        print(f"{k} -> p: {cat_p[k]}, l: {cat_l[k]}")
        
    print("\n--- difieren ---")
    print(f"casos: {dif}")
    
    print("\n--- laya duda (< 0.6) ---")
    print(f"casos: {dudas}")

if __name__ == "__main__":
    main()