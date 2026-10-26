"""Pruebas del agente Laya y del puente a Prolog (Persona 2).

Ejecutar desde la carpeta raíz:  python -m unittest tests.test_laya -v

Las pruebas de Laya usan un router SIMULADO con la misma forma de respuesta que Laya 0.4.12.
No reemplazan la ejecución real: solo verifican que se envía el estado correcto y que se
registra todo. Las de Prolog se omiten si SWI-Prolog no está instalado.
"""

import unittest

from laya_agent.agente_laya import ejecutar_laya
from laya_agent.agente_prolog import buscar_swipl, ejecutar_prolog
from laya_agent.casos import cargar_casos
from laya_agent.ejecutar_caso import comparar
from laya_agent.preguntas import ACCIONES, CRITERIOS, pregunta


class RouterSimulado:
    """Imita Router.predict de Laya: devuelve answers -> accion -> choice, probabilities..."""

    def __init__(self, eleccion="despachar", falla=False):
        self.eleccion, self.falla, self.llamadas = eleccion, falla, []

    def predict(self, state, questions, model=None):
        self.llamadas.append((state, questions, model))
        if self.falla:
            raise ConnectionError("sin conexión para descargar el modelo")
        probabilidades = {a: 0.05 for a in ACCIONES}
        probabilidades[self.eleccion] = 0.8
        return {
            "answers": {"accion": {
                "type": "choice", "choice": self.eleccion, "probabilities": probabilidades,
                "confidence": 0.41, "answer_confidence": 0.8, "action": {"act_probability": 0.97},
            }},
            "routing": {"model": model, "reason": "model= override"},
        }


def hay_swipl():
    try:
        buscar_swipl()
        return True
    except RuntimeError:
        return False


class TestPregunta(unittest.TestCase):
    def test_mismas_acciones_que_prolog_y_mismo_orden(self):
        for version in CRITERIOS:
            q = pregunta(version)["accion"]
            self.assertEqual(q["type"], "choice")
            self.assertEqual(tuple(q["criteria"]), ACCIONES)

    def test_version_desconocida(self):
        with self.assertRaises(ValueError):
            pregunta("v9")


class TestAgenteLaya(unittest.TestCase):
    def test_envia_solo_el_estado(self):
        caso = cargar_casos()[0]
        router = RouterSimulado()
        ejecutar_laya(caso["estado"], router=router)
        enviado, preguntas, modelo = router.llamadas[0]
        self.assertIs(enviado, caso["estado"])
        self.assertNotIn("decision_esperada", str(enviado))
        self.assertEqual(modelo, "multilingual")
        self.assertIn("accion", preguntas)

    def test_registra_respuesta_probabilidades_y_confianza(self):
        r = ejecutar_laya(cargar_casos()[0]["estado"], router=RouterSimulado("reasignar"))
        self.assertEqual(r["accion"], "reasignar")
        self.assertEqual(set(r["probabilidades"]), set(ACCIONES))
        self.assertEqual(r["confianza"], 0.8)
        self.assertEqual(r["concentracion"], 0.41)
        self.assertIsNone(r["error"])

    def test_error_queda_registrado(self):
        r = ejecutar_laya(cargar_casos()[0]["estado"], router=RouterSimulado(falla=True))
        self.assertIsNone(r["accion"])
        self.assertIn("ConnectionError", r["error"])

    def test_comparacion(self):
        c = comparar("despachar", {"accion": "despachar"}, {"accion": "esperar"})
        self.assertEqual(c, {"esperada": "despachar", "prolog_correcto": True,
                             "laya_correcto": False, "coinciden": False})


@unittest.skipUnless(hay_swipl(), "SWI-Prolog no está instalado")
class TestPuenteProlog(unittest.TestCase):
    def test_todos_los_casos(self):
        for caso in cargar_casos():
            with self.subTest(caso=caso["id"]):
                r = ejecutar_prolog(caso["estado"])
                self.assertIsNone(r["error"], r["error"])
                # Si Prolog acierta o no es un resultado del experimento, no un error del puente.
                self.assertIn(r["accion"], ACCIONES)
                self.assertTrue(r["justificacion"])


if __name__ == "__main__":
    unittest.main()
