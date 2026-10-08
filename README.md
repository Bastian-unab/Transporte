# Proyecto 2

# 1.- Requisitos
* Python 3.10 o superior
* Librería Laya (`pip install laya`)
* SWI-Prolog 9.x o superior con `swipl` en el PATH (probado con 9.0.4 y 10.1)

# 2.- instalación
* Clonar el repositorio.
* Instalar la librería Laya en la terminal: `pip install laya`

# 3.- Estructura del repositorio
* `docs/`: Documentación del modelo y estado canónico.
* `prolog/`: Base de conocimiento, hechos y reglas.
* `laya_agent/`: Script de integración con el modelo Laya.
* `casos/`: Batería de pruebas en formato JSON.
* `experimento/`: Scripts para ejecutar la comparación y obtener métricas.

# 4.- Ejecucion
python experimento/runner.py