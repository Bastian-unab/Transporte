:- encoding(utf8).
/*  ejecutar.pl  ·  Ejecuta el agente Prolog sobre un estado JSON desde la terminal
    ------------------------------------------------------------------
    Pensado para que Persona 2 lo llame desde Python (subprocess) sin
    conocer las reglas. Ejecutar desde la carpeta raíz del repositorio.

      swipl prolog/ejecutar.pl estado.json                 -> resultado en JSON
      swipl prolog/ejecutar.pl casos/casos_directa_paso1.json C05
      swipl prolog/ejecutar.pl casos/casos_directa_paso1.json C05 --texto

    Salida JSON (una línea):
      { "pedido": "p05", "accion": "reasignar",
        "candidatas": ["reasignar"], "contradicciones": [], "faltantes": [],
        "justificacion": ["accion_candidata(p05,reasignar)   <- regla", ...],
        "caso": "C05", "decision_esperada": "reasignar" }
*/

:- initialization(main, main).

:- ensure_loaded(reglas).
:- ensure_loaded(estado_json).

main :-
    current_prolog_flag(argv, Argumentos0),
    maplist(atom_string, Argumentos, Argumentos0),
    partition([A]>>sub_atom(A, 0, _, _, '--'), Argumentos, Opciones, Posicionales),
    (   Posicionales = [Archivo]
    ->  cargar_estado(Archivo, P), Extra = _{}
    ;   Posicionales = [Archivo, Id]
    ->  cargar_caso(Archivo, Id, P, Esperada),
        Extra = _{caso: Id, decision_esperada: Esperada}
    ;   format(user_error,
               "Uso: swipl prolog/ejecutar.pl ARCHIVO.json [ID_CASO] [--texto]~n", []),
        halt(1)
    ),
    (   memberchk('--texto', Opciones)
    ->  explicar(P)
    ;   resultado(P, Resultado0),
        put_dict(Extra, Resultado0, Resultado),
        set_stream(user_output, encoding(utf8)),
        json_write_dict(user_output, Resultado, [width(0)]),
        nl
    ).

% resultado(+P, -Dict): la decisión y todo lo necesario para mostrarla.
resultado(P, _{pedido: P, accion: Accion, candidatas: Candidatas,
               contradicciones: Contradicciones, faltantes: Faltantes,
               justificacion: Lineas}) :-
    decidir(P, Accion, Pasos),
    acciones_candidatas(P, Candidatas),
    findall(T, (contradiccion(P, C), term_string(C, T)), C0),
    sort(C0, Contradicciones),
    findall(T, (falta_dato_critico(P, F), term_string(F, T)), F0),
    sort(F0, Faltantes),
    maplist(texto_paso, Pasos, Lineas).
