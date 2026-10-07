:- encoding(utf8).
/*  consultas.pl  ·  Consultas comentadas sobre la base de conocimiento (Persona 1)
    ------------------------------------------------------------------
    Ejecutar todas, desde la carpeta raíz del repositorio:
        swipl prolog/consultas.pl

    O cargar y probar una por una:
        ?- [prolog/consultas].
        ?- ejecutar_consulta(3).
        ?- decidir(p05, A, J).
*/

:- ensure_loaded(reglas).
:- ensure_loaded(hechos).

:- initialization(main, main).

% consulta(Numero, QueMuestra, TextoDeLaConsulta)

% 1. Información directa: el predicado de entrada con un pedido concreto.
%    Prolog unifica P = p01 con la cabeza de decidir/3 y devuelve la acción.
consulta(1, 'Decisión para un pedido concreto (información directa)',
         "decidir(p01, Accion, _)").

% 2. Variables y varias soluciones: con P sin ligar, Prolog recorre todos
%    los pedidos (retroceso) y entrega una respuesta por cada uno.
consulta(2, 'Variables y varias soluciones: la decisión de cada pedido cargado',
         "decidir(P, Accion, _)").

% 3. Regla de un paso: ¿qué vehículos no tienen capacidad para su pedido?
%    Une dos hechos (carga y capacidad) con una comparación aritmética.
consulta(3, 'Regla de un paso: pedidos cuya carga no cabe en el vehículo asignado',
         "(asignado(P, V), \\+ tiene_capacidad(P, V))").

% 4. Unificación y retroceso: para p90 hay dos alternativos; v901 falla
%    (poco combustible) y Prolog retrocede hasta encontrar v902.
consulta(4, 'Unificación y retroceso: ¿qué alternativo de p90 es apto?',
         "alternativa_apta(p90, W)").

% 5. Inferencia encadenada: vehiculo_apto/2 depende de cuatro reglas
%    (operativo, capacidad, tipo de carga, zona). ¿Qué pedidos tienen un
%    vehículo asignado que sirve? (p92 no aparece: su furgón está en el taller)
consulta(5, 'Inferencia encadenada: pedidos cuyo vehículo asignado es apto',
         "(asignado(P, V), vehiculo_apto(P, V))").

% 6. Caso negativo: con los hechos de p01 no se puede demostrar reasignar.
%    "No se puede demostrar" no significa "es falso": es negación por falla.
consulta(6, 'Caso negativo: ¿se puede demostrar que hay que reasignar p01?',
         "accion_candidata(p01, reasignar)").

% 7. Sin solución: p91 no tiene ninguna acción demostrable...
consulta(7, 'Sin solución: acciones demostrables para p91',
         "accion_candidata(p91, A)").

% 8. ...y por eso decidir/3 cae en inspeccionar por defecto.
consulta(8, 'Sin solución: decidir/3 cae en inspeccionar',
         "decidir(p91, Accion, Justificacion)").

% 9. Contradicción y varias candidatas: en p92 se demuestran inspeccionar
%    y reasignar; la prioridad elige inspeccionar.
consulta(9, 'Contradicción: varias acciones demostrables para p92 (en orden de prioridad)',
         "acciones_candidatas(p92, Acciones)").

% 10. Qué contradicciones detecta la base en todos los pedidos.
consulta(10, 'Contradicciones detectadas',
         "contradiccion(P, Tipo)").

% 11. Derivación completa de una decisión encadenada.
consulta(11, 'Derivación completa de la decisión de p90',
         "porque(p90, reasignar)").

% 12. Explicar por qué algo NO se cumple (útil en la defensa).
consulta(12, '¿Por qué v50 no sirve para p05?',
         "por_que_no(vehiculo_apto(p05, v50))").


main :- ejecutar_consultas.

ejecutar_consultas :-
    forall(consulta(N, _, _), ejecutar_consulta(N)).

ejecutar_consulta(N) :-
    consulta(N, Descripcion, Texto),
    format("~n[~w] ~w~n?- ~w.~n", [N, Descripcion, Texto]),
    term_string(Meta, Texto, [variable_names(Variables0)]),
    exclude([Nombre=_]>>sub_atom(Nombre, 0, 1, _, '_'), Variables0, Variables),
    findall(Variables, Meta, Soluciones0),
    list_to_set(Soluciones0, Soluciones),          % quita soluciones repetidas
    mostrar_soluciones(Variables, Soluciones).

mostrar_soluciones(_, []) :- !,
    format("   false.   (no se puede demostrar con los hechos y reglas actuales)~n").
mostrar_soluciones([], [_|_]) :- !,
    format("   true.~n").
mostrar_soluciones(_, Soluciones) :-
    forall(member(Ligaduras, Soluciones),
           ( format("   "), mostrar_ligaduras(Ligaduras), nl )).

mostrar_ligaduras([Nombre = Valor]) :- !,
    format("~w = ", [Nombre]), escribir(Valor).
mostrar_ligaduras([Nombre = Valor | Resto]) :-
    format("~w = ", [Nombre]), escribir(Valor), format(", "),
    mostrar_ligaduras(Resto).
