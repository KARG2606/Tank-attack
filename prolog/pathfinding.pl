path(Start, Goal, Path) :-
    dfs(Start, Goal, [Start], RevPath, 0),
    reverse(RevPath, Path),
    !.

dfs(Goal, Goal, Visited, Visited, _) :- !.

dfs(Current, Goal, Visited, Path, Depth) :-

    Depth < 12,

    connected(Current, Next),

    \+ member(Next, Visited),

    NewDepth is Depth + 1,

    dfs(
        Next,
        Goal,
        [Next|Visited],
        Path,
        NewDepth
    ).