% =========================
% PATH ENTRY POINT
% =========================

path(Start, Goal, Path) :-
    dfs(Start, Goal, [Start], RevPath, 0),
    reverse(RevPath, Path).

% =========================
% DFS CON LIMITE
% =========================

dfs(Goal, Goal, Visited, Visited, _).

dfs(Current, Goal, Visited, Path, Depth) :-
    Depth < 2000,
    connected(Current, Next),
    \+ member(Next, Visited),
    D2 is Depth + 1,
    dfs(Next, Goal, [Next|Visited], Path, D2).

% =========================
% HEURÍSTICA (MANHATTAN)
% =========================

heuristic(A, B, Cost) :-
    split_node(A, Ax, Ay),
    split_node(B, Bx, By),
    Cost is abs(Ax - Bx) + abs(Ay - By).

% =========================
% CONVERTIR "x_y"
% =========================

split_node(Node, X, Y) :-
    atomic_list_concat([Xs, Ys], '_', Node),
    number_string(X, Xs),
    number_string(Y, Ys).