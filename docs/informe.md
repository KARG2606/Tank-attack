# Tank-Attack

## Informe de diseño e implementación

**Proyecto 2 — Paradigma Lógico y Orientado a Objetos**

Lenguajes de Programación · 2026

Instituto Tecnológico de Costa Rica · Sede Regional San Carlos

---

| | |
|---|---|
| **Estudiante 1** | Angie Herrera — Carné 2020035640 |
| **Estudiante 2** | Kevin Rivera — Carné 2024157337|
| **Profesor** | Oscar Víquez Acuña |
| **Fecha de entrega** | 2 de junio de 2026 |

---

## Tabla de contenidos

1. Introducción
2. Descripción del problema
3. Decisiones de diseño
4. Arquitectura general
5. Diagrama de clases
6. Implementación orientada a objetos
7. Implementación lógica (Prolog)
8. Heurística usada en DFS
9. Coordinación táctica (puntos extra)
10. Manual de usuario
11. Manual técnico
12. Pruebas realizadas
13. Conclusiones
14. Limitaciones y mejoras futuras
15. Referencias

---

## 1. Introducción

Este proyecto implementa **Tank-Attack**, un videojuego de tanques que combina dos paradigmas de programación. La parte gráfica, el motor del juego y las entidades se construyen en **Python con Pygame** siguiendo el paradigma **Orientado a Objetos**. La inteligencia artificial de los enemigos —decisiones tácticas y cálculo de rutas— se implementa en **SWI-Prolog**, comunicado con Python mediante **PySwip**.

El objetivo del proyecto es demostrar cómo dos paradigmas con filosofías opuestas (estado mutable vs. relaciones declarativas; flujo imperativo vs. unificación) pueden cooperar en un mismo producto, asignando a cada uno la parte del problema en la que sobresale.

---

## 2. Descripción del problema

El jugador controla un tanque que debe destruir los **objetivos primarios** de cada nivel. Estos objetivos son custodiados por **tanques enemigos**, cada uno con un comportamiento distinto. El juego termina cuando el jugador destruye todos los objetivos del último nivel (victoria) o cuando pierde sus tres vidas en un nivel (derrota).

Características fundamentales requeridas por el enunciado:

- Hasta 3 niveles, con **colocación aleatoria** de objetivos y enemigos.
- **Dos tipos** de objetivos primarios.
- **Tres tipos** de tanques enemigos con capacidades distintas.
- Los enemigos disparan **solo cuando están cerca** del jugador.
- Existen **muros** indestructibles en el borde y dentro del tablero.
- El jugador tiene **3 vidas por nivel**.
- Movimiento únicamente en las **4 direcciones cardinales**.
- Las **balas son objetos** con su propio ciclo de vida y colisiones.
- Los actores móviles se ejecutan con la **fluidez** propia de un juego.
- El motor **OO consulta al motor lógico** en tiempo de ejecución para decisiones y rutas.
- Existe un **editor de pantallas**.

---

## 3. Decisiones de diseño

### 3.1 Stack tecnológico

| Componente | Decisión | Razón |
|---|---|---|
| Lenguaje OO | Python 3.9 | Sintaxis clara, ecosistema maduro para 2D |
| Motor lógico | SWI-Prolog 10 | Estándar de facto, predicados dinámicos sólidos |
| Puente OO ↔ Prolog | PySwip 0.3 | Integración madura, llamada directa a `assertz`/`query` |
| Interfaz gráfica | Pygame 2.6 | Liviano, ideal para juegos 2D basados en cuadrícula |
| Concurrencia | Game loop síncrono + `query_in_progress` | Suficiente para 60 FPS sin contención |

### 3.2 Tablero

- Dimensiones: **40 columnas × 22 filas** (880 celdas).
- Unidad lógica: **la celda**. Tanto Python como Prolog razonan sobre celdas.
- Tamaño en píxeles por celda: **32 px** (`TILE_SIZE`), por lo que el área del mapa es 1280×704 px dentro de una superficie lógica de 1280×720.

### 3.3 Definición de "cerca"

Implementada en Prolog como el predicado `cerca_de_jugador/1`:

> Un tanque está "cerca" del jugador si la distancia Manhattan entre ambos es **menor o igual a 5 celdas**.

Cuando se cumple, el predicado `decidir_accion/2` devuelve `atacar`, lo cual activa el disparo de la bala en Python.

### 3.4 Velocidades

Definidas en [`game/constants.py`](../game/constants.py) y en los `__init__` de las entidades:

