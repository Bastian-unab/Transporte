"""Front web para comparar Prolog y Laya (Persona 2).

Solo usa la biblioteca estándar de Python: no hay que instalar nada extra.

Desde la carpeta raíz del repositorio, con el entorno virtual activado:
    python app/servidor.py
y se abre http://localhost:8000 en el navegador.

Funciones (rúbrica G5):
  1. se ejecuta sin modificar el código;
  2. permite elegir un caso de casos/ o escribir un estado nuevo;
  3. ejecuta Prolog (decidir/3 de Persona 1);
  4. ejecuta Laya con la misma pregunta y las mismas alternativas;
  5. muestra por separado acción, justificación, probabilidades, confianza y la comparación.
"""

import argparse
import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))   # para importar laya_agent al ejecutar "python app/servidor.py"

from laya_agent import agente_laya                       # noqa: E402
from laya_agent.agente_prolog import buscar_swipl         # noqa: E402
from laya_agent.casos import cargar_casos                 # noqa: E402
from laya_agent.ejecutar_caso import ejecutar_ambos       # noqa: E402
from laya_agent.preguntas import ACCIONES, CRITERIOS, VERSION_POR_DEFECTO  # noqa: E402

PAGINA = Path(__file__).resolve().parent / "index.html"


def estado_prolog() -> dict:
    try:
        return {"listo": True, "error": None, "ruta": buscar_swipl()}
    except RuntimeError as error:
        return {"listo": False, "error": str(error), "ruta": None}


class Manejador(BaseHTTPRequestHandler):
    def _responder(self, codigo: int, cuerpo: bytes, tipo: str) -> None:
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _json(self, datos, codigo: int = 200) -> None:
        self._responder(codigo, json.dumps(datos, ensure_ascii=False).encode("utf-8"),
                        "application/json; charset=utf-8")

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._responder(200, PAGINA.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/casos":
            self._json(cargar_casos())
        elif self.path == "/api/configuracion":
            self._json({
                "acciones": ACCIONES,
                "versiones": list(CRITERIOS),
                "version_por_defecto": VERSION_POR_DEFECTO,
                "prolog": estado_prolog(),
                "laya": agente_laya.estado_carga,
            })
        else:
            self._json({"error": "no encontrado"}, 404)

    def do_POST(self):
        if self.path != "/api/ejecutar":
            self._json({"error": "no encontrado"}, 404)
            return
        try:
            largo = int(self.headers.get("Content-Length", 0))
            pedido = json.loads(self.rfile.read(largo).decode("utf-8"))
            estado = pedido["estado"]
            if not isinstance(estado, dict):
                raise ValueError("el estado debe ser un objeto JSON")
        except (ValueError, KeyError) as error:
            self._json({"error": f"Pedido inválido: {error}"}, 400)
            return
        agentes = pedido.get("agentes", ["prolog", "laya"])
        version = pedido.get("criterios", VERSION_POR_DEFECTO)
        if version not in CRITERIOS:
            version = VERSION_POR_DEFECTO
        resultado = ejecutar_ambos(
            estado, pedido.get("esperada") or None, version,
            con_prolog="prolog" in agentes, con_laya="laya" in agentes,
        )
        if resultado["laya"] and not resultado["laya"]["error"]:
            agente_laya.registrar(resultado["laya"], pedido.get("id") or "front")
        self._json(resultado)

    def log_message(self, formato, *args):   # sin ruido en la consola
        pass


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Front para comparar Prolog y Laya")
    parser.add_argument("--puerto", type=int, default=8000)
    parser.add_argument("--sin-navegador", action="store_true", help="no abrir el navegador")
    args = parser.parse_args()

    # El modelo de Laya se carga en segundo plano para que la primera consulta sea rápida.
    threading.Thread(target=agente_laya.precargar_laya, daemon=True).start()

    url = f"http://localhost:{args.puerto}"
    servidor = ThreadingHTTPServer(("127.0.0.1", args.puerto), Manejador)
    print(f"Front listo en {url}  (Ctrl+C para detener)")
    print("Laya se está cargando en segundo plano; la página muestra cuándo está listo.")
    if not args.sin_navegador:
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nDetenido.")


if __name__ == "__main__":
    main()
