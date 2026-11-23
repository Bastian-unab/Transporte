"""Mini servidor web del proyecto: carga Prolog y Laya UNA vez y sirve el front.

Desde la carpeta raíz del repositorio, con el entorno virtual activado:

    python app/servidor.py                    abre http://127.0.0.1:8000
    python app/servidor.py --puerto 8080
    python app/servidor.py --sin-navegador

Solo usa la biblioteca estándar de Python (no hay que instalar Flask ni nada extra).

Qué carga al iniciar:
  - Prolog: abre `swipl prolog/servidor.pl`, que queda esperando peticiones. Si se edita
    prolog/reglas.pl con el servidor andando, el cambio se aplica en la siguiente ejecución.
  - Laya: el checkpoint multilingüe (sin entrenar). La carga corre en segundo plano: la página
    abre de inmediato y muestra "Laya cargando" hasta que esté listo.

API (JSON):
  GET  /api/estado      estado de ambos agentes, acciones, preguntas de Laya
  GET  /api/casos       los 20 casos de casos/casos.json
  POST /api/ejecutar    {estado, id_caso?, esperada?} -> prolog, laya, comparacion, diagnostico
  POST /api/consulta    {estado, consulta} -> consulta libre de Prolog sobre ese estado
  POST /api/texto_laya  {estado} -> el texto exacto que recibe Laya
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

from laya_agent.agente_laya import AgenteLaya, registrar                     # noqa: E402
from laya_agent.agente_prolog import AgenteProlog                            # noqa: E402
from laya_agent.casos import CATEGORIAS, cargar_casos                        # noqa: E402
from laya_agent.comparacion import comparar, comparar_diagnostico            # noqa: E402
from laya_agent.estado_texto import estado_a_texto                           # noqa: E402
from laya_agent.pregunta import ACCIONES, DIAGNOSTICO, pregunta_decision     # noqa: E402

ESTATICOS = Path(__file__).resolve().parent / "static"
TIPOS_CONTENIDO = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
                   ".js": "text/javascript; charset=utf-8", ".svg": "image/svg+xml"}

prolog = AgenteProlog()
laya = AgenteLaya()
estado_prolog = {"listo": False, "error": None}


def cargar_laya_en_segundo_plano() -> None:
    def tarea():
        try:
            laya.cargar()
        except Exception:
            pass   # el error queda en laya.error y el front lo muestra
    threading.Thread(target=tarea, daemon=True).start()


class Manejador(BaseHTTPRequestHandler):
    server_version = "CentralDespacho/1.0"

    def log_message(self, formato, *args):   # consola más limpia: solo la API
        if self.path.startswith("/api/"):
            sys.stderr.write("  %s %s\n" % (self.command, self.path))

    def _responder(self, codigo: int, cuerpo: bytes, tipo: str) -> None:
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _json(self, datos, codigo: int = 200) -> None:
        self._responder(codigo, json.dumps(datos, ensure_ascii=False).encode("utf-8"),
                        "application/json; charset=utf-8")

    def _leer_json(self) -> dict:
        largo = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(largo).decode("utf-8") or "{}")

    # ---- GET -------------------------------------------------------------
    def do_GET(self):
        ruta = self.path.split("?", 1)[0]
        if ruta in ("/", "/index.html"):
            return self._archivo(ESTATICOS / "index.html")
        if ruta.startswith("/static/"):
            archivo = (ESTATICOS / ruta.removeprefix("/static/")).resolve()
            if ESTATICOS.resolve() in archivo.parents:
                return self._archivo(archivo)
        if ruta == "/api/estado":
            return self._json({
                "prolog": {**estado_prolog, "version": prolog.version, "ruta": prolog.ruta},
                "laya": {"listo": laya.listo, "cargando": laya.cargando, "error": laya.error,
                         "version": laya.version_laya, "modelo": "multilingual (sin entrenar)"},
                "acciones": ACCIONES,
                "pregunta": pregunta_decision(),
                "diagnostico": {k: {"pregunta": v["pregunta"], "prolog": v["prolog"], "nivel": v["nivel"]}
                                for k, v in DIAGNOSTICO.items()},
                "categorias": CATEGORIAS,
            })
        if ruta == "/api/casos":
            return self._json(cargar_casos())
        self._json({"error": "no encontrado"}, 404)

    def _archivo(self, archivo: Path) -> None:
        if not archivo.is_file():
            return self._json({"error": "no encontrado"}, 404)
        tipo = TIPOS_CONTENIDO.get(archivo.suffix, "application/octet-stream")
        self._responder(200, archivo.read_bytes(), tipo)

    # ---- POST ------------------------------------------------------------
    def do_POST(self):
        try:
            pedido = self._leer_json()
        except (ValueError, UnicodeDecodeError):
            return self._json({"error": "El cuerpo no es JSON válido"}, 400)
        estado = pedido.get("estado")
        if not isinstance(estado, dict):
            return self._json({"error": "Falta 'estado' (un objeto JSON)"}, 400)

        if self.path == "/api/ejecutar":
            r_prolog = prolog.decidir(estado)      # ninguno de los dos recibe la esperada
            r_laya = laya.decidir(estado)
            id_caso = pedido.get("id_caso") or "nuevo"
            if not r_laya["error"]:
                registrar(r_laya, id_caso, estado)
            return self._json({
                "id_caso": id_caso, "prolog": r_prolog, "laya": r_laya,
                "comparacion": comparar(pedido.get("esperada"), r_prolog, r_laya),
                "diagnostico": comparar_diagnostico(estado, r_prolog, r_laya),
            })

        if self.path == "/api/consulta":
            consulta = (pedido.get("consulta") or "").strip()
            if not consulta:
                return self._json({"error": "Escribe una consulta"}, 400)
            return self._json(prolog.consultar(estado, consulta))

        if self.path == "/api/texto_laya":
            return self._json({"texto": estado_a_texto(estado)})

        self._json({"error": "no encontrado"}, 404)


def iniciar_servidor(puerto: int) -> ThreadingHTTPServer:
    for p in range(puerto, puerto + 10):
        try:
            return ThreadingHTTPServer(("127.0.0.1", p), Manejador)
        except OSError:
            continue
    raise OSError(f"No hay puertos libres entre {puerto} y {puerto + 9}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Servidor del front Prolog vs Laya")
    parser.add_argument("--puerto", type=int, default=8000)
    parser.add_argument("--sin-navegador", action="store_true")
    args = parser.parse_args()

    print("Iniciando Prolog...")
    try:
        prolog.iniciar()
        estado_prolog["listo"] = True
        print(f"  SWI-Prolog {prolog.version} listo ({prolog.ruta})")
    except Exception as error:
        estado_prolog["error"] = str(error)
        print(f"  Prolog no pudo iniciar: {error}")

    print("Cargando Laya (checkpoint multilingüe) en segundo plano...")
    cargar_laya_en_segundo_plano()

    servidor = iniciar_servidor(args.puerto)
    url = f"http://127.0.0.1:{servidor.server_address[1]}"
    print(f"\nAbre {url}   (Ctrl+C para detener)\n")
    if not args.sin_navegador:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo...")
    finally:
        servidor.server_close()
        prolog.cerrar()


if __name__ == "__main__":
    main()