| Elemento | Velocidad | Notas |
|---|---|---|
| Jugador | 2 px/frame | Ágil, controlado por teclado |
| Enemigo ASSAULT (tipo 1) | 3 px/frame | Rápido, frágil |
| Enemigo DEFENDER (tipo 2) | 2 px/frame | Equilibrado |
| Enemigo FLANKER (tipo 3) | 2 px/frame | Lento pero embosca |
| Balas | 6 px/frame | Más rápidas que los tanques |
| Cooldown disparo enemigo | 60 / 90 / 120 frames | Por tipo |
| Consulta a Prolog (decisión) | 60 frames (1 s a 60 FPS) | Por tanque enemigo |

### 3.5 Formato del archivo de pantallas

Cada nivel es un `.txt` donde cada carácter representa una celda:

| Carácter | Significado |
|---|---|
| `#` | Muro indestructible |
| `P` | Posición inicial del jugador |
| `O` | Objetivo primario tipo 1 (amarillo) |
| `Q` | Objetivo primario tipo 2 (rosa) |
| `1` | Enemigo placeholder tipo 1 |
| `2` | Enemigo placeholder tipo 2 |
| `3` | Enemigo placeholder tipo 3 |
| `.` | Celda vacía transitable |

### 3.6 Aleatoriedad

Estrategia **mixta**:

- Los **muros** se quedan tal cual en el `.txt` (preserva el diseño del nivel).
- Las **posiciones de los objetivos** se reubican aleatoriamente respetando el conteo del `.txt` (número de `O` y de `Q`).
- Por cada objetivo se coloca **un único enemigo** en una celda aleatoria, con el **tipo (1/2/3) elegido al azar**.
- Se garantiza que cada objetivo y cada enemigo se ubica en una celda **alcanzable** desde el jugador (BFS de validación).
- La semilla es configurable vía la variable de entorno `TANK_SEED` para reproducir bugs.

---

## 4. Arquitectura general

El sistema se organiza en cinco subsistemas que se comunican mediante interfaces explícitas.

```
┌──────────────────────────────────────────────────────────────┐
│                       GameManager (loop)                     │
│  menú → playing → level_clear → win/game_over                │
└──────┬──────────────────────────────────────────────┬────────┘
       │                                              │
       │ a) ciclo de 60 frames                        │ b) ciclo de 1 s
       ▼                                              ▼
┌─────────────────────────────┐   ┌────────────────────────────┐
│ Entidades (Python OO)       │   │  Prolog Manager (puente)   │
│ - PlayerTank                │   │                            │
│ - EnemyTank (FSM + roles)   │◀──┤  sync_state(level)         │
│ - Bullet                    │   │  consultar_accion(id)      │
│ - Wall, Objetivo1/2         │   │  find_path(s, g)           │
└──────────────┬──────────────┘   └────────────┬───────────────┘
               │                                │
               │                                ▼
               │                  ┌────────────────────────────┐
               │                  │   SWI-Prolog (vía PySwip)  │
               │                  │  decision.pl               │
               │                  │   decidir_accion/2         │
               │                  │   cerca_de_jugador/1       │
               │                  │   objetivo_amenazado/1     │
               │                  │  pathfinding.pl            │
               │                  │   path/3                   │
               │                  │   dfs/5  (con heurística)  │
               │                  └────────────────────────────┘
               │
               │  c) coordinación  d) ruta local
               ▼                   ▼
┌─────────────────────────────┐   ┌────────────────────────────┐
│  TacticalManager (Python)   │   │  Pathfinding (Python BFS)  │
│  Memoria compartida del     │   │  Fallback de bajo nivel    │
│  último avistamiento del    │   │  para path-following frame │
│  jugador. Offsets tácticos. │   │  a frame.                  │
└─────────────────────────────┘   └────────────────────────────┘
```

### Ciclo de ejecución de un enemigo en cada update

1. `tactical_manager.update(player)` — refresca la memoria del último avistamiento.
2. **Cada 60 frames**, `GameManager` llama a `prolog_manager.sync_state(level_loader)`:
   - `retractall` de todos los hechos `tanque/4`, `jugador/2`, `objetivo/3`, `jugador_detectado/2`.
   - `assertz` con la fotografía actual del nivel (todas las entidades, sus posiciones en celdas).
