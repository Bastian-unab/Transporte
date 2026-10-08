import json
import subprocess
import os

def llamar_prolog(ruta, idcaso):
    comando = ["swipl", "prolog/ejecutar.pl", ruta, idcaso]
    proceso = subprocess.run(comando, capture_output=True, text=True, check=True)
    texto = proceso.stdout.strip()
    diccionario = json.loads(texto)
    return diccionario

def llamar_laya(estado):
    falso_dict = {"accion_laya": "pendiente"}
    return falso_dict

def iniciar(ruta):
    if not os.path.exists(ruta):
        print("archivo no existe")
        return

    archivo = open(ruta, 'r', encoding='utf-8')
    casos = json.load(archivo)
    archivo.close()

    print("id | esperada | prolog | laya | estado")
    print("-" * 50)

    for caso in casos:
        idcaso = caso["id"]
        esperada = caso.get("decision_esperada", "nada")
        
        res_prolog = llamar_prolog(ruta, idcaso)
        accion_p = res_prolog.get("accion", "error")
        
        res_laya = llamar_laya(caso["estado"])
        accion_l = res_laya.get("accion_laya", "error")
        
        if accion_p == esperada:
            estatus = "bien"
        else:
            estatus = "mal"
        
        print(f"{idcaso} | {esperada} | {accion_p} | {accion_l} | {estatus}")

if __name__ == "__main__":
    iniciar("casos/casos_directa_paso1.json")
    iniciar("casos/casos_contradiccion.json")