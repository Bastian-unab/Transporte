:- encoding(utf8).
/*  reglas.pl  ·  Base de conocimiento del agente lógico (Persona 1)
    ------------------------------------------------------------------
    Dominio : central de despacho de carga local.
    Decisión: ¿qué acción de despacho debe ejecutarse primero para un pedido?
    Acciones: despachar, reasignar, esperar, inspeccionar, alertar.

    Este archivo contiene SOLO conocimiento general (no datos de un caso).
    Los datos de cada pedido vienen de:
      - prolog/hechos.pl          ejemplos escritos a mano, o
      - prolog/estado_json.pl     que lee el estado canónico en JSON.

    Predicado de entrada para el resto del grupo:
        decidir(+Pedido, -Accion, -Justificacion)

    Uso interactivo, desde la carpeta raíz del repositorio:
        ?- [prolog/reglas, prolog/hechos].
        ?- decidir(p01, Accion, Justificacion).
        ?- explicar(p90).
        ?- por_que_no(vehiculo_apto(p05, v50)).
*/


/* ==================================================================
   1. HECHOS DEL ESTADO (los aporta cada caso)
   ------------------------------------------------------------------
   Hay dos tipos de entidades: pedidos (p01, p02...) y vehículos
   (v10, v50...). Cada campo del estado canónico se convierte en un
   hecho  campo(Entidad, Valor). Un campo vacío (null) se convierte en
   desconocido(Entidad, campo).
   Se declaran dinámicos para que consultar un dato ausente falle en
   vez de dar error de "procedimiento desconocido".
   ================================================================== */

:- dynamic
    pedido/1,                % pedido(P)
    carga_kg/2,              % carga_kg(P, Kilos)
    tipo_carga/2,            % tipo_carga(P, general | refrigerada)
    destino/2,               % destino(P, centro | zona_norte | zona_sur | zona_oriente | zona_poniente)
    urgencia/2,              % urgencia(P, alta | media | baja)
    ruta_despejada/2,        % ruta_despejada(P, si | no)
    asignado/2,              % asignado(P, V): V es el vehículo asignado al pedido P
    alternativo/2,           % alternativo(P, W): W es un vehículo alternativo para P
    vehiculo/1,              % vehiculo(V)
    tipo_vehiculo/2,         % tipo_vehiculo(V, camioneta | furgon | furgon_refrigerado | camion)
    capacidad_kg/2,          % capacidad_kg(V, Kilos)
    disponible/2,            % disponible(V, si | no): no está ocupado en otro reparto
    en_mantencion/2,         % en_mantencion(V, si | no): registrado en el taller
    combustible/2,           % combustible(V, suficiente | bajo)
    conductor_disponible/2,  % conductor_disponible(V, si | no)
    desconocido/2.           % desconocido(Entidad, Campo): el dato llegó vacío

:- discontiguous
    pedido/1, carga_kg/2, tipo_carga/2, destino/2, urgencia/2, ruta_despejada/2,
    asignado/2, alternativo/2, vehiculo/1, tipo_vehiculo/2, capacidad_kg/2,
    disponible/2, en_mantencion/2, combustible/2, conductor_disponible/2,
    desconocido/2.


/* ==================================================================
   2. CONOCIMIENTO GENERAL DEL DOMINIO (no depende del caso)
   ================================================================== */

% accion(A): las cinco alternativas. Laya recibe exactamente las mismas.
accion(despachar).      % hay vehículo adecuado y disponible: sale ahora
accion(reasignar).      % el asignado no sirve, pero hay otro apto
accion(esperar).        % no hay urgencia o no hay vehículo libre todavía
accion(inspeccionar).   % faltan datos o hay contradicción
accion(alertar).        % requiere intervención del supervisor

% prioridad(A, N): si varias acciones son demostrables, gana la de menor N.
% Primero la calidad de los datos, luego lo urgente, luego la operación.
prioridad(inspeccionar, 1).
prioridad(alertar,      2).
prioridad(reasignar,    3).
prioridad(despachar,    4).
prioridad(esperar,      5).

% capacidad_maxima(Tipo, Kg): carga máxima real de cada tipo de vehículo.
% Sirve para detectar capacidades declaradas imposibles (contradicción).
capacidad_maxima(camioneta,          1500).
capacidad_maxima(furgon,             3500).
capacidad_maxima(furgon_refrigerado, 3000).
capacidad_maxima(camion,            12000).

% zona_restringida(Zona, Tipo): el tipo de vehículo no puede entrar a la zona.
zona_restringida(centro, camion).

% umbral(Nombre, Valor): límites numéricos usados por las reglas.
umbral(aprovechamiento_alto, 0.8).   % 80 % de la capacidad


