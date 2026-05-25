from pyswip import Prolog
from game.constants import TILE_SIZE


class PrologManager:

    def __init__(self):

        self.prolog = Prolog()

        # =========================
        # Cargar lógica Prolog
        # =========================
        self.prolog.consult("prolog/pathfinding.pl")

    # =========================
    # Limpiar hechos anteriores
    # =========================
    def clear_facts(self):

        list(
            self.prolog.query(
                "retractall(connected(_, _))"
            )
        )

    # =========================
    # Generar grafo desde mapa
    # =========================
    def generate_graph(self, level_loader):

        self.clear_facts()

        walls = set()

        # =========================
        # Registrar muros
        # =========================
        for wall in level_loader.walls:

            grid_x = wall.rect.x // TILE_SIZE
            grid_y = wall.rect.y // TILE_SIZE

            walls.add((grid_x, grid_y))

        rows = len(level_loader.map_data)
        cols = len(level_loader.map_data[0])

        # Debug útil (opcional)
        print("ROWS:", rows, "COLS:", cols)
        print("WALLS:", len(walls))

        # =========================
        # Crear conexiones del grafo
        # =========================
        for y in range(rows):

            for x in range(cols):

                # Saltar muro
                if (x, y) in walls:
                    continue

                # ⚠ IMPORTANTE: formato correcto de nodo
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

                            # FORMATO CORRECTO (x_y)
                            neighbor = f"{nx}_{ny}"

                            # Insertar hecho en Prolog
                            self.prolog.assertz(f"connected('{current}','{neighbor}')")
                            

    # =========================
    # Buscar ruta con Prolog (DFS)
    # =========================
    def find_path(self, start_x, start_y, goal_x, goal_y):

        start = f"'{start_x}_{start_y}'"
        goal = f"'{goal_x}_{goal_y}'"

        query = f"path({start},{goal},Path)"

        # Solo una solución para evitar backtracking infinito
        result = list(
            self.prolog.query(query, maxresult=1)
        )

        if result:
            return result[0]["Path"]

        return []