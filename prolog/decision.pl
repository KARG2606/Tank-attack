% =========================
% Tank-Attack — Decisión táctica en Prolog
%
% Python sincroniza el estado del tablero antes de cada consulta:
%   - retractall de todos los hechos dinámicos
%   - assertz de la fotografía actual (tanques, jugador, objetivos)
%
% Luego pregunta:
%   decidir_accion(IdTanque, Accion).
%
% Devuelve: atacar | defender | emboscar | retroceder | patrullar
% =========================

:- dynamic muro/2.
:- dynamic tanque/4.        % tanque(Id, X, Y, Tipo).
:- dynamic jugador/2.       % jugador(X, Y).
:- dynamic objetivo/3.      % objetivo(IdObj, X, Y).
:- dynamic vida_baja_flag/1.% vida_baja_flag(IdTanque).
:- dynamic jugador_detectado/2. % jugador_detectado(X, Y).

% =========================
% Distancia Manhattan
% =========================

distancia(X1, Y1, X2, Y2, D) :-
    D is abs(X1 - X2) + abs(Y1 - Y2).

% =========================
% Predicados auxiliares
% =========================

% cerca_de_jugador(+IdTanque)
% Verdadero si el tanque está a distancia Manhattan <= 5 del jugador.
cerca_de_jugador(Id) :-
    tanque(Id, Tx, Ty, _),
    jugador(Jx, Jy),
    distancia(Tx, Ty, Jx, Jy, D),
    D =< 5.

% en_rango_deteccion(+IdTanque)
% Más permisivo que cerca_de_jugador, para detectar antes de atacar.
en_rango_deteccion(Id) :-
    tanque(Id, Tx, Ty, _),
    jugador(Jx, Jy),
    distancia(Tx, Ty, Jx, Jy, D),
    D =< 8.

% objetivo_amenazado(?IdObj)
% Verdadero si algún objetivo tiene al jugador a 7 celdas o menos.
objetivo_amenazado(IdObj) :-
    objetivo(IdObj, Ox, Oy),
    jugador(Jx, Jy),
    distancia(Ox, Oy, Jx, Jy, D),
    D =< 7.

% vida_baja(+IdTanque)
% Python puede marcar tanques con vida baja vía assertz(vida_baja_flag(Id)).
vida_baja(Id) :-
    vida_baja_flag(Id).

% =========================
% Coordinación (puntos extra)
%
% Cuando un enemigo ve al jugador asienta jugador_detectado(X, Y).
% Otros enemigos consultan ese hecho para emboscar coordinadamente.
% =========================

avistar_jugador(Id) :-
    cerca_de_jugador(Id),
    jugador(Jx, Jy),
    retractall(jugador_detectado(_, _)),
    assertz(jugador_detectado(Jx, Jy)).

aliado_avisto(Id) :-
    tanque(Id, _, _, _),
    jugador_detectado(_, _).

% =========================
% decidir_accion/2
%
% Las cláusulas se evalúan en orden; la primera que se cumple gana.
% =========================

% 1) retroceder si la vida está baja (autopreservación)
decidir_accion(Id, retroceder) :-
    vida_baja(Id), !.

% 2) atacar si el tanque está cerca del jugador
decidir_accion(Id, atacar) :-
    cerca_de_jugador(Id), !.

% 3) defender si su objetivo está amenazado
decidir_accion(Id, defender) :-
    tanque(Id, _, _, _),
    objetivo_amenazado(_),
    !.

% 4) emboscar si un aliado avistó al jugador y este tanque es flanqueador
decidir_accion(Id, emboscar) :-
    tanque(Id, _, _, 3),
    aliado_avisto(Id),
    !.

% 5) emboscar si está en rango de detección
decidir_accion(Id, emboscar) :-
    en_rango_deteccion(Id), !.

% 6) patrullar por defecto
decidir_accion(_, patrullar).
