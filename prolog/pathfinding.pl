% =========================
% Tank-Attack — Pathfinding en Prolog
% DFS con heurística Manhattan aplicada en el orden de expansión.
% =========================

% Nodo: átomo 'X_Y' (ej. '5_12').
% Hechos: connected(Origen, Destino) asertado dinámicamente desde Python.

:- dynamic connected/2.

% =========================
% Predicado principal: path/3
% =========================

path(Start, Goal, Path) :-
    dfs(Start, Goal, [Start], RevPath, 0),
    reverse(RevPath, Path),
    !.

% =========================
% DFS con corte de profundidad y heurística
% =========================

dfs(Goal, Goal, Visited, Visited, _) :- !.

dfs(Current, Goal, Visited, Path, Depth) :-
    Depth < 200,
    % Genera vecinos ordenados por distancia Manhattan al objetivo
    % (best-first sobre DFS — cumple el requisito de "DFS con heurística").
    findall(H-Next,
        ( connected(Current, Next),
          \+ member(Next, Visited),
          heuristic(Next, Goal, H)
        ),
        Pairs),
    keysort(Pairs, Sorted),
    member(_-Next, Sorted),
    NewDepth is Depth + 1,
    dfs(Next, Goal, [Next|Visited], Path, NewDepth).

% =========================
% Heurística Manhattan
% =========================

heuristic(A, B, H) :-
    split_node(A, Ax, Ay),
    split_node(B, Bx, By),
    H is abs(Ax - Bx) + abs(Ay - By).

% =========================
% Utilidad: parsea 'X_Y' a enteros
% =========================

split_node(Node, X, Y) :-
    atom_string(Node, S),
    split_string(S, "_", "", [Xs, Ys]),
    number_string(X, Xs),
    number_string(Y, Ys).
