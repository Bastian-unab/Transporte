:- encoding(utf8).
/*  verificar_casos.pl  ·  Ejecuta Prolog sobre todos los casos y compara
    ------------------------------------------------------------------
    Sirve para revisar rápido, después de cambiar una regla, qué casos
    cambian de decisión. Ejecutar desde la carpeta raíz del repositorio:

      swipl prolog/verificar_casos.pl                       (todos los .json de la carpeta casos)
      swipl prolog/verificar_casos.pl casos/casos_directa_paso1.json
*/

:- initialization(main, main).

:- ensure_loaded(reglas).
:- ensure_loaded(estado_json).

main :-
    current_prolog_flag(argv, Argumentos),
    (   Argumentos == []
    ->  expand_file_name('casos/*.json', Archivos)
    ;   Archivos = Argumentos
    ),
    (   Archivos == []
    ->  format("No se encontraron archivos de casos.~n")
    ;   foldl(verificar_archivo, Archivos, 0-0, Aciertos-Total),
        format("~nTotal: Prolog coincide con la decisión esperada en ~w de ~w casos.~n",
               [Aciertos, Total])
    ).

verificar_archivo(Archivo, A0-T0, A-T) :-
    format("~n== ~w~n", [Archivo]),
    leer_json(Archivo, Casos),
    foldl(verificar_caso, Casos, A0-T0, A-T).

verificar_caso(Caso, A0-T0, A-T) :-
    limpiar_estado,
    afirmar_estado(Caso.estado, P),
    decidir(P, Accion, _),
    Esperada = Caso.decision_esperada,
    (   Accion == Esperada
    ->  Marca = 'OK', A is A0 + 1
    ;   Marca = 'DIFIERE', A = A0
    ),
    T is T0 + 1,
    format("~w~t~6|~w~t~30|esperada=~w~t~52|prolog=~w~t~72|~w~n",
           [Caso.id, Caso.categoria, Esperada, Accion, Marca]).
