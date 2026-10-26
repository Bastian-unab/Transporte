:- encoding(utf8).
/*  estado_json.pl  ·  Lee el estado canónico (JSON) y lo convierte en hechos
    ------------------------------------------------------------------
    Así Prolog recibe exactamente el mismo archivo que Laya, sin que
    nadie traduzca a mano. La traducción es mecánica y no agrega
    conclusiones:
        "carga_kg": 800            ->  carga_kg(p01, 800).
        "ruta_despejada": true     ->  ruta_despejada(p01, si).
        "urgencia": null           ->  desconocido(p01, urgencia).
        "vehiculo_asignado": {...} ->  asignado(p01, v10). + hechos de v10
        "vehiculos_alternativos": [{...}] -> alternativo(p01, v11). + hechos de v11
    Los identificadores se pasan a minúscula ("P01" -> p01).

    Uso:
        ?- [prolog/reglas, prolog/estado_json].
        ?- cargar_estado('mi_estado.json', P), explicar(P).
        ?- cargar_caso('casos/casos_directa_paso1.json', 'C05', P, Esperada).
*/

:- if(exists_source(library(json))).       % SWI-Prolog 10 o más reciente
:- use_module(library(json)).
:- else.                                   % SWI-Prolog 9.x
:- use_module(library(http/json)).
:- endif.

campos_pedido([carga_kg, tipo_carga, destino, urgencia, ruta_despejada]).
campos_vehiculo([tipo_vehiculo, capacidad_kg, disponible, en_mantencion,
                 combustible, conductor_disponible]).

predicados_estado([pedido/1, carga_kg/2, tipo_carga/2, destino/2, urgencia/2,
                   ruta_despejada/2, asignado/2, alternativo/2, vehiculo/1,
                   tipo_vehiculo/2, capacidad_kg/2, disponible/2, en_mantencion/2,
                   combustible/2, conductor_disponible/2, desconocido/2]).

% limpiar_estado: borra todos los hechos de pedidos y vehículos cargados.
limpiar_estado :-
    predicados_estado(Ps),
    forall(member(Nombre/Aridad, Ps),
           ( functor(Cabeza, Nombre, Aridad), retractall(Cabeza) )).

% leer_json(+Archivo, -Dato): lee un archivo JSON (UTF-8) como dict de SWI-Prolog.
leer_json(Archivo, Dato) :-
    setup_call_cleanup(
        open(Archivo, read, Flujo, [encoding(utf8)]),
        json_read_dict(Flujo, Dato, [value_string_as(atom)]),
        close(Flujo)).

% cargar_estado(+Archivo, -Pedido): limpia lo anterior y carga UN estado.
cargar_estado(Archivo, Pedido) :-
    leer_json(Archivo, Estado),
    limpiar_estado,
    afirmar_estado(Estado, Pedido).

% cargar_caso(+Archivo, +Id, -Pedido, -Esperada): carga un caso de un
% archivo de casos (lista de objetos con id, estado, decision_esperada...).
cargar_caso(Archivo, Id, Pedido, Esperada) :-
    leer_json(Archivo, Casos),
    atom_string(IdAtomo, Id),
    (   member(Caso, Casos), get_dict(id, Caso, IdAtomo)
    ->  limpiar_estado,
        afirmar_estado(Caso.estado, Pedido),
        ( get_dict(decision_esperada, Caso, Esperada) -> true ; Esperada = null )
    ;   format(user_error, "No existe el caso ~w en ~w~n", [Id, Archivo]),
        fail
    ).

% afirmar_estado(+Estado, -Pedido): convierte un estado (dict) en hechos.
afirmar_estado(Estado, P) :-
    get_dict(pedido, Estado, IdPedido),
    a_identificador(IdPedido, P),
    assertz(pedido(P)),
    campos_pedido(Campos),
    forall(member(Campo, Campos), afirmar_campo(P, Campo, Estado)),
    valor(Estado, vehiculo_asignado, Asignado),
    (   Asignado == null
    ->  assertz(desconocido(P, vehiculo_asignado))
    ;   afirmar_vehiculo(Asignado, V),
        assertz(asignado(P, V))
    ),
    valor(Estado, vehiculos_alternativos, Alternativos),
    (   Alternativos == null
    ->  assertz(desconocido(P, vehiculos_alternativos))
    ;   forall(member(Alt, Alternativos),
               ( afirmar_vehiculo(Alt, W), assertz(alternativo(P, W)) ))
    ).

afirmar_vehiculo(Datos, V) :-
    get_dict(id, Datos, Id),
    a_identificador(Id, V),
    (   vehiculo(V) -> true ; assertz(vehiculo(V)) ),
    campos_vehiculo(Campos),
    forall(member(Campo, Campos), afirmar_campo(V, Campo, Datos)).

% afirmar_campo(+Entidad, +Campo, +Dict): un hecho por campo, o desconocido/2.
afirmar_campo(Entidad, Campo, Dict) :-
    valor(Dict, Campo, Valor0),
    a_valor_prolog(Valor0, Valor),
    (   Valor == null
    ->  assertz(desconocido(Entidad, Campo))
    ;   Hecho =.. [Campo, Entidad, Valor],
        assertz(Hecho)
    ).

% valor(+Dict, +Clave, -Valor): un campo ausente cuenta como null.
valor(Dict, Clave, Valor) :-
    (   get_dict(Clave, Dict, V) -> Valor = V ; Valor = null ).

a_valor_prolog(true, si) :- !.
a_valor_prolog(false, no) :- !.
a_valor_prolog(V, V).

a_identificador(Id, Atomo) :-
    atom_string(A, Id),
    downcase_atom(A, Atomo).
