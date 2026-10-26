# Proyecto 2: Despacho de vehículos y carga local

Este repositorio contiene la solución conjunta para comparar inferencia lógica (Prolog) y decisión estadística (Laya) en un dominio de transporte logístico.

## 1. Requisitos
- Python 3.10 o superior.
- SWI-Prolog 9.x o superior (asegurarse de que `swipl` esté agregado al PATH del sistema).
- Conexión a internet estable para la primera descarga del modelo Laya.

## 2. Instalación
Clona el repositorio en una carpeta limpia y configura el entorno virtual:
```bash
git clone <url-del-repositorio>
cd Transporte
python -m venv venv
# Activar entorno en Windows: venv\Scripts\activate
# Activar entorno en Linux/Mac: source venv/bin/activate
pip install -r requirements.txt