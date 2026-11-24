# Despacho de carga con Prolog y Laya

Proyecto 2 de Fundamentos de Inteligencia Artificial, Universidad Andrés Bello.

El proyecto compara dos agentes que reciben el mismo estado de un pedido de
transporte y eligen entre cinco acciones: `despachar`, `reasignar`, `esperar`,
`inspeccionar` y `alertar`. Prolog decide mediante reglas y muestra cómo llegó
a su respuesta. Laya elige una acción y devuelve las probabilidades de las
alternativas.

## Requisitos

- Git para clonar el repositorio.
- Python 3.10 o superior.
- SWI-Prolog disponible en el `PATH`. El proyecto se probó con la versión 10.0.2.
- Conexión a internet para instalar las dependencias y descargar el modelo
  multilingüe en la primera ejecución.
- Laya 0.5.0, fijado en `requirements.txt`.

## Instalación en Windows

Abre PowerShell y clona el repositorio:

```powershell
git clone https://github.com/Bastian-unab/Transporte.git
cd Transporte
```

Si ya tienes el repositorio, abre PowerShell en la carpeta `Transporte` y
asegúrate de estar en `main`.

Para crear el entorno e instalar las dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
swipl --version
```

Los comandos siguientes usan directamente el Python de `.venv`, así que no
hace falta activarlo. Si ya tienes un entorno activo con las dependencias
instaladas, puedes usar `python` en su lugar.

## Abrir la interfaz

```powershell
.\.venv\Scripts\python.exe app\servidor.py --puerto 8080
```

Abre [http://127.0.0.1:8080](http://127.0.0.1:8080) y deja la terminal abierta
mientras usas la página.

Puedes seleccionar un caso guardado, como C17, o ingresar un estado nuevo.
El botón **Ejecutar ambos agentes** muestra la decisión y la justificación
de Prolog, las probabilidades de Laya y la comparación entre ambos. La pestaña
**Experimento · 20 casos** permite ejecutar la evaluación completa.

El formato de entrada está descrito en [Estado canónico](docs/estado_canonico.md).

## Verificar los casos y ejecutar las pruebas

```powershell
swipl prolog/verificar_casos.pl
swipl -g run_tests -t halt tests/test_reglas.pl
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

El primer comando verifica que las decisiones de Prolog coincidan con las
esperadas en los 20 casos de `casos/casos.json`. El conjunto tiene cuatro casos
por categoría: información directa, inferencia de un paso, inferencia
encadenada, información incompleta y contradicción o ambigüedad.

Las pruebas unitarias del agente Laya usan un simulador. Para probar el modelo
real, hay que ejecutar el experimento.

## Reproducir el experimento

```powershell
.\.venv\Scripts\python.exe -m experimento.ejecutar
```

El comando ejecuta ambos agentes sobre los 20 casos, calcula las métricas y
guarda estos archivos:

| Archivo | Contenido |
|---|---|
| [resultados.json](experimento/resultados.json) | Estados, decisiones, justificaciones, probabilidades y métricas |
| [resultados.csv](experimento/resultados.csv) | Resumen de los casos en formato tabular |
| [resultados.md](experimento/resultados.md) | Resultados y métricas en Markdown |

En la corrida final, Prolog acertó **20 de 20** casos y Laya acertó
**3 de 20**. Hubo **acuerdo en 3 de 20** casos. El acierto compara cada
respuesta con la esperada. El acuerdo compara las respuestas de los dos
agentes entre sí.

## Estructura

| Ruta | Contenido |
|---|---|
| `app/` | Servidor local e interfaz web |
| `prolog/` | Hechos, reglas, consultas y ejecución del agente lógico |
| `laya_agent/` | Agente Laya, preguntas y conexión entre Python y Prolog |
| `casos/casos.json` | Los 20 casos y sus decisiones esperadas |
| `experimento/` | Ejecución, métricas y resultados |
| `tests/` | Pruebas de Prolog y Python |
| `docs/` | Modelo del problema, informe y declaración de uso de IA |

## Documentación

- [Modelo del dominio](docs/modelo_dominio.md)
- [Estado canónico](docs/estado_canonico.md)
- [Agente Laya](docs/agente_laya.md)
- [Informe del proyecto](docs/Informe.md)
- [Uso de IA y evidencias](docs/uso_ia.md)

## Alcance

Los escenarios son simulados y se evalúan según la política de despacho del
grupo. La aplicación trabaja con los vehículos incluidos en el estado de
entrada. La confianza de Laya corresponde a la probabilidad asignada a su
elección y puede ser alta incluso cuando la respuesta es incorrecta.

## Fuentes técnicas

- [SWI-Prolog](https://www.swi-prolog.org/download/stable)
- [Laya 0.5.0](https://pypi.org/project/laya/0.5.0/)
- [Modelo multilingüe de Laya](https://huggingface.co/convaiinnovations/laya)