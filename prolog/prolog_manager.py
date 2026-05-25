from pyswip import Prolog
from game.constants import TILE_SIZE


class PrologManager:

    def __init__(self):

        self.prolog = Prolog()
        self.prolog.consult("prolog/pathfinding.pl")

        # Cache de rutas
        self.path_cache = {}

        self.query_in_progress = False

    # =========================
    # LIMPIAR HECHOS
    # =========================

    def clear_facts(self):
        list(self.prolog.query("retractall(connected(_, _))"))

    # =========================
    # GENERAR GRAFO
    # =========================

    def generate_graph(self, level_loader):

        self.clear_facts()

        walls = set()

        for wall in level_loader.walls:

            grid_x = wall.rect.x // TILE_SIZE
            grid_y = wall.rect.y // TILE_SIZE

            walls.add((grid_x, grid_y))

        rows = len(level_loader.map_data)
        cols = len(level_loader.map_data[0])

        for y in range(rows):
            for x in range(cols):

                if (x, y) in walls:
                    continue

                current = f"{x}_{y}"

                directions = [
                    (1, 0),
                    (-1, 0),
                    (0, 1),
                    (0, -1)
                ]

                for dx, dy in directions:

                    nx = x + dx
                    ny = y + dy

                    if 0 <= nx < cols and 0 <= ny < rows:

                        if (nx, ny) not in walls:

                            neighbor = f"{nx}_{ny}"

                            self.prolog.assertz(
                                f"connected('{current}','{neighbor}')"
                            )

    # =========================
    # PATHFINDING
    # =========================

    def find_path(self, start_x, start_y, goal_x, goal_y):

        if self.query_in_progress:
            return []

        self.query_in_progress = True

        try:

            cache_key = (
                start_x,
                start_y,
                goal_x,
                goal_y
            )

            if cache_key in self.path_cache:

                self.query_in_progress = False
                return self.path_cache[cache_key]

            start = f"'{start_x}_{start_y}'"
            goal = f"'{goal_x}_{goal_y}'"

            query = f"path({start},{goal},Path)"

            result = self.prolog.query(
                query,
                maxresult=1
            )

            result = list(result)

            if result:

                path = result[0]["Path"]

                if isinstance(path, list):

                    self.path_cache[cache_key] = path

                    self.query_in_progress = False

                    return path

        except Exception as e:

            print("PROLOG QUERY ERROR:", e)

        self.query_in_progress = False

        return []

    # =========================
    # LIMPIAR CACHE
    # =========================

    def clear_cache(self):
        self.path_cache.clear()