3. Por cada enemigo se llama a `prolog_manager.consultar_accion(idx)` que devuelve `atacar | defender | emboscar | retroceder | patrullar`.
4. Si la acción es `atacar`, ese tanque enemigo publica `jugador_detectado(X,Y)` para que los aliados puedan emboscar coordinadamente.
5. Dentro de `enemy.update(...)`, la función `_aplicar_accion_prolog` traduce la acción a un estado FSM y un destino. Si la acción es `patrullar` o no se aplica, cae a la lógica específica del rol.
6. `pathfinding.find_path(start, goal, walls, w, h)` (BFS en Python) calcula la ruta entre dos celdas.
7. `enemy.follow_path(tile_size)` avanza al siguiente nodo de la ruta.
8. Si el estado es `ATTACK`/`HOLD` y la distancia es menor o igual al `attack_range`, el enemigo dispara una bala que se devuelve al `GameManager` para colisiones.

---

## 5. Diagrama de clases

Las clases del proyecto se agrupan en cinco capas:

```
┌─────────────────────────────────────────────────────────────┐
│ CONTROL DEL JUEGO                                           │
│   GameManager  ─────────────────► LevelLoader               │
│   ▲                                  │                      │
│   └──────────────┐                   ▼                      │
│                  │             Lista<Entidad>               │
└──────────────────┼──────────────────┼──────────────────────┘
                   │                  │
┌──────────────────┴──────────────────┼──────────────────────┐
│ ENTIDADES (jerarquía)               │                      │
│                                     ▼                      │
│  «abstract»                    Entidad                      │
│      ▲       ▲       ▲          ▲                          │
│      │       │       │          │                          │
│   Muro   Objetivo   Bullet   Tanque                        │
│         ╱     ╲                ▲                            │
│  ObjetivoT1  ObjetivoT2   PlayerTank   EnemyTank           │
│                                          (roles ASSAULT,    │
│                                          DEFENDER, FLANKER) │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ INTELIGENCIA ARTIFICIAL Y LÓGICA                            │
│                                                             │
│   AIController          TacticalManager                     │
│        │                   │                                │
│        └─► PrologManager ◄─┘                                │
│                  │                                          │
│                  ▼                                          │
│         pathfinding.pl  +  decision.pl                      │
│                                                             │
│   Pathfinding (BFS en Python) — usado por EnemyTank        │
│   PrologBridge (adaptador delgado)                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SOPORTE                                                     │
│   Assets         (carga y rotación de sprites)             │
│   GeneradorAleatorio (BFS + reubicación aleatoria)         │
│   MapEditor      (editor visual de pantallas)              │
│   EnemyState (Enum: PATROL, ATTACK, DEFEND, RETREAT, ...)  │
└─────────────────────────────────────────────────────────────┘
```

### Relaciones clave

| Origen | Relación | Destino |
|---|---|---|
| `EnemyTank`, `PlayerTank`, `Bullet`, `Wall`, `Objective` | herencia | `Entity` |
| `ObjetivoTipo1`, `ObjetivoTipo2` | herencia | `Objective` |
| `GameManager` | composición | `LevelLoader`, `PrologManager`, `TacticalManager`, `AIController`, `Pathfinding`, `Assets`, `GeneradorAleatorio` |
| `EnemyTank.update(...)` | usa | `AIController`, `TacticalManager`, `Pathfinding`, `PrologManager` (vía atributo `prolog_action`) |
| `PrologManager` | usa | `pathfinding.pl`, `decision.pl` (vía PySwip) |
| `GeneradorAleatorio` | reubica | `Objective`, `EnemyTank` |

### Encapsulamiento

El proyecto sigue las convenciones de Python para encapsulamiento:

- Atributos **públicos**: estado visible que otras clases consultan (ej. `enemy.rect`, `player.lives`, `objetivo.tipo`).
- Atributos **protegidos** (`_`): estado interno con semántica controlada (ej. `_lives`, `_spawn_x`, `_shoot_cooldown`, `_invuln_timer`).
- Propiedades (`@property`): exposición de lectura controlada (ej. `lives`, `is_invulnerable`, `seed`, `tipo`).

---

## 6. Implementación orientada a objetos

### 6.1 Jerarquía de entidades

`Entity` provee la base común: posición, tamaño, color, `pygame.Rect` y método `draw`. Sus subclases agregan comportamiento específico.

**`PlayerTank`** ([`entities/player_tank.py`](../entities/player_tank.py)) — Maneja la entrada del teclado en cuatro direcciones, dispara con `Espacio`, mantiene un cooldown de 45 frames entre disparos, tiene 3 vidas y un timer de invulnerabilidad post-respawn (90 frames). Si recibe daño se reubica en su `_spawn_x, _spawn_y` con `_invuln_timer = 90`.

**`EnemyTank`** ([`entities/enemy_tank.py`](../entities/enemy_tank.py)) — Es la entidad más compleja:

- Tres **roles** según `enemy_type`:
  - Tipo 1 → ASSAULT (rojo): se alerta a 150 px, ataca a < 140 px, persigue hasta `max_chase_distance = 250 px` desde su spawn.
  - Tipo 2 → DEFENDER (azul): patrulla alrededor de su objetivo en un radio de 80 px, ataca al jugador solo si entra en el `defense_radius = 220 px` del objetivo.
  - Tipo 3 → FLANKER (morado): detecta a mayor distancia (×1.5) y emboscar usando offsets tácticos del `TacticalManager`.
- Una **FSM** de 7 estados: `PATROL`, `DEFEND`, `ATTACK`, `RETREAT`, `HOLD`, `AMBUSH`, `SEARCH`.
- Una **cola de ruta** (`current_path`, `path_index`) que sigue paso a paso mediante `follow_path`.
- Timers: `repath_timer` (60 frames entre recálculos de ruta), `ai_timer` (30 frames entre decisiones), `target_lock_timer` (30 frames de lock al objetivo actual), `_shoot_cooldown` (60/90/120 según tipo).
- Disparo: el método `shoot(player)` calcula la dirección hacia el jugador, posiciona la bala en el **borde del cañón** (no en el centro), y devuelve un `Bullet` con `owner="ENEMY"`.

**`Bullet`** — Entidad simple con dirección y velocidad. Se desactiva al colisionar con muros u otras entidades.

**`Objective`** y subclases `ObjetivoTipo1` / `ObjetivoTipo2` — Diferencian el tipo mediante el atributo `_tipo` accesible vía `@property tipo`. Se distinguen visualmente con tints amarillo y rosa.

### 6.2 Control del juego

**`GameManager`** ([`game/game_manager.py`](../game/game_manager.py)) tiene una **máquina de estados de alto nivel**:

```
MENU ─── Enter / clic ──► PLAYING
PLAYING ── objetivos == 0 ──► LEVEL_CLEAR ── Enter ──► PLAYING (nivel++)
                          └── último nivel ──────► WIN
PLAYING ── vidas == 0 ──► GAME_OVER
WIN, GAME_OVER ─── R ──► MENU
```

En cada frame ejecuta:
1. `handle_events()` — teclado, ratón, cierre.
2. `update()` — actualiza jugador, sincroniza Prolog cada 60 frames, actualiza enemigos, mueve balas, resuelve colisiones, evalúa condiciones de fin.
3. `draw()` — dibuja el menú o el nivel + HUD + overlays.

**`LevelLoader`** parsea el `.txt`, crea las entidades y guarda `map_data` para que `PrologManager` pueda generar el grafo.

**`GeneradorAleatorio`** ([`util/generador_aleatorio.py`](../util/generador_aleatorio.py)) hace BFS desde la posición del jugador para construir el conjunto de **celdas alcanzables**. Luego elige aleatoriamente `n_objetivos * 2` celdas distintas (objetivos + sus enemigos custodios) respetando una distancia mínima Manhattan de 6 desde el jugador (para no aparecer encima).

### 6.3 Editor de pantallas

[`ui/editor_pantallas.py`](../ui/editor_pantallas.py) abre una ventana de Pygame que carga un `.txt` (o crea uno en blanco), permite editar cada celda con clic izquierdo (ciclo `. → # → P → O → Q → 1 → 2 → 3`) y validar el mapa antes de guardar. La validación reutiliza el **mismo BFS** que el generador para garantizar que no haya zonas no muro aisladas del jugador.

### 6.4 Sprites

[`game/assets.py`](../game/assets.py) carga las imágenes una sola vez, las escala a 32×32 y pre-rota a las 4 direcciones cardinales. Los objetivos se tintan en amarillo (Tipo 1) y rosa (Tipo 2) usando `BLEND_MULT`. Bajo cada tanque se dibuja un disco semitransparente con el color del rol (rojo, azul, morado o verde) para que el jugador identifique el tipo a la primera vista.

---

## 7. Implementación lógica (Prolog)

La lógica se distribuye en dos archivos: [`prolog/decision.pl`](../prolog/decision.pl) (decisiones tácticas) y [`prolog/pathfinding.pl`](../prolog/pathfinding.pl) (cálculo de rutas).

### 7.1 Hechos dinámicos

`decision.pl` declara:

```prolog
:- dynamic muro/2.
:- dynamic tanque/4.        % tanque(Id, X, Y, Tipo).
:- dynamic jugador/2.       % jugador(X, Y).
:- dynamic objetivo/3.      % objetivo(IdObj, X, Y).
:- dynamic vida_baja_flag/1.
:- dynamic jugador_detectado/2.
```

Python asienta estos hechos con `assertz` en cada `sync_state`. Antes hace `retractall` para evitar acumulación entre ciclos.

### 7.2 Predicados auxiliares

```prolog
distancia(X1, Y1, X2, Y2, D) :-
    D is abs(X1 - X2) + abs(Y1 - Y2).

cerca_de_jugador(Id) :-
    tanque(Id, Tx, Ty, _),
    jugador(Jx, Jy),
    distancia(Tx, Ty, Jx, Jy, D),
    D =< 5.

en_rango_deteccion(Id) :-
    tanque(Id, Tx, Ty, _),
    jugador(Jx, Jy),
    distancia(Tx, Ty, Jx, Jy, D),
    D =< 8.

objetivo_amenazado(IdObj) :-
    objetivo(IdObj, Ox, Oy),
    jugador(Jx, Jy),
    distancia(Ox, Oy, Jx, Jy, D),
    D =< 7.

vida_baja(Id) :- vida_baja_flag(Id).
```

### 7.3 Predicado central de decisión

```prolog
% Las cláusulas se evalúan en orden; la primera que se cumple gana.

decidir_accion(Id, retroceder) :- vida_baja(Id), !.
decidir_accion(Id, atacar)     :- cerca_de_jugador(Id), !.
decidir_accion(Id, defender)   :- tanque(Id, _, _, _), objetivo_amenazado(_), !.
decidir_accion(Id, emboscar)   :- tanque(Id, _, _, 3), aliado_avisto(Id), !.
decidir_accion(Id, emboscar)   :- en_rango_deteccion(Id), !.
decidir_accion(_,  patrullar).
```

Esta es la **única fuente de decisiones de alto nivel**. Python solo ejecuta lo que Prolog determina.

### 7.4 Sincronización Python → Prolog

[`prolog/prolog_manager.py`](../prolog/prolog_manager.py) expone:

```python
def sync_state(self, level_loader):
    list(self.prolog.query("retractall(tanque(_,_,_,_))"))
    list(self.prolog.query("retractall(jugador(_,_))"))
    list(self.prolog.query("retractall(objetivo(_,_,_))"))
    list(self.prolog.query("retractall(jugador_detectado(_,_))"))

    if level_loader.player:
        jx = level_loader.player.rect.centerx // TILE_SIZE
        jy = level_loader.player.rect.centery // TILE_SIZE
        self.prolog.assertz(f"jugador({jx},{jy})")

    for idx, enemy in enumerate(level_loader.enemies):
        ex = enemy.rect.centerx // TILE_SIZE
        ey = enemy.rect.centery // TILE_SIZE
        self.prolog.assertz(
            f"tanque(t{idx},{ex},{ey},{enemy.enemy_type})"
        )

    for idx, obj in enumerate(level_loader.objectives):
        ox = obj.rect.centerx // TILE_SIZE
        oy = obj.rect.centery // TILE_SIZE
        self.prolog.assertz(f"objetivo(o{idx},{ox},{oy})")
```

Y la consulta:

```python
def consultar_accion(self, enemy_id):
    query = f"decidir_accion(t{enemy_id}, Accion)"
    result = list(self.prolog.query(query, maxresult=1))
    if result:
        accion = result[0]["Accion"]
        if isinstance(accion, bytes):
            accion = accion.decode("utf-8")
        return str(accion)
    return "patrullar"
```

---

## 8. Heurística usada en DFS

[`prolog/pathfinding.pl`](../prolog/pathfinding.pl):

```prolog
path(Start, Goal, Path) :-
    dfs(Start, Goal, [Start], RevPath, 0),
    reverse(RevPath, Path),
    !.

dfs(Goal, Goal, Visited, Visited, _) :- !.

dfs(Current, Goal, Visited, Path, Depth) :-
    Depth < 200,
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

heuristic(A, B, H) :-
    split_node(A, Ax, Ay),
    split_node(B, Bx, By),
    H is abs(Ax - Bx) + abs(Ay - By).
```

### ¿Por qué Manhattan?

Como los tanques solo se mueven en las **cuatro direcciones cardinales** (no en diagonal), el costo mínimo entre dos celdas es exactamente la **suma de las diferencias en X e Y** —la distancia Manhattan. Esta heurística cumple:

