# Despacho de carga con Prolog y Laya

Proyecto 2 de Fundamentos de Inteligencia Artificial. Compara dos agentes que
reciben el mismo pedido de transporte y eligen entre cinco acciones: despachar,
reasignar, esperar, inspeccionar o alertar.

## Requisitos

- Git.
- Python 3.10 o superior. El entorno usado tiene Python 3.13.14.
- SWI-Prolog en el `PATH`. Se verificó con SWI-Prolog 10.0.2.
- Conexión a internet para instalar las dependencias y descargar el modelo de
  Laya en su primera ejecución.

## Instalación en Windows

Abre PowerShell en la carpeta donde quieras clonar el proyecto.

```powershell
git clone https://github.com/Bastian-unab/Transporte.git
cd Transporte
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
swipl --version
```

Si ya tienes el repositorio clonado, entra a su carpeta y continúa desde la
creación o activación del entorno virtual.

## Ejecutar el proyecto

Ejecuta estos comandos desde la raíz del repositorio, con el entorno activado.

| Para | Comando |
|---|---|
| Abrir la interfaz | `python app/servidor.py` |
| Comparar ambos agentes en el caso C17 | `python -m laya_agent.ejecutar_caso C17` |
| Ejecutar C17 solo con Prolog | `python -m laya_agent.ejecutar_caso C17 --solo-prolog` |
| Comparar ambos agentes con un estado nuevo | `python -m laya_agent.ejecutar_caso --estado mi_estado.json` |
| Verificar los 20 casos con Prolog | `swipl prolog/verificar_casos.pl` |
| Ejecutar las pruebas de Prolog | `swipl -g run_tests -t halt tests/test_reglas.pl` |
| Ejecutar las pruebas de Python | `python -m unittest tests.test_laya -v` |

La interfaz abre en `http://localhost:8000`. Para los estados nuevos, usa el
formato descrito en [Estado canónico](docs/estado_canonico.md).

## Reproducir el experimento

```powershell
python experimento/runner.py
python experimento/metricas.py
```

El primer comando ejecuta los dos agentes y guarda sus salidas en
`experimento/resultados/resultados.json`. El segundo lee ese archivo y muestra
los aciertos totales y por categoría, los desacuerdos y las decisiones de Laya
con confianza inferior a 0,60.

En la corrida del informe se usó Laya 0.4.12, modelo `multilingual` y criterios
`v1`. Prolog acertó 20 de 20 casos y Laya acertó 4 de 20. El análisis está en
[Informe](docs/Informe.md).

## Estructura

| Carpeta | Contenido |
|---|---|
| `docs/` | Modelo del dominio, formato del estado e informe |
| `prolog/` | Hechos, reglas, consultas y carga del estado JSON |
| `laya_agent/` | Agente Laya, pregunta tipada y puente a Prolog |
| `app/` | Interfaz web local |
| `casos/` | Los 20 casos con sus decisiones esperadas |
| `experimento/` | Ejecución de ambos agentes, resultados y métricas |
| `tests/` | Pruebas de Prolog y Python |

## Limitaciones

La evaluación usa 20 casos diseñados según la política de despacho del grupo.
Las reglas de Prolog codifican esa política y los criterios `v1` de Laya
resumen las acciones. Una confianza alta de Laya puede acompañar una respuesta
incorrecta. Los casos representan escenarios simulados y la aplicación opera
con los vehículos incluidos en el estado de entrada.

## Fuentes técnicas

- [Descarga oficial de SWI-Prolog](https://www.swi-prolog.org/download/stable)
- [Laya 0.4.12 y documentación de uso](https://pypi.org/project/laya/0.4.12/)
- [Ficha del modelo Laya](https://huggingface.co/convaiinnovations/laya)