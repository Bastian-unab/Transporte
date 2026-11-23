"""Pruebas de Python: pregunta, traducción a texto, datos sintéticos, puente a Prolog y Laya.

Desde la carpeta raíz:   python -m unittest discover -s tests -v

Las pruebas de Laya usan un Router SIMULADO con la misma forma de respuesta que Laya: no
descargan nada y verifican que se envía el estado correcto y nunca la decisión esperada.
Las de Prolog se omiten si SWI-Prolog no está instalado.
"""

import json
import tempfile
import unittest
from pathlib import Path

from laya_agent.agente_laya import AgenteLaya, registrar
from laya_agent.agente_prolog import AgenteProlog, buscar_swipl
from laya_agent.casos import CATEGORIAS, cargar_casos
from laya_agent.comparacion import comparar, comparar_diagnostico
from laya_agent.estado_texto import estado_a_texto
from laya_agent.generador import firma, generar
from laya_agent.pregunta import ACCIONES, CRITERIOS, DIAGNOSTICO, preguntas, rotaciones


def hay_swipl() -> bool:
    try:
        buscar_swipl()
        return True
    except RuntimeError:
        return False


class TestCasos(unittest.TestCase):
    def test_veinte_casos_cuatro_por_categoria(self):
        casos = cargar_casos()
        self.assertEqual(len(casos), 20)
        for categoria in CATEGORIAS:
            self.assertEqual(sum(c["categoria"] == categoria for c in casos), 4, categoria)

    def test_cada_caso_tiene_los_campos_requeridos(self):
        for c in cargar_casos():
            for campo in ("id", "categoria", "descripcion", "estado", "decision_esperada", "criterio_esperada"):
                self.assertIn(campo, c, c.get("id"))
            self.assertIn(c["decision_esperada"], ACCIONES)

    def test_el_estado_no_contiene_la_conclusion(self):
        prohibidas = {"accion", "decision", "apto", "contradiccion", "esperada", "inspeccionar",
                      "despachar", "reasignar", "alertar", "esperar"}
        for c in cargar_casos():
            texto = json.dumps(c["estado"]).lower()
            for palabra in prohibidas:
                self.assertNotIn(f'"{palabra}', texto, f"{c['id']} tiene un campo '{palabra}'")


class TestPregunta(unittest.TestCase):
    def test_choice_con_las_cinco_acciones_en_orden(self):
        q = preguntas()["accion_r0"]
        self.assertEqual(q["type"], "choice")
        self.assertEqual(tuple(q["criteria"]), ACCIONES)
        self.assertEqual(tuple(CRITERIOS), ACCIONES)


class TestEstadoTexto(unittest.TestCase):
    def test_traduce_sin_conclusiones(self):
        for c in cargar_casos():
            texto = estado_a_texto(c["estado"]).lower()
            for palabra in ("apto", "cabe", "sirve", "contradic", "%", c["decision_esperada"]):
                self.assertNotIn(palabra, texto, c["id"])

    def test_null_es_sin_dato(self):
        estado = cargar_casos()[12]["estado"]          # C13: urgencia null
        self.assertIsNone(estado["urgencia"])
        self.assertIn("Urgencia: sin dato.", estado_a_texto(estado))

    def test_lista_de_alternativos_null_y_vacia(self):
        e = dict(cargar_casos()[0]["estado"])
        e["vehiculos_alternativos"] = None
        self.assertIn("Vehículos alternativos: sin dato.", estado_a_texto(e))
        e["vehiculos_alternativos"] = []
        self.assertIn("Vehículos alternativos: ninguno.", estado_a_texto(e))


@unittest.skipUnless(hay_swipl(), "SWI-Prolog no está instalado")
class TestProlog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prolog = AgenteProlog()
        cls.prolog.iniciar()

    @classmethod
    def tearDownClass(cls):
        cls.prolog.cerrar()

    def test_los_20_casos(self):
        for c in cargar_casos():
            r = self.prolog.decidir(c["estado"])
            self.assertIsNone(r["error"], c["id"])
            self.assertEqual(r["accion"], c["decision_esperada"], c["id"])

    def test_justificacion_y_pasos(self):
        r = self.prolog.decidir(cargar_casos()[4]["estado"])   # C05
        self.assertEqual(r["accion"], "reasignar")
        self.assertIs(r["asignado_apto"], False)                # 1200 kg no caben en 1000 kg
        self.assertIs(self.prolog.decidir(cargar_casos()[0]["estado"])["asignado_apto"], True)
        self.assertTrue(r["justificacion"][0].startswith("accion_candidata(p05,reasignar)"))
        self.assertEqual(r["pasos"][0]["tipo"], "regla")

    def test_las_acciones_de_prolog_son_las_de_laya(self):
        r = self.prolog.consultar(cargar_casos()[0]["estado"], "accion(A)")
        self.assertEqual(tuple(s["A"] for s in r["soluciones"]), ACCIONES)

    def test_consulta_sin_solucion_y_con_error(self):
        estado = cargar_casos()[0]["estado"]
        self.assertEqual(self.prolog.consultar(estado, "accion_candidata(p01, reasignar)")["soluciones"], [])
        self.assertFalse(self.prolog.consultar(estado, "esto no es prolog((")["ok"])

    def test_se_recupera_si_prolog_termina(self):
        estado = cargar_casos()[0]["estado"]
        self.prolog.consultar(estado, "halt")
        self.assertEqual(self.prolog.decidir(estado)["accion"], "despachar")

    def test_generador_no_repite_casos_de_evaluacion(self):
        prueba = {firma(c["estado"]) for c in cargar_casos()}
        filas = generar(4, 7, self.prolog, excluir=prueba)
        self.assertEqual(len(filas), 4 * len(ACCIONES))
        for f in filas:
            self.assertNotIn(firma(f["estado"]), prueba)
            self.assertEqual(self.prolog.decidir(f["estado"])["accion"], f["accion"])