1. **Admisibilidad** — nunca sobrestima el costo real (es el costo de un camino libre, sin muros).
2. **Consistencia** — para celdas adyacentes, `h(n) ≤ 1 + h(vecino)`.

### ¿Cómo se aplica en DFS?

DFS clásico explora todos los vecinos en orden arbitrario. Aquí, en cada llamada recursiva:

1. Se generan los pares `H-Next` para cada vecino libre no visitado.
2. `keysort` los ordena por `H` ascendente (vecinos más cercanos al destino primero).
3. `member(_-Next, Sorted)` recorre los pares en orden, intentando primero los más prometedores.

El resultado es un **best-first DFS**: mantiene la simplicidad de la recursión (no requiere cola de prioridad explícita), pero gracias a la heurística sigue rutas casi óptimas en lugar de serpentear por todo el mapa.

### Resultado experimental

Para una ruta de (1,1) a (10,10) en `maps/level1.txt`:

| Variante | Nodos en la ruta |
|---|---|
| DFS plano sin heurística (versión inicial) | ~180–200 (serpenteo por todo el mapa) |
| DFS con heurística Manhattan (versión final) | 31 (cercano al óptimo 18 = costo Manhattan) |

La heurística reduce el costo de la consulta a Prolog en un orden de magnitud.

### Límite de profundidad

`Depth < 200` evita recursiones infinitas en grafos densos. 200 cubre cualquier ruta razonable en un mapa de 40×22 (880 celdas).

---

## 9. Coordinación táctica (puntos extra)

Implementamos coordinación entre tanques en **dos niveles**: a nivel de hechos Prolog y a nivel de posiciones tácticas en Python.

### 9.1 Coordinación a nivel lógico

Cuando un enemigo recibe la acción `atacar` desde Prolog, `GameManager` ejecuta:

```python
if enemy.prolog_action == "atacar":
    self.prolog_manager.asentar_avistamiento(idx)
```

Internamente esto invoca:

```prolog
avistar_jugador(Id) :-
    cerca_de_jugador(Id),
    jugador(Jx, Jy),
    retractall(jugador_detectado(_, _)),
    assertz(jugador_detectado(Jx, Jy)).
```

A partir de ese momento, **cualquier aliado** puede consultar:

```prolog
aliado_avisto(Id) :-
    tanque(Id, _, _, _),
    jugador_detectado(_, _).
```

Y la cláusula:

```prolog
decidir_accion(Id, emboscar) :-
    tanque(Id, _, _, 3),
    aliado_avisto(Id), !.
```

provoca que **los flanqueadores (tipo 3) pasen a `emboscar` aunque ellos mismos no vean al jugador**, simplemente porque un compañero lo avistó.

### 9.2 Coordinación a nivel de posiciones tácticas

El `TacticalManager` mantiene un arreglo de offsets relativos al jugador:

```python
self.attack_offsets = [
    (0, 0),    # directo
    (-3, 0),   # izquierda
    (3, 0),    # derecha
    (0, -3),   # arriba
    (0, 3),    # abajo
]
```

Cuando un enemigo entra en estado `AMBUSH`, llama a `tactical_manager.get_tactical_target(self, enemies, tile_size)`. El manager:

1. Filtra los enemigos del **mismo tipo** que el actual.
2. Los ordena por posición (para tener un índice determinista).
3. Asigna a este enemigo el offset `attack_offsets[idx % 5]`.
4. Devuelve la posición resultante: `(player.x + offset[0] * tile, player.y + offset[1] * tile)`.

El efecto es que **dos o más flanqueadores que vean al jugador se reparten** las posiciones de embocada en lugar de amontonarse todos en el mismo punto. Visualmente se ve como un cerco coordinado.

---

## 10. Manual de usuario

### Inicio

Al lanzar `python3 main.py` aparece la pantalla de menú con el botón **INICIAR**. Presiona `Enter`, `Espacio` o haz clic.

### Durante el juego

| Tecla | Acción |
|---|---|
| `W` `A` `S` `D` o flechas | Mueve el tanque |
| `Espacio` | Dispara una bala en la dirección actual |
| `R` | Reinicia el nivel desde cero |
| `Esc` | Cierra el juego |

### HUD

- **Arriba izquierda**: vidas restantes (3 por nivel) y objetivos restantes.
- **Arriba derecha**: nivel actual (1/3, 2/3 o 3/3).

### Identificar enemigos

Cada tanque tiene un halo de color bajo el chasis:

