"""Puente Python -> Prolog.

Abre UNA vez el proceso `swipl prolog/servidor.pl` y le envía peticiones JSON por la entrada
estándar (una por línea). Así Prolog carga las reglas una sola vez y responde en milisegundos.
Si el proceso se cae (por ejemplo, una consulta llamó a halt/0), se vuelve a abrir solo.

    from laya_agent.agente_prolog import AgenteProlog
    prolog = AgenteProlog()
    prolog.decidir(estado)                          # acción + justificación
    prolog.consultar(estado, "vehiculo_apto(p05, V)")
"""

import json
import os
import shutil
import subprocess
import threading
import time
from collections import deque
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SERVIDOR_PL = RAIZ / "prolog" / "servidor.pl"

# Rutas típicas si swipl no quedó en el PATH al instalar.
RUTAS_SWIPL = [
    r"C:\Program Files\swipl\bin\swipl.exe",
    r"C:\Program Files (x86)\swipl\bin\swipl.exe",
    "/Applications/SWI-Prolog.app/Contents/MacOS/swipl",
    "/usr/bin/swipl",
    "/usr/local/bin/swipl",
]


def buscar_swipl() -> str:
    """La variable de entorno SWIPL, luego el PATH, luego las rutas típicas."""
    candidato = os.environ.get("SWIPL") or shutil.which("swipl")
    if candidato:
        return candidato
    for ruta in RUTAS_SWIPL:
        if Path(ruta).exists():
            return ruta
    raise RuntimeError(
        "No se encontró SWI-Prolog. Instálalo desde https://www.swi-prolog.org/download/stable "
        "(marca la opción de agregarlo al PATH) o define la variable de entorno SWIPL."
    )


def _version_texto(numero: int) -> str:
    return f"{numero // 10000}.{numero // 100 % 100}.{numero % 100}"


class AgenteProlog:
    def __init__(self):
        self._proceso = None
        self._candado = threading.Lock()
        self._errores = deque(maxlen=50)   # últimas líneas de la salida de error de swipl
        self.version = None
        self.ruta = None

    # ---- proceso -------------------------------------------------------
    def iniciar(self) -> None:
        with self._candado:
            self._iniciar()

    def _iniciar(self) -> None:
        self.ruta = buscar_swipl()
        opciones = {}
        if os.name == "nt":
            opciones["creationflags"] = subprocess.CREATE_NO_WINDOW
        self._proceso = subprocess.Popen(
            [self.ruta, str(SERVIDOR_PL)],
            cwd=RAIZ, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", bufsize=1, **opciones,
        )
        threading.Thread(target=self._leer_errores, args=(self._proceso,), daemon=True).start()
        saludo = self._leer_respuesta()
        self.version = _version_texto(saludo["version"])

    def _leer_errores(self, proceso) -> None:
        for linea in proceso.stderr:
            self._errores.append(linea.rstrip())

    def _leer_respuesta(self) -> dict:
        linea = self._proceso.stdout.readline()
        if not linea:
            detalle = "\n".join(list(self._errores)[-10:])
            raise RuntimeError(f"Prolog terminó sin responder.\n{detalle}".strip())
        return json.loads(linea)

    def _vivo(self) -> bool:
        return self._proceso is not None and self._proceso.poll() is None

    def _pedir(self, peticion: dict) -> dict:
        with self._candado:
            for intento in (1, 2):
                if not self._vivo():
                    self._iniciar()
                try:
                    self._proceso.stdin.write(json.dumps(peticion, ensure_ascii=False) + "\n")
                    self._proceso.stdin.flush()
                    return self._leer_respuesta()
                except (OSError, RuntimeError, ValueError):
                    if intento == 2:
                        raise
                    self._cerrar()

    def _cerrar(self) -> None:
        if self._proceso is not None:
            try:
                self._proceso.kill()
                self._proceso.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                pass
            for flujo in (self._proceso.stdin, self._proceso.stdout, self._proceso.stderr):
                try:
                    flujo.close()
                except (OSError, ValueError):
                    pass
            self._proceso = None

    def cerrar(self) -> None:
        with self._candado:
            self._cerrar()

    # ---- operaciones ---------------------------------------------------
    def decidir(self, estado: dict) -> dict:
        """Decisión de Prolog para un estado. Nunca lanza excepción: el error queda en 'error'."""
        resultado = {"agente": "prolog", "accion": None, "candidatas": [], "contradicciones": [],
                     "faltantes": [], "asignado_apto": None, "justificacion": [], "pasos": [],
                     "avisos": [], "tiempo_ms": None, "error": None}
        inicio = time.perf_counter()
        try:
            r = self._pedir({"op": "decidir", "estado": estado})
        except Exception as error:
            resultado["error"] = f"{type(error).__name__}: {error}"
            return resultado
        resultado["tiempo_ms"] = round((time.perf_counter() - inicio) * 1000, 1)
        if not r.get("ok"):
            resultado["error"] = r.get("error", "error desconocido")
            resultado["avisos"] = r.get("avisos", [])
            return resultado
        for clave in ("accion", "candidatas", "contradicciones", "faltantes", "asignado_apto",
                      "justificacion", "pasos", "avisos"):
            resultado[clave] = r.get(clave, resultado[clave])
        return resultado

    def consultar(self, estado: dict, consulta: str) -> dict:
        """Ejecuta una consulta escrita a mano sobre el estado (consola del front)."""
        consulta = consulta.strip().rstrip(".").strip()
        try:
            return self._pedir({"op": "consulta", "estado": estado, "consulta": consulta})
        except Exception as error:
            return {"ok": False, "error": f"{type(error).__name__}: {error}", "avisos": []}
