# Despacho de carga con Prolog y Laya

Proyecto 2 de Fundamentos de Inteligencia Artificial, Universidad Andrés Bello.

Comparamos dos agentes que reciben el mismo estado de un pedido de transporte.
Ambos eligen entre cinco acciones: `despachar`, `reasignar`, `esperar`,
`inspeccionar` y `alertar`. Prolog aplica reglas y muestra la derivación de
su respuesta. Laya usa una pregunta de decisión y devuelve las probabilidades
de las acciones.

## Requisitos

- Git para clonar el repositorio.
- Python 3.10 o superior.
- SWI-Prolog disponible en el `PATH`.
- Conexión a internet para instalar las dependencias y descargar el modelo
  multilingüe en la primera ejecución.
- Laya 0.5.0, fijado en `requirements.txt`.

## Instalación en Windows

Si todavía no tienes el repositorio, clona la rama de prueba desde PowerShell.

```powershell
git clone --branch Prueba_laya https://github.com/Bastian-unab/Transporte.git
cd Transporte
```

Si ya lo tienes, abre PowerShell en la carpeta `Transporte` y asegúrate de
estar en `Prueba_laya`. Crea un entorno para esta versión e instala las
dependencias.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
swipl --version
```

Los comandos usan directamente el Python de `.venv`, por lo que puedes
ejecutarlos sin activar el entorno.

## Abrir la interfaz

```powershell
.\.venv\Scripts\python.exe app\servidor.py --puerto 8080
```

Abre [http://127.0.0.1:8080](http://127.0.0.1:8080). Puedes seleccionar un caso
guardado, como C17, o ingresar un estado nuevo. La interfaz muestra por separado
la decisión y derivación de Prolog, la distribución de probabilidades de Laya
y la comparación entre ambos.

El formato de entrada está descrito en [Estado canónico](docs/estado_canonico.md).

## Verificar los casos y ejecutar las pruebas

```powershell
swipl prolog/verificar_casos.pl
swipl -g run_tests -t halt tests/test_reglas.pl
.\.venv\Scripts\python.exe -m unittest tests.test_agentes -v
```

El primer comando verifica las decisiones esperadas de los 20 casos de
`casos/casos.json`. Hay cuatro casos por categoría: información directa,
inferencia de un paso, inferencia encadenada, información incompleta y
contradicción o ambigüedad. Las pruebas unitarias de Laya usan un simulador.
El experimento siguiente ejecuta el modelo real.

## Reproducir el experimento

```powershell
.\.venv\Scripts\python.exe -m experimento.ejecutar
```

El comando ejecuta ambos agentes sobre `casos/casos.json` y calcula las
métricas. Genera tres archivos:

| Archivo | Contenido |
|---|---|
| `experimento/resultados.json` | Estado, decisiones, derivaciones, probabilidades y métricas |
| `experimento/resultados.csv` | Resumen tabular de los casos |
| `experimento/resultados.md` | Resultados y métricas en Markdown |

La verificación de Prolog dio **20 de 20** en esta rama. El resultado de Laya
0.5.0 se registra a partir de una corrida nueva del experimento.

## Estructura

| Ruta | Contenido |
|---|---|
| `app/` | Servidor local y archivos de la interfaz en `app/static/` |
| `prolog/` | Reglas, consultas y ejecución del agente lógico |
| `laya_agent/` | Agente Laya, preguntas y puente entre Python y Prolog |
| `casos/casos.json` | Los 20 casos que usa esta versión |
| `experimento/` | Ejecución, métricas y archivos de salida |
| `tests/` | Pruebas de Prolog y Python |
| `docs/` | Modelo del dominio y documentación del proyecto |

## Alcance

Los escenarios son simulados. La aplicación evalúa los vehículos que vienen
en el estado de entrada. La confianza de Laya describe la certeza de su
elección y puede ser alta incluso cuando la respuesta es incorrecta.

## Fuentes técnicas

- [SWI-Prolog](https://www.swi-prolog.org/download/stable)
- [Laya 0.5.0](https://pypi.org/project/laya/0.5.0/)
- [Modelo multilingüe de Laya](https://huggingface.co/convaiinnovations/laya)