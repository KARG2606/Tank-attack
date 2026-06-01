from pyswip import Prolog
from game.constants import TILE_SIZE


class PrologManager:

    def __init__(self):

        self.prolog = Prolog()
        self.prolog.consult("prolog/pathfinding.pl")
        self.prolog.consult("prolog/decision.pl")

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

    # =========================
    # SINCRONIZAR ESTADO DEL JUEGO A PROLOG
    # =========================

    def sync_state(self, level_loader):
        """
        Sincroniza el estado actual del nivel a Prolog antes de
        consultar decisiones. Hace retractall + assertz para que
        los predicados decidir_accion/cerca_de_jugador/etc. usen
        la fotografía más reciente del juego.
        """
        # Limpia hechos dinámicos.
        list(self.prolog.query("retractall(tanque(_,_,_,_))"))
        list(self.prolog.query("retractall(jugador(_,_))"))
        list(self.prolog.query("retractall(objetivo(_,_,_))"))
        list(self.prolog.query("retractall(jugador_detectado(_,_))"))

        # Jugador
        if level_loader.player:
            jx = level_loader.player.rect.centerx // TILE_SIZE
            jy = level_loader.player.rect.centery // TILE_SIZE
            self.prolog.assertz(f"jugador({jx},{jy})")

        # Tanques enemigos: tanque(Id, X, Y, Tipo)
        for idx, enemy in enumerate(level_loader.enemies):
            ex = enemy.rect.centerx // TILE_SIZE
            ey = enemy.rect.centery // TILE_SIZE
            self.prolog.assertz(
                f"tanque(t{idx},{ex},{ey},{enemy.enemy_type})"
            )

        # Objetivos: objetivo(Id, X, Y)
        for idx, obj in enumerate(level_loader.objectives):
            ox = obj.rect.centerx // TILE_SIZE
            oy = obj.rect.centery // TILE_SIZE
            self.prolog.assertz(f"objetivo(o{idx},{ox},{oy})")

    def consultar_accion(self, enemy_id):
        """
        Pregunta a Prolog qué acción tomar para un tanque dado.
        Devuelve una de: 'atacar', 'defender', 'emboscar',
        'retroceder', 'patrullar'. Si algo falla, 'patrullar'.
        """
        try:
            query = f"decidir_accion(t{enemy_id}, Accion)"
            result = list(self.prolog.query(query, maxresult=1))
            if result:
                accion = result[0]["Accion"]
                if isinstance(accion, bytes):
                    accion = accion.decode("utf-8")
                return str(accion)
        except Exception as e:
            print("PROLOG DECISION ERROR:", e)
        return "patrullar"

    def asentar_avistamiento(self, enemy_id):
        """
        Hace que el tanque enemigo `enemy_id` (que ve al jugador)
        publique el hecho para que otros tanques lo consulten —
        base de la coordinación táctica de la Fase 7.
        """
        try:
            list(self.prolog.query(f"avistar_jugador(t{enemy_id})"))
        except Exception as e:
            print("PROLOG SIGHT ERROR:", e)