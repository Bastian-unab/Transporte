:- encoding(utf8).
/*  servidor.pl  ·  Proceso Prolog que queda abierto para el servidor web
    ------------------------------------------------------------------
    app/servidor.py lo inicia una sola vez (swipl prolog/servidor.pl) y
    conversa con él por la entrada y la salida estándar: una petición
    JSON por línea y una respuesta JSON por línea.

      {"op": "ping"}
      {"op": "decidir",  "estado": {...}}
      {"op": "consulta", "estado": {...}, "consulta": "vehiculo_apto(p05, V)"}

    Antes de cada petición ejecuta make/0, que vuelve a cargar los
    archivos .pl modificados. Si en la defensa se edita reglas.pl, el
    cambio se aplica en la siguiente ejecución sin reiniciar nada. Los
    errores de carga (por ejemplo, un punto que falta) se devuelven en
    "avisos" para mostrarlos en el front.
*/

:- initialization(main, main).

:- ensure_loaded(reglas).
:- ensure_loaded(estado_json).

:- dynamic aviso/1.

main :-
    set_stream(user_input, encoding(utf8)),
    set_stream(user_output, encoding(utf8)),
    current_prolog_flag(version, Version),
    responder(_{ok: true, listo: true, version: Version}),
    bucle.

bucle :-
    read_line_to_string(user_input, Linea),
    (   Linea == end_of_file
    ->  true
    ;   Linea == ""
    ->  bucle
    ;   atender(Linea),
        bucle
    ).

% atender(+Linea): una petición completa. Cualquier error se convierte
% en {"ok": false, "error": "..."} para que Python nunca quede esperando.
atender(Linea) :-
    retractall(aviso(_)),
    catch(( atom_json_dict(Linea, Peticion, [value_string_as(atom)]),
            recargar,
            procesar(Peticion, Respuesta0)
          ),
          Error,
          ( error_texto(Error, Texto),
            Respuesta0 = _{ok: false, error: Texto} )),
    findall(A, aviso(A), Avisos),
    put_dict(avisos, Respuesta0, Avisos, Respuesta),
    responder(Respuesta).

responder(Dict) :-
    json_write_dict(user_output, Dict, [width(0)]),
    nl(user_output),
    flush_output(user_output).

% error_texto(+Error, -Texto): el mensaje que SWI-Prolog mostraría en la consola.
error_texto(Error, Texto) :-
    catch(( phrase('$messages':translate_message(Error), Lineas),
            with_output_to(string(Texto), print_message_lines(current_output, '', Lineas)) ),
          _, fail), !.
error_texto(Error, Texto) :-
    term_string(Error, Texto).

/* ---- Recarga de reglas y captura de errores ---------------------- */

:- prolog_load_context(directory, Dir), nb_setval(carpeta_prolog, Dir).

% recargar: vuelve a cargar reglas.pl y estado_json.pl solo si cambiaron
% desde la última carga (como make/0, pero sin sus chequeos extra).
recargar :-
    nb_getval(carpeta_prolog, Dir),
    findall(F, ( member(N, [reglas, estado_json]),
                 atomic_list_concat([Dir, '/', N, '.pl'], F) ), Archivos),
    setup_call_cleanup(
        nb_setval(capturando, true),
        load_files(Archivos, [if(changed)]),
        nb_setval(capturando, false)).

% Mientras se recarga, los errores y advertencias de carga se guardan
% como avisos (y además se imprimen en la salida de error, como siempre).
:- multifile user:message_hook/3.
user:message_hook(_Termino, Tipo, Lineas) :-
    memberchk(Tipo, [error, warning]),
    nb_current(capturando, true),
    with_output_to(string(Texto), print_message_lines(current_output, '', Lineas)),
    assertz(aviso(Texto)),
    fail.

/* ---- Peticiones -------------------------------------------------- */

procesar(Peticion, _{ok: true}) :-
    Peticion.op == ping, !.
procesar(Peticion, Respuesta) :-
    Peticion.op == decidir, !,
    limpiar_estado,
    afirmar_estado(Peticion.estado, P),
    resultado(P, Resultado),
    put_dict(ok, Resultado, true, Respuesta).
procesar(Peticion, Respuesta) :-
    Peticion.op == consulta, !,
    limpiar_estado,
    afirmar_estado(Peticion.estado, P),
    consultar(Peticion.consulta, Soluciones, Salida, Limite),
    Respuesta = _{ok: true, pedido: P, soluciones: Soluciones,
                  salida: Salida, limite_alcanzado: Limite}.
procesar(Peticion, _) :-
    throw(error(domain_error(operacion, Peticion.op), _)).

% consultar(+Texto, -Soluciones, -Salida, -Limite): ejecuta una consulta
% escrita a mano (consola del front) sobre el estado cargado. Devuelve
% hasta 25 soluciones; cada una es un dict Variable -> valor (texto).
% Lo que la consulta imprime (por ejemplo explicar/1) vuelve en Salida.
% Una consulta sin variables que se cumple devuelve [{}] (true);
% una que no se puede demostrar devuelve [] (false).
consultar(Texto, Soluciones, Salida, Limite) :-
    term_string(Meta, Texto, [variable_names(Variables0)]),
    exclude([Nombre=_]>>sub_atom(Nombre, 0, 1, _, '_'), Variables0, Variables),
    Maximo = 25,
    with_output_to(string(Salida),
        call_with_time_limit(5,
            findall(Variables, limit(Maximo, Meta), Ligaduras0))),
    list_to_set(Ligaduras0, Ligaduras),
    length(Ligaduras0, N),
    ( N >= Maximo -> Limite = true ; Limite = false ),
    maplist(ligaduras_dict, Ligaduras, Soluciones).

ligaduras_dict(Ligaduras, Dict) :-
    findall(Nombre-Valor,
            ( member(Nombre=V, Ligaduras), texto_termino(V, Valor) ),
            Pares),
    dict_pairs(Dict, _, Pares).