/* ==================================================================
   3. REGLAS DE UN PASO (una condición del dominio)
   ================================================================== */

% urgente(P): el pedido tiene urgencia alta.
urgente(P) :-
    urgencia(P, alta).

% operativo(V): el vehículo puede salir (libre, fuera del taller,
% con combustible y con conductor).
operativo(V) :-
    disponible(V, si),
    en_mantencion(V, no),
    combustible(V, suficiente),
    conductor_disponible(V, si).

% tiene_capacidad(P, V): la carga de P cabe en V.
tiene_capacidad(P, V) :-
    carga_kg(P, Carga),
    capacidad_kg(V, Capacidad),
    Carga =< Capacidad.

% tipo_compatible(P, V): V puede llevar el tipo de carga de P.
tipo_compatible(P, V) :-
    tipo_carga(P, general),
    vehiculo(V).
tipo_compatible(P, V) :-
    tipo_carga(P, refrigerada),
    tipo_vehiculo(V, furgon_refrigerado).

% puede_ingresar(P, V): V tiene permitido entrar al destino de P.
puede_ingresar(P, V) :-
    destino(P, Zona),
    tipo_vehiculo(V, Tipo),
    \+ zona_restringida(Zona, Tipo).

% aprovechamiento_alto(P, V): la carga ocupa al menos el 80 % de V.
aprovechamiento_alto(P, V) :-
    carga_kg(P, Carga),
    capacidad_kg(V, Capacidad),
    Capacidad > 0,
    umbral(aprovechamiento_alto, U),
    Carga / Capacidad >= U.


/* ==================================================================
   4. REGLAS ENCADENADAS
   ================================================================== */

% vehiculo_apto(P, V): V sirve para P (cuatro condiciones).
vehiculo_apto(P, V) :-
    operativo(V),
    tiene_capacidad(P, V),
    tipo_compatible(P, V),
    puede_ingresar(P, V).

% alternativa_apta(P, W): alguno de los alternativos de P es apto.
% Si hay varios alternativos, Prolog los prueba en orden (retroceso).
alternativa_apta(P, W) :-
    alternativo(P, W),
    vehiculo_apto(P, W).

% sin_vehiculo_apto(P): ni el asignado ni ningún alternativo sirven.
sin_vehiculo_apto(P) :-
    asignado(P, V),
    \+ vehiculo_apto(P, V),
    \+ alternativa_apta(P, _).

% conviene_salir(P, V): vale la pena que V salga ahora con P.
conviene_salir(P, _) :-
    urgencia(P, alta).
conviene_salir(P, _) :-
    urgencia(P, media).
conviene_salir(P, V) :-               % sin urgencia, solo si va casi lleno
    urgencia(P, baja),
    aprovechamiento_alto(P, V).


/* ==================================================================
   5. INFORMACIÓN FALTANTE Y CONTRADICCIONES
   ------------------------------------------------------------------
   La negación por falla (\+) supone un mundo cerrado: lo que no se
   puede demostrar se trata como falso. Para no convertir "no sé" en
   "no", los campos vacíos se registran con desconocido/2 y estas
   reglas detectan cuándo un dato vacío importa para la decisión.
   ================================================================== */

% vehiculo_relevante(P, V): vehículo cuyos datos importan para decidir.
% Los alternativos solo importan si el asignado no sirve.
vehiculo_relevante(P, V) :-
    asignado(P, V).
vehiculo_relevante(P, W) :-
    asignado(P, V),
    \+ vehiculo_apto(P, V),
    alternativo(P, W).

% falta_dato_critico(P, dato(Entidad, Campo)): falta un dato necesario.
falta_dato_critico(P, dato(P, Campo)) :-          % datos del pedido
    pedido(P),
    desconocido(P, Campo),
    Campo \== vehiculos_alternativos.
falta_dato_critico(P, dato(P, vehiculos_alternativos)) :-   % solo si hacen falta
    desconocido(P, vehiculos_alternativos),
    asignado(P, V),
    \+ vehiculo_apto(P, V).
falta_dato_critico(P, dato(V, Campo)) :-          % datos de un vehículo relevante
    vehiculo_relevante(P, V),
    desconocido(V, Campo).

% contradiccion(P, Tipo): los datos no pueden ser verdad al mismo tiempo.
contradiccion(P, disponible_y_en_mantencion(V)) :-
    vehiculo_relevante(P, V),
    disponible(V, si),
    en_mantencion(V, si).
contradiccion(P, capacidad_imposible(V)) :-
    vehiculo_relevante(P, V),
    tipo_vehiculo(V, Tipo),
    capacidad_kg(V, Capacidad),
    capacidad_maxima(Tipo, Maxima),
    Capacidad > Maxima.
contradiccion(P, carga_no_positiva) :-
    carga_kg(P, Carga),
    Carga =< 0.


/* ==================================================================
   6. ACCIONES CANDIDATAS Y DECISIÓN
   ================================================================== */

% accion_candidata(P, A): A es demostrable para P. Puede haber varias.
accion_candidata(P, inspeccionar) :-
    contradiccion(P, _).
accion_candidata(P, inspeccionar) :-
    falta_dato_critico(P, _).
accion_candidata(P, alertar) :-             % urgente y sin vehículo que sirva
    urgente(P),
    sin_vehiculo_apto(P).
accion_candidata(P, alertar) :-             % urgente y la ruta está cortada
    urgente(P),
    ruta_despejada(P, no).
accion_candidata(P, reasignar) :-
    asignado(P, V),
    \+ vehiculo_apto(P, V),
    alternativa_apta(P, _).
accion_candidata(P, despachar) :-
    asignado(P, V),
    vehiculo_apto(P, V),
    ruta_despejada(P, si),
    conviene_salir(P, V).
accion_candidata(P, esperar) :-             % sin urgencia y va casi vacío
    asignado(P, V),
    vehiculo_apto(P, V),
    ruta_despejada(P, si),
    \+ conviene_salir(P, V).
accion_candidata(P, esperar) :-             % ruta cortada, pero no es urgente
    ruta_despejada(P, no),
    \+ urgente(P).
accion_candidata(P, esperar) :-             % no hay vehículo libre todavía
    sin_vehiculo_apto(P),
    \+ urgente(P).

% acciones_candidatas(P, Lista): candidatas sin repetir, por prioridad.
acciones_candidatas(P, Acciones) :-
    findall(N-A, (accion_candidata(P, A), prioridad(A, N)), Pares),
    keysort(Pares, Ordenados),
    pairs_values(Ordenados, ConRepetidas),
    list_to_set(ConRepetidas, Acciones).

% decidir(+P, -Accion, -Justificacion): PREDICADO DE ENTRADA.
% Elige la candidata de mayor prioridad y devuelve los pasos que la
% demuestran. Si ninguna acción es demostrable, cae en inspeccionar.
decidir(P, Accion, Justificacion) :-
    pedido(P),
    acciones_candidatas(P, Candidatas),
    (   Candidatas = [Accion|_]
    ->  once(demostrar(accion_candidata(P, Accion), Arbol)),
        aplanar(Arbol, 0, Justificacion)
    ;   Accion = inspeccionar,
        Justificacion = [paso(0, sin_regla, ninguna_accion_demostrable(P))]
    ).


/* ==================================================================
   7. JUSTIFICACIÓN: META-INTÉRPRETE QUE GUARDA LA DERIVACIÓN
   ------------------------------------------------------------------
   demostrar(Meta, Arbol) resuelve Meta igual que Prolog (resolución
   SLD con unificación y retroceso) y además construye el árbol:
     hecho(M)               M está en la base de hechos
     regla(M, Cuerpo)       M se obtuvo con una regla
     calculo(M)             comparación aritmética (=<, >=, >)
     no_demostrable(M, F)   negación por falla; F = dónde falló M
   ================================================================== */

demostrar(true, verdadero) :- !.
demostrar((A, B), y(ArbolA, ArbolB)) :- !,
    demostrar(A, ArbolA),
    demostrar(B, ArbolB).
demostrar(\+ Meta, no_demostrable(Meta, Fallas)) :- !,
    \+ demostrar(Meta, _),
    fallas(Meta, Fallas).
demostrar(Meta, calculo(Meta)) :-
    predicate_property(Meta, built_in), !,
    call(Meta).
demostrar(Meta, hecho(Meta)) :-
    clause(Meta, true).
demostrar(Meta, regla(Meta, ArbolCuerpo)) :-
    clause(Meta, Cuerpo),
    Cuerpo \== true,
    demostrar(Cuerpo, ArbolCuerpo).

% fallas(Meta, Lista): para cada cláusula de Meta, la primera submeta
% que no se cumple. Si Meta es un hecho que no existe, la lista es [Meta].
fallas(Meta, Fallas) :-
    findall(F,
            ( clause(Meta, Cuerpo),
              ( Cuerpo == true -> F = Meta ; primera_falla(Cuerpo, F) ) ),
            Lista),
    ( Lista == [] -> Fallas = [Meta] ; Fallas = Lista ).

primera_falla((A, B), Falla) :- !,
    (   call(A) -> primera_falla(B, Falla) ; Falla = A ).
primera_falla(A, A).

% aplanar(Arbol, Nivel, Pasos): convierte el árbol en una lista de
% paso(Nivel, Tipo, Meta), fácil de mostrar o de enviar a Python.
aplanar(verdadero, _, []).
aplanar(y(A, B), N, Pasos) :-
    aplanar(A, N, PA),
    aplanar(B, N, PB),
    append(PA, PB, Pasos).
aplanar(hecho(M), N, [paso(N, hecho, M)]).
aplanar(calculo(M), N, [paso(N, calculo, M)]).
aplanar(no_demostrable(M, F), N, [paso(N, no_demostrable(F), M)]).
aplanar(regla(M, Cuerpo), N, [paso(N, regla, M)|Pasos]) :-
    N1 is N + 1,
    aplanar(Cuerpo, N1, Pasos).

% texto_paso(Paso, Texto): una línea legible para personas.
texto_paso(paso(N, Tipo, Meta), Texto) :-
    Sangria is N * 4,
    with_output_to(string(Texto),
        ( forall(between(1, Sangria, _), write(' ')),
          escribir_paso(Tipo, Meta) )).

escribir_paso(hecho, M)   :- escribir(M), write('   <- hecho').
escribir_paso(regla, M)   :- escribir(M), write('   <- regla').
escribir_paso(calculo, M) :- escribir(M), write('   <- cálculo').
escribir_paso(no_demostrable(F), M) :-
    write('no se puede demostrar '), escribir(M),
    write('   <- negación por falla (falla: '), escribir_lista(F), write(')').
escribir_paso(sin_regla, M) :-
    escribir(M), write('   <- ninguna regla aplicable: se inspecciona por defecto').

escribir(T) :-
    \+ \+ ( numbervars(T, 0, _),
            write_term(T, [quoted(true), numbervars(true)]) ).

escribir_lista([X]) :- !, escribir(X).
escribir_lista([X|Xs]) :- escribir(X), write(' / '), escribir_lista(Xs).


/* ==================================================================
   8. HERRAMIENTAS PARA LA DEMO Y LA DEFENSA
   ================================================================== */

% explicar(P): resumen completo de la decisión para el pedido P.
explicar(P) :-
    (   pedido(P)
    ->  decidir(P, Accion, Pasos),
        acciones_candidatas(P, Candidatas),
        findall(C, contradiccion(P, C), C0),      sort(C0, Contradicciones),
        findall(F, falta_dato_critico(P, F), F0), sort(F0, Faltantes),
        format("Pedido: ~w~nDecisión: ~w~n", [P, Accion]),
        format("Acciones demostrables (por prioridad): ~w~n", [Candidatas]),
        format("Contradicciones: ~w~nDatos críticos faltantes: ~w~n", [Contradicciones, Faltantes]),
        format("Justificación:~n"),
        forall(member(Paso, Pasos), (texto_paso(Paso, T), format("    ~s~n", [T])))
    ;   format("No existe el pedido ~q.~n", [P])
    ).

% porque(P, A): muestra por qué A es candidata para P, o dice que no lo es.
porque(P, Accion) :-
    (   once(demostrar(accion_candidata(P, Accion), Arbol))
    ->  aplanar(Arbol, 0, Pasos),
        forall(member(Paso, Pasos), (texto_paso(Paso, T), format("~s~n", [T])))
    ;   format("No se puede demostrar accion_candidata(~q, ~q).~n", [P, Accion]),
        format("Revisa con: ?- por_que_no(accion_candidata(~q, ~q)).~n", [P, Accion])
    ).

% por_que_no(Meta): explica por qué Meta NO se puede demostrar, bajando
% hasta 4 niveles por la primera condición que falla de cada regla.
por_que_no(Meta) :-
    (   demostrar(Meta, _)
    ->  format("Sí se puede demostrar: "), escribir(Meta), nl
    ;   por_que_no(Meta, 0)
    ).

por_que_no(Meta, Nivel) :-
    Sangria is Nivel * 4,
    forall(between(1, Sangria, _), write(' ')),
    write('no se cumple: '), escribir(Meta),
    (   Meta = (\+ Positiva)
    ->  write('   (porque SÍ se puede demostrar '), escribir(Positiva), write(')')
    ;   true
    ),
    nl,
    (   Nivel < 4,
        \+ predicate_property(Meta, built_in),
        \+ Meta = (\+ _)
    ->  fallas(Meta, Fallas),
        N1 is Nivel + 1,
        forall(( member(F, Fallas), F \== Meta ), por_que_no(F, N1))
    ;   true
    ).
