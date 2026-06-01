import os
import random

from game.constants import TILE_SIZE

from entities.objective import ObjetivoTipo1, ObjetivoTipo2
from entities.enemy_tank import EnemyTank


class GeneradorAleatorio:
    """
    Reubica objetivos y enemigos en celdas libres aleatorias.

    Estrategia:
    - El .txt define los muros y la posición inicial del jugador.
    - El conteo de objetivos (por tipo) se toma del .txt cargado.
    - Cada objetivo es custodiado por exactamente un enemigo de tipo
      aleatorio (1, 2 o 3). Los enemigos placeholder del .txt se ignoran.

    Semilla:
    - Si se pasa `seed`, se usa esa.
    - Si no, se lee la variable de entorno TANK_SEED.
    - Si tampoco existe, se usa entropía del sistema (no reproducible).
    """

    MIN_DIST_TO_PLAYER = 6

    def __init__(self, seed=None):

        if seed is None:
            env_seed = os.environ.get("TANK_SEED")
            if env_seed is not None and env_seed.strip() != "":
                try:
                    seed = int(env_seed)
                except ValueError:
                    seed = env_seed

        self._seed = seed
        self._rng = random.Random(seed)

    @property
    def seed(self):
        return self._seed

    def aleatorizar_nivel(self, level_loader):

        cols = level_loader.map_width
        rows = level_loader.map_height

        # Conteo a respetar (definido por el .txt).
        n_tipo1 = sum(
            1 for o in level_loader.objectives if o.tipo == 1
        )
        n_tipo2 = sum(
            1 for o in level_loader.objectives if o.tipo == 2
        )
        n_objetivos = n_tipo1 + n_tipo2

        wall_cells = self._wall_cells(level_loader)

        player_cell = self._player_cell(level_loader)

        if player_cell == (-1, -1):
            raise RuntimeError(
                "El mapa no tiene posición de jugador (P). "
                "No se puede aleatorizar."
            )

        # BFS desde el jugador: solo celdas alcanzables son válidas.
        reachable = self._bfs_reachable(
            player_cell, wall_cells, cols, rows
        )

        # Celdas libres = alcanzables, no muro, no jugador, distancia mínima.
        libres = []
        for (x, y) in reachable:
            if (x, y) == player_cell:
                continue
            if self._manhattan(
                (x, y), player_cell
            ) < self.MIN_DIST_TO_PLAYER:
                continue
            libres.append((x, y))

        self._rng.shuffle(libres)

        if len(libres) < n_objetivos * 2:
            raise RuntimeError(
                "Mapa inválido o muy lleno: solo "
                f"{len(libres)} celdas alcanzables disponibles para "
                f"{n_objetivos} objetivos y {n_objetivos} enemigos. "
                "Revisa el .txt — quizá el jugador está aislado."
            )

        level_loader.objectives.clear()
        level_loader.enemies.clear()

        # Coloca objetivos.
        for _ in range(n_tipo1):
            cx, cy = libres.pop()
            level_loader.objectives.append(
                ObjetivoTipo1(
                    cx * TILE_SIZE, cy * TILE_SIZE, TILE_SIZE
                )
            )

        for _ in range(n_tipo2):
            cx, cy = libres.pop()
            level_loader.objectives.append(
                ObjetivoTipo2(
                    cx * TILE_SIZE, cy * TILE_SIZE, TILE_SIZE
                )
            )

        # Coloca un enemigo de tipo aleatorio por cada objetivo.
        for _ in range(n_objetivos):
            cx, cy = libres.pop()
            tipo = self._rng.choice([1, 2, 3])
            level_loader.enemies.append(
                EnemyTank(
                    cx * TILE_SIZE,
                    cy * TILE_SIZE,
                    TILE_SIZE,
                    enemy_type=tipo,
                )
            )

    def _wall_cells(self, level_loader):
        cells = set()
        for w in level_loader.walls:
            cells.add(
                (w.rect.x // TILE_SIZE, w.rect.y // TILE_SIZE)
            )
        return cells

    @staticmethod
    def _bfs_reachable(start, wall_cells, cols, rows):
        """
        Devuelve el conjunto de celdas alcanzables desde `start`
        moviéndose en 4 direcciones sin atravesar muros.
        """
        visited = {start}
        frontier = [start]
        while frontier:
            cx, cy = frontier.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if (nx, ny) in visited:
                    continue
                if nx < 0 or ny < 0 or nx >= cols or ny >= rows:
                    continue
                if (nx, ny) in wall_cells:
                    continue
                visited.add((nx, ny))
                frontier.append((nx, ny))
        return visited

    def _player_cell(self, level_loader):
        if not level_loader.player:
            return (-1, -1)
        p = level_loader.player
        return (p.rect.x // TILE_SIZE, p.rect.y // TILE_SIZE)

    @staticmethod
    def _manhattan(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
