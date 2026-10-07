:- encoding(utf8).
/*  test_reglas.pl  ·  Pruebas automáticas de la base Prolog (Persona 1)
    ------------------------------------------------------------------
    Ejecutar desde la carpeta raíz del repositorio:
        swipl -g run_tests -t halt tests/test_reglas.pl

    Si cambias una regla y alguna prueba falla, la prueba dice qué
    decisión cambió. Si el cambio es intencional, actualiza la prueba.
*/

:- use_module(library(plunit)).

:- prolog_load_context(directory, Dir),
   atom_concat(Dir, '/..', Raiz),
   asserta(user:raiz_proyecto(Raiz)).

:- raiz_proyecto(R), atom_concat(R, '/prolog/reglas', F), ensure_loaded(F).
:- raiz_proyecto(R), atom_concat(R, '/prolog/hechos', F), ensure_loaded(F).
:- raiz_proyecto(R), atom_concat(R, '/prolog/estado_json', F), ensure_loaded(F).

/* ---- Pedidos de ejemplo de prolog/hechos.pl ---------------------- */
:- begin_tests(hechos_de_ejemplo).

test(despachar_directo) :-
    decidir(p01, despachar, _).
test(alertar_ruta_cortada) :-
    decidir(p02, alertar, _).
test(reasignar_por_capacidad) :-
    decidir(p05, reasignar, _).
test(retroceso_al_segundo_alternativo, W == v902) :-
    alternativa_apta(p90, W).
test(primer_alternativo_no_operativo, fail) :-
    operativo(v901).
test(negativo_no_se_reasigna_p01, fail) :-
    accion_candidata(p01, reasignar).
test(sin_solucion_cae_en_inspeccionar) :-
    \+ accion_candidata(p91, _),
    decidir(p91, inspeccionar, [paso(0, sin_regla, _)]).
test(contradiccion_con_varias_candidatas, Acciones == [inspeccionar, reasignar]) :-
    acciones_candidatas(p92, Acciones).
test(todas_las_acciones_tienen_prioridad) :-
    forall(accion(A), prioridad(A, _)).
test(justificacion_empieza_por_la_accion, Primero == accion_candidata(p05, reasignar)) :-
    decidir(p05, _, [paso(0, regla, Primero)|_]).

:- end_tests(hechos_de_ejemplo).

/* ---- Datos faltantes, construidos a partir de un caso completo --- */
:- begin_tests(datos_faltantes, [setup(limpiar_estado), cleanup(limpiar_estado)]).

caso_c01_sin(Campo, P) :-
    raiz_proyecto(R),
    atom_concat(R, '/casos/casos_directa_paso1.json', Archivo),
    leer_json(Archivo, [Caso|_]),
    put_dict(Campo, Caso.estado, null, Estado),
    limpiar_estado,
    afirmar_estado(Estado, P).

test(urgencia_desconocida_es_critica, [nondet]) :-
    caso_c01_sin(urgencia, P),
    decidir(P, inspeccionar, _),
    falta_dato_critico(P, dato(P, urgencia)).
test(alternativos_desconocidos_no_importan_si_el_asignado_sirve) :-
    caso_c01_sin(vehiculos_alternativos, P),
    decidir(P, despachar, _).

:- end_tests(datos_faltantes).

/* ---- Los 8 casos de casos/casos_directa_paso1.json --------------- */
:- begin_tests(casos_persona1, [cleanup(limpiar_estado)]).

test(caso, [forall(caso_p1(Id, Estado, Esperada)), true(Accion == Esperada)]) :-
    limpiar_estado,
    afirmar_estado(Estado, P),
    decidir(P, Accion, _),
    ( Accion == Esperada -> true ; format(user_error, "~w: ~w~n", [Id, Accion]) ).

caso_p1(Id, Estado, Esperada) :-
    raiz_proyecto(R),
    atom_concat(R, '/casos/casos_directa_paso1.json', Archivo),
    leer_json(Archivo, Casos),
    member(Caso, Casos),
    Id = Caso.id, Estado = Caso.estado, Esperada = Caso.decision_esperada.

:- end_tests(casos_persona1).
