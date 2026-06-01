from collections import deque


class Pathfinding:
    """
    BFS sobre grilla de tiles.

    Coordenadas: (col, row) en espacio de tiles (no píxeles).
    El llamador convierte píxeles → tile dividiendo entre TILE_SIZE.
    """

    def __init__(self):
        # Cache: (start_tile, goal_tile) → path de tiles
        # Se limpia externamente al recargar el nivel.
        self._cache: dict = {}

    # =========================================================================
    #  CONVERSIÓN PÍXELES ↔ TILE
    # =========================================================================

    @staticmethod
    def pixel_to_tile(px, py, tile_size):
        return (int(px // tile_size), int(py // tile_size))

    @staticmethod
    def tile_to_pixel_center(col, row, tile_size):
        return (
            col * tile_size + tile_size // 2,
            row * tile_size + tile_size // 2
        )

    # =========================================================================
    #  CONSTRUCCIÓN DEL SET DE MUROS (llamar una vez al cargar nivel)
    # =========================================================================

    @staticmethod
    def build_wall_set(walls, tile_size):
        """
        Convierte la lista de Wall a un set de (col, row) para O(1) lookup.
        Llama esto una vez al cargar el nivel y pasa el resultado a find_path.
        """
        return {
            (w.rect.x // tile_size, w.rect.y // tile_size)
            for w in walls
        }

    # =========================================================================
    #  BFS PRINCIPAL
    # =========================================================================

    def find_path(
        self,
        start_px, start_py,
        goal_px,  goal_py,
        wall_set,
        map_width, map_height,
        tile_size
    ):
        """
        Encuentra el camino más corto en tiles de (start_px,start_py)
        a (goal_px,goal_py) evitando wall_set.

        Retorna lista de coordenadas en PÍXELES (centros de tile),
        sin incluir la posición inicial, o [] si no hay camino.
        """
        start = self.pixel_to_tile(start_px, start_py, tile_size)
        goal  = self.pixel_to_tile(goal_px,  goal_py,  tile_size)

        if start == goal:
            return []

        # Cache hit
        cache_key = (start, goal)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # BFS
        queue   = deque()
        queue.append((start, [start]))
        visited = {start}

        result = []
        found  = False

        while queue:
            current, path = queue.popleft()

            if current == goal:
                result = path[1:]   # Excluir inicio
                found  = True
                break

            cx, cy = current
            for nx, ny in ((cx+1,cy),(cx-1,cy),(cx,cy+1),(cx,cy-1)):
                if not (0 <= nx < map_width and 0 <= ny < map_height):
                    continue
                if (nx, ny) in wall_set:
                    continue
                if (nx, ny) in visited:
                    continue
                visited.add((nx, ny))
                queue.append(((nx, ny), path + [(nx, ny)]))

        if not found:
            self._cache[cache_key] = []
            return []

        # Convertir tiles → centros de pixel
        pixel_path = [
            self.tile_to_pixel_center(col, row, tile_size)
            for col, row in result
        ]

        self._cache[cache_key] = pixel_path
        return pixel_path

    def clear_cache(self):
        self._cache.clear()
