:- encoding(utf8).
/*  ejecutar.pl  ·  Ejecuta el agente Prolog sobre un estado JSON desde la terminal
    ------------------------------------------------------------------
    Ejecutar desde la carpeta raíz del repositorio:

      swipl prolog/ejecutar.pl estado.json                    -> resultado en JSON
      swipl prolog/ejecutar.pl casos/casos.json C05           -> un caso del archivo de casos
      swipl prolog/ejecutar.pl casos/casos.json C05 --texto   -> explicación legible

    El servidor web no usa este archivo (usa servidor.pl, que queda
    abierto); este sirve para probar a mano o en la defensa.
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
    set_stream(user_output, encoding(utf8)),
    (   memberchk('--texto', Opciones)
    ->  explicar(P)
    ;   resultado(P, Resultado0),
        del_dict(pasos, Resultado0, _, Resultado1),
        put_dict(Extra, Resultado1, Resultado),
        json_write_dict(user_output, Resultado, [width(0)]),
        nl
    ).