- 🟢 verde brillante — tú
- 🔴 rojo — ASSAULT (agresivo de corto alcance)
- 🔵 azul — DEFENDER (custodia su objetivo)
- 🟣 morado — FLANKER (embosca usando coordinación táctica)

### Fin de nivel

- Si destruyes todos los objetivos, aparece **"Nivel N superado"**. Presiona `Enter` o clic para pasar al siguiente.
- Si pierdes las 3 vidas, aparece **GAME OVER**. `R` te lleva al menú.
- Tras superar el nivel 3 sale **¡VICTORIA!**.

### Editor de pantallas

```bash
python3 -m ui.editor_pantallas maps/level1.txt
```

| Acción | Cómo |
|---|---|
| Cambiar contenido de una celda | clic izquierdo (cicla los caracteres válidos) |
| Vaciar una celda | clic derecho |
| Validar | `V` |
| Guardar | `S` |
| Recargar desde disco | `R` |
| Salir | `Esc` |

---

## 11. Manual técnico

### 11.1 Dependencias

- Python 3.9+
- SWI-Prolog 8+
- `pygame == 2.6.1`
- `pyswip == 0.3.3`

### 11.2 Compilación

No requiere compilación. Es código Python interpretado.

### 11.3 Ejecución desde código fuente

```bash
git clone https://github.com/KARG2606/Tank-attack.git
cd Tank-attack
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

### 11.4 Variables de entorno

| Variable | Efecto |
|---|---|
| `TANK_SEED` | Semilla para la randomización (entero) |
| `SWI_HOME_DIR` | Ruta a la instalación de SWI-Prolog (solo si PySwip no la detecta) |
| `DYLD_FALLBACK_LIBRARY_PATH` | Ruta a `libswipl` en macOS |

### 11.5 Cómo modificar la dificultad

- **Velocidades de los tanques**: `SPEED_BY_TYPE` en [`entities/enemy_tank.py`](../entities/enemy_tank.py).
- **Cooldown de disparo**: `SHOOT_COOLDOWN_BY_TYPE` en el mismo archivo.
- **Rango de detección y ataque**: `detection_range`, `attack_range`, `defense_radius` en el `__init__` de `EnemyTank`.
- **Frecuencia de consultas a Prolog**: `_prolog_query_interval` en [`game/game_manager.py`](../game/game_manager.py).
- **Distancia mínima de spawn**: `MIN_DIST_TO_PLAYER` en [`util/generador_aleatorio.py`](../util/generador_aleatorio.py).
- **Definición de "cerca" en Prolog**: el `=< 5` dentro de `cerca_de_jugador/1` en [`prolog/decision.pl`](../prolog/decision.pl).

### 11.6 Cómo agregar un nuevo nivel

1. Crea `maps/level4.txt` con la estructura de muros, la `P` del jugador y N objetivos (`O`/`Q`).
2. Valida con `python3 -m ui.editor_pantallas maps/level4.txt` y presiona `V`.
3. Agrega la ruta a la lista `LEVELS` en [`game/game_manager.py`](../game/game_manager.py).

---

## 12. Pruebas realizadas

| Prueba | Resultado |
|---|---|
| Puente PySwip ↔ SWI-Prolog (`member(X, [1,2,3])`) | ✅ Devuelve los tres elementos |
| Carga de los 3 niveles con validación de alcanzabilidad | ✅ Todas las celdas no muro son alcanzables desde la `P` |
| `GeneradorAleatorio` con semillas distintas | ✅ Reubica objetivos en posiciones diferentes |
| Mapa intencionalmente roto (jugador encerrado) | ✅ El generador lanza `RuntimeError` con mensaje claro |
| Editor: validación de mapas con celdas aisladas | ✅ Bloquea el guardado y muestra el conteo |
| Flujo completo MENU → 3 niveles → WIN | ✅ Transiciones correctas |
| Disparo enemigo en estado ATTACK | ✅ Bala con `owner="ENEMY"` golpea al jugador y resta vidas |
| `decidir_accion` con jugador lejos | ✅ Devuelve `patrullar` o `emboscar` |
| `decidir_accion` con jugador cerca | ✅ Devuelve `atacar` |
| DFS con heurística | ✅ Ruta (1,1)→(10,10) en 31 nodos (vs ~200 sin heurística) |
| Coordinación: dos FLANKERS ven al jugador | ✅ Se reparten offsets tácticos distintos |

---

## 13. Conclusiones

1. **El paradigma lógico encaja perfectamente con la toma de decisiones tácticas.** Reglas como "atacar si está cerca o un aliado lo vio" se expresan en una línea de Prolog, mientras que en Python requerirían varios condicionales y estado mutable difícil de seguir.
2. **La heurística Manhattan transforma DFS en una herramienta práctica.** Sin ella, las rutas serpenteaban por todo el mapa; con `keysort` sobre los vecinos pre-evaluados, las rutas son casi óptimas con un costo computacional bajo.
3. **El patrón `retractall` + `assertz` antes de cada consulta es esencial.** Acumular hechos viejos llevaba a respuestas inconsistentes en las primeras pruebas. Sincronizar el estado completo antes de cada query es la única forma fiable de mantener Prolog actualizado.
4. **Separar `PrologManager` del resto del código** permitió reemplazar predicados y agregar nuevos sin tocar la lógica del juego. La interfaz `sync_state` / `consultar_accion` es muy estable.
5. **La coordinación táctica es valiosa en dos niveles.** A nivel lógico (`jugador_detectado` + `aliado_avisto`) controla la decisión "qué quiero hacer". A nivel de Python (`TacticalManager` con offsets) controla "dónde me ubico". Ambos se complementan.

---

## 14. Limitaciones y mejoras futuras

- **El pathfinding en caliente es Python BFS, no Prolog DFS.** Aunque `prolog/pathfinding.pl` está implementado y probado, los enemigos usan `logic/pathfinding.py` para el `repath` cada 60 frames porque BFS es más rápido para grafos densos y no bloquea el loop de Pygame. Una mejora sería usar Prolog para el path inicial y BFS como ajuste fino, manteniendo el DFS heurístico como demostración del paradigma lógico.
- **El estado `vida_baja` no se rastrea por enemigo.** Hoy `vida_baja/1` necesita que Python asienta `vida_baja_flag/1`. Una mejora natural es darles a los tanques enemigos un sistema de hits y declararlos "vida baja" cuando reciban N golpes.
- **No hay sonido**. Las balas y los impactos serían más impactantes con efectos de audio.
- **Sin animación de explosión**. Al destruir un objetivo o enemigo simplemente desaparece.
- **Un único hilo**. La consulta a Prolog cada 60 frames toma tiempo perceptible. Mover las consultas a un hilo separado eliminaría el ocasional micro-stutter.
- **Los sprites no rotan suavemente.** Solo pre-calculamos las 4 direcciones cardinales. Para 8 direcciones bastaría agregar las diagonales.

---

## 15. Referencias

- Wielemaker, J. *SWI-Prolog Manual*. <https://www.swi-prolog.org/pldoc/man>
- Tekol, Y. *PySwip Documentation*. <https://github.com/yuce/pyswip>
- Shinners, P. *Pygame Documentation*. <https://www.pygame.org/docs/>
- Russell, S., Norvig, P. *Artificial Intelligence: A Modern Approach*, 4ª ed. — Capítulos 3 y 4 (búsqueda informada, heurísticas admisibles).
- Sterling, L., Shapiro, E. *The Art of Prolog*, 2ª ed. — Capítulo sobre meta-interpretación y hechos dinámicos.
- Víquez Acuña, O. *Tarea 2 — Tank-Attack* (enunciado del proyecto). ITCR, 2026.

---

## Anexo A. Capturas de pantalla

> **NOMBRE_AQUÍ**: agregar capturas reales de:
>
> 1. Pantalla de menú con botón INICIAR.
> 2. Nivel 1 en juego (mostrando los 4 colores de halo).
> 3. Disparo del enemigo y bala en vuelo.
> 4. HUD con vidas reducidas y pantalla de respawn (parpadeo).
> 5. Overlay "Nivel superado" y overlay "VICTORIA".
> 6. Editor de pantallas con el mapa cargado y la barra de estado verde "Mapa válido".

## Anexo B. Estructura de archivos relevantes

```
Tank-attack/
├── main.py
├── requirements.txt
├── README.md
├── ai/enemy_state.py
├── entities/{entity, wall, objective, player_tank, enemy_tank, bullet}.py
├── game/{constants, collision_manager, level_loader, assets, game_manager}.py
├── logic/{ai_controller, pathfinding, prolog_bridge, tactical_manager}.py
├── prolog/{prolog_manager.py, pathfinding.pl, decision.pl}
├── util/generador_aleatorio.py
├── ui/editor_pantallas.py
├── maps/level{1,2,3}.txt
├── resourses/{jugador, enemigo1/2/3, objetivo}.png   (y muro.jpg, bg.jpg)
└── docs/informe.md
```