class RouterSimulado:
    """Imita Router.predict de Laya: una respuesta por pregunta (choice, score o noul).

    En la rotación r la primera alternativa es ACCIONES[r]; este simulador elige siempre la
    primera que ve, como un modelo con sesgo de posición total.
    """

    def __init__(self):
        self.llamadas = []

    def predict(self, state, questions, model=None):
        self.llamadas.append((state, questions, model))
        respuestas = {}
        for qid, q in questions.items():
            if q["type"] == "choice":
                orden = q.get("option_order", list(range(len(ACCIONES))))
                primera = list(q["criteria"])[orden[0]]
                p = {a: 0.1 for a in q["criteria"]}
                p[primera] = 0.6
                respuestas[qid] = {"choice": primera, "probabilities": p, "answer_confidence": 0.6}
            elif q["type"] == "score":
                respuestas[qid] = {"score": 1.0, "probabilities": {"0": 0.2, "1": 0.7, "2": 0.1},
                                   "answer_confidence": 0.7}
            else:
                respuestas[qid] = {"noul": 0.9}
        return {"answers": respuestas}


class TestPreguntaRotada(unittest.TestCase):
    def test_cada_alternativa_ocupa_cada_lugar_una_vez(self):
        rot = rotaciones()
        self.assertEqual(len(rot), len(ACCIONES))
        for lugar in range(len(ACCIONES)):
            self.assertEqual(sorted(q["option_order"][lugar] for q in rot.values()), list(range(len(ACCIONES))))

    def test_una_sola_llamada_con_rotaciones_y_diagnostico(self):
        q = preguntas()
        self.assertEqual({x["type"] for x in q.values()}, {"choice", "score", "noul"})
        self.assertTrue(set(DIAGNOSTICO) <= set(q))


class TestLaya(unittest.TestCase):
    def setUp(self):
        self.agente = AgenteLaya(dispositivo="cpu")
        self.router = RouterSimulado()
        self.agente._router = self.router

    def test_recibe_el_texto_del_estado_y_las_preguntas_sin_la_esperada(self):
        caso = cargar_casos()[4]
        r = self.agente.decidir(caso["estado"])
        enviado, pregunta, modelo = self.router.llamadas[0]
        self.assertEqual(enviado, estado_a_texto(caso["estado"]))
        self.assertEqual(pregunta, preguntas())
        self.assertEqual(modelo, "multilingual")
        self.assertNotIn(caso["criterio_esperada"], enviado)
        self.assertIsNone(r["error"])

    def test_promedio_de_rotaciones_y_estabilidad(self):
        r = self.agente.decidir(cargar_casos()[0]["estado"])
        # cada rotación elige una acción distinta: el promedio queda empatado y la estabilidad es 1/5
        self.assertAlmostEqual(sum(r["probabilidades"].values()), 1.0, places=3)
        self.assertEqual(r["estabilidad"]["total"], 5)
        self.assertEqual(r["estabilidad"]["coinciden"], 1)
        self.assertEqual([o["eleccion"] for o in r["por_orden"]], list(ACCIONES))

    def test_diagnostico(self):
        r = self.agente.decidir(cargar_casos()[0]["estado"])
        self.assertEqual(r["diagnostico"]["urgencia"]["valor"], "media")
        self.assertIs(r["diagnostico"]["falta_dato"]["valor"], True)
        self.assertEqual(r["diagnostico"]["falta_dato"]["p_si"], 0.9)

    def test_registro_jsonl(self):
        r = self.agente.decidir(cargar_casos()[0]["estado"])
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "laya.jsonl"
            registrar(r, "C01", cargar_casos()[0]["estado"], ruta=ruta)
            linea = json.loads(ruta.read_text(encoding="utf-8"))
        for campo in ("fecha", "caso", "estado", "texto_enviado", "pregunta", "accion",
                      "probabilidades", "confianza", "estabilidad", "diagnostico"):
            self.assertIn(campo, linea)

    def test_error_no_detiene_el_programa(self):
        class Roto:
            def predict(self, *a, **k):
                raise ConnectionError("sin internet")
        self.agente._router = Roto()
        r = self.agente.decidir(cargar_casos()[0]["estado"])
        self.assertIn("sin internet", r["error"])
        self.assertIsNone(r["accion"])


class TestComparar(unittest.TestCase):
    def test_comparar(self):
        c = comparar("reasignar", {"accion": "reasignar"}, {"accion": "despachar"})
        self.assertEqual(c, {"esperada": "reasignar", "prolog_correcto": True,
                             "laya_correcto": False, "coinciden": False})
        self.assertIsNone(comparar(None, {"accion": "x"}, {"accion": "x"})["prolog_correcto"])

    def test_comparar_diagnostico(self):
        estado = cargar_casos()[4]["estado"]                       # C05, urgencia media
        prolog = {"faltantes": [], "contradicciones": [], "asignado_apto": False, "error": None}
        laya = {"error": None, "diagnostico": {
            "urgencia": {"valor": "media"}, "falta_dato": {"valor": True, "p_si": 0.9},
            "contradiccion": {"valor": False, "p_si": 0.1}, "asignado_sirve": {"valor": True, "p_si": 0.8}}}
        d = comparar_diagnostico(estado, prolog, laya)
        self.assertEqual({k: v["coincide"] for k, v in d.items()},
                         {"urgencia": True, "falta_dato": False, "contradiccion": True, "asignado_sirve": False})


if __name__ == "__main__":
    unittest.main()
