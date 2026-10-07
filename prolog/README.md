## Agente Prolog

**Requisito:** SWI-Prolog 9.x o superior con `swipl` en el PATH
(probado con 9.0.4 y 10.1). Fuente: documentación oficial de SWI-Prolog.

**Ejecutar (desde la raíz del repositorio):**

    swipl prolog/consultas.pl                          # 12 consultas comentadas
    swipl prolog/verificar_casos.pl                    # Prolog vs. decisión esperada
    swipl -g run_tests -t halt tests/test_reglas.pl    # pruebas automáticas
    swipl prolog/ejecutar.pl casos/casos_directa_paso1.json C05 --texto

**Interactivo:**

    ?- [prolog/reglas, prolog/hechos].
    ?- decidir(p90, Accion, Justificacion).
    ?- explicar(p90).

**Archivos:** `reglas.pl` (conocimiento general y `decidir/3`), `hechos.pl`
(pedidos de ejemplo), `estado_json.pl` (lee el estado JSON), `ejecutar.pl`
(salida JSON para Python).

**Limitaciones:** Prolog usa negación por falla; los datos vacíos se marcan con
`desconocido/2`. Las decisiones esperadas siguen la misma política que las
reglas, por lo que el acierto de Prolog en estos casos es en parte por construcción.