import math
import random

from entities.entity import Entity
from ai.enemy_state import EnemyState


class EnemyTank(Entity):

    def __init__(self, x, y, size, enemy_type=1):

        self.enemy_type = enemy_type

        # =========================
        # ROLE BASE
        # =========================

        if enemy_type == 1:
            self.role = "ASSAULT"

        elif enemy_type == 2:
            self.role = "DEFENDER"

        else:
            self.role = "FLANKER"

        # =========================
        # COLOR
        # =========================

        if enemy_type == 1:
            color = (200, 0, 0)

        elif enemy_type == 2:
            color = (0, 120, 255)

        else:
            color = (0, 200, 100)

        super().__init__(x, y, size, color)

        # =========================
        # FSM
        # =========================

        self.state = EnemyState.PATROL

        # =========================
        # OBJECTIVES
        # =========================

        self.target_objective = None

        # =========================
        # PATH
        # =========================

        self.current_path = []
        self.path_index = 0

        # =========================
        # TIMERS
        # =========================

        self.repath_interval = 60
        self.repath_timer = random.randint(0, 60)

        self.ai_interval = 30
        self.ai_timer = 0

        # =========================
        # TARGET LOCK
        # =========================

        self.target_lock_timer = 0
        self.target_lock_duration = 30

        # =========================
        # MOVEMENT
        # =========================

        self.speed = 3

        # =========================
        # TARGETS
        # =========================

        self.target_x = None
        self.target_y = None

        # =========================
        # PATROL
        # =========================

        self.patrol_target = None

        # =========================
        # COMBAT
        # =========================

        self.attack_range = 140
        self.too_close_range = 70
        self.shoot_cooldown = 0
        self.detection_range = 150
        self.defense_radius = 220
        self.defense_patrol_radius = 80
        self.alerted = False

        self.spawn_x = x
        self.spawn_y = y

        self.max_chase_distance = 250

    # =========================
    # DISTANCIA AL JUGADOR
    # =========================

    def distance_to_player(self, player):

        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery

        return math.sqrt(dx * dx + dy * dy)
    
    # =========================
    # GENERAR PATRULLA
    # =========================

    def generate_patrol_point(self):

        patrol_distance = 120

        offset_x = random.randint(
            -patrol_distance,
            patrol_distance
        )

        offset_y = random.randint(
            -patrol_distance,
            patrol_distance
        )

        self.patrol_target = (
            self.rect.centerx + offset_x,
            self.rect.centery + offset_y
        )

    # =========================
    # FOLLOW PATH
    # =========================

    def follow_path(self, tile_size):

        # =========================
        # NO HAY PATH
        # =========================

        if not self.current_path:
            return

        # =========================
        # TERMINÓ RUTA
        # =========================

        if self.path_index >= len(self.current_path):

            self.current_path = []
            self.path_index = 0

            self.patrol_target = None

            # permitir nueva decisión
            self.target_lock_timer = 0

            return

        # =========================
        # NODO ACTUAL
        # =========================

        node = self.current_path[self.path_index]

        # BFS devuelve (x, y)
        x, y = node

        # =========================
        # CENTRO DEL TILE
        # =========================

        target_x = (x * tile_size) + (tile_size // 2)
        target_y = (y * tile_size) + (tile_size // 2)

        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery

        # =========================
        # LLEGÓ AL NODO
        # =========================

        if abs(dx) < 5 and abs(dy) < 5:

            self.path_index += 1

            return

        # =========================
        # MOVIMIENTO CARDINAL
        # =========================

        if abs(dx) > abs(dy):

            if dx > 0:
                self.rect.x += self.speed
            else:
                self.rect.x -= self.speed

        else:

            if dy > 0:
                self.rect.y += self.speed
            else:
                self.rect.y -= self.speed

        self.x = self.rect.x
        self.y = self.rect.y
    # =========================
    # UPDATE
    # =========================

    def update(
        self,
        player,
        objectives,
        walls,
        enemies,
        ai_controller,
        tactical_manager,
        pathfinding,
        tile_size,
        map_width,
        map_height
    ):

        # =========================
        # VALIDAR OBJETIVO
        # =========================

        if self.target_objective not in objectives:
            self.target_objective = None

        # =========================
        # TIMERS
        # =========================

        self.repath_timer -= 1
        self.ai_timer -= 1
        self.target_lock_timer -= 1
        self.shoot_cooldown -= 1
        distance = self.distance_to_player(player)

        # =========================
        # DISTANCIA A SPAWN
        # =========================

        spawn_distance = math.sqrt(
            (self.rect.centerx - self.spawn_x) ** 2 +
            (self.rect.centery - self.spawn_y) ** 2
        )

        # =========================
        # IA
        # =========================

        if (self.ai_timer <= 0
            and self.target_lock_timer <= 0
        ):
            print("REPATH TRIGGERED")
            print("AI THINKING")

            # =========================
            # DEFENDER
            # =========================

            if self.role == "DEFENDER":

                # =========================
                # OBJETIVO EXISTE
                # =========================

                if self.target_objective in objectives:

                    obj = self.target_objective

                    # distancia al objetivo
                    dist_to_obj = math.sqrt(
                        (obj.rect.centerx - self.rect.centerx) ** 2 +
                        (obj.rect.centery - self.rect.centery) ** 2
                    )

                    # distancia jugador ↔ objetivo
                    player_to_obj = math.sqrt(
                        (player.rect.centerx - obj.rect.centerx) ** 2 +
                        (player.rect.centery - obj.rect.centery) ** 2
                    )

                    # =========================
                    # JUGADOR CERCA DEL OBJETIVO
                    # =========================

                    if player_to_obj < self.defense_radius:
                        self.patrol_target = None

                        self.alerted = True

                        # jugador demasiado cerca → atacar

                        if distance > self.attack_range:

                            self.state = EnemyState.ATTACK

                            tx = player.rect.centerx
                            ty = player.rect.centery

                        elif distance < self.too_close_range:

                            self.state = EnemyState.RETREAT

                            dx = self.rect.centerx - player.rect.centerx
                            dy = self.rect.centery - player.rect.centery

                            tx = self.rect.centerx + dx
                            ty = self.rect.centery + dy

                        else:

                            self.state = EnemyState.HOLD

                            tx = self.rect.centerx
                            ty = self.rect.centery

                    # =========================
                    # JUGADOR LEJOS
                    # =========================

                    else:

                        self.alerted = False
                        # regresar a defender

                        if dist_to_obj > 80:

                            self.state = EnemyState.DEFEND

                            tx = obj.rect.centerx
                            ty = obj.rect.centery

                        else:

                            self.state = EnemyState.PATROL

                            if self.patrol_target is None:
                                self.generate_patrol_point()

                            tx, ty = self.patrol_target

                # =========================
                # OBJETIVO DESTRUIDO
                # =========================

                else:

                    self.state = EnemyState.ATTACK

                    tx = player.rect.centerx
                    ty = player.rect.centery

            # =========================
            # ASSAULT
            # =========================

            elif self.role == "ASSAULT":

                # =========================
                # DETECTÓ JUGADOR
                # =========================

                if distance < self.detection_range:
                    self.alerted = True

                # =========================
                # PERDIÓ JUGADOR
                # =========================

                elif distance > self.detection_range * 1.5:
                    self.alerted = False

                # =========================
                # ALERTA ACTIVA
                # =========================

                if self.alerted:

                    # =========================
                    # MUY LEJOS DE SU ZONA
                    # =========================

                    if spawn_distance > self.max_chase_distance:

                        self.alerted = False

                    if distance > self.attack_range:

                        self.state = EnemyState.ATTACK

                        tx = player.rect.centerx
                        ty = player.rect.centery

                    elif distance < self.too_close_range:

                        self.state = EnemyState.RETREAT

                        dx = self.rect.centerx - player.rect.centerx
                        dy = self.rect.centery - player.rect.centery

                        tx = self.rect.centerx + dx
                        ty = self.rect.centery + dy

                    else:

                        self.state = EnemyState.HOLD

                        tx = self.rect.centerx
                        ty = self.rect.centery

                # =========================
                # PATRULLA
                # =========================

                else:
                    obj = self.target_objective

                    if obj is None:

                        self.state = EnemyState.PATROL

                        if self.patrol_target is None:
                            self.generate_patrol_point()

                        tx, ty = self.patrol_target

                    else:
                        self.state = EnemyState.DEFEND

                        # =========================
                        # GENERAR PATRULLA DEFENSIVA
                        # =========================

                        if (
                            self.patrol_target is None
                            or self.current_path == []
                        ):

                            offset_x = random.randint(
                                -self.defense_patrol_radius,
                                self.defense_patrol_radius
                            )

                            offset_y = random.randint(
                                -self.defense_patrol_radius,
                                self.defense_patrol_radius
                            )

                            self.patrol_target = (
                                obj.rect.centerx + offset_x,
                                obj.rect.centery + offset_y
                            )

                        tx, ty = self.patrol_target
            # =========================
            # FLANKER
            # =========================

            elif self.role == "FLANKER":

                # =========================
                # DETECCIÓN
                # =========================

                if distance < self.detection_range * 1.5:
                    self.alerted = True

                # =========================
                # PERDIÓ JUGADOR
                # =========================

                elif distance > self.detection_range * 2:
                    self.alerted = False

                # =========================
                # ALERTA ACTIVA
                # =========================

                if self.alerted:

                    # =========================
                    # MUY LEJOS DE SU ZONA
                    # =========================

                    if spawn_distance > self.max_chase_distance:

                        self.alerted = False

                    self.state = EnemyState.AMBUSH

                    offsets = [
                        (-120, 0),
                        (120, 0),
                        (0, -120),
                        (0, 120)
                    ]

                    offset = random.choice(offsets)

                    tx = player.rect.centerx + offset[0]
                    ty = player.rect.centery + offset[1]

                # =========================
                # PATRULLA
                # =========================

                else:

                    self.state = EnemyState.PATROL

                    if self.patrol_target is None:
                        self.generate_patrol_point()

                    tx, ty = self.patrol_target
            # ---------------------------------
            # ATTACK
            # ---------------------------------

            elif self.state == EnemyState.ATTACK:

                # =========================
                # Última posición conocida
                # =========================

                if tactical_manager.last_known_player_position:

                    lx, ly = (
                        tactical_manager.last_known_player_position
                    )

                    # Variación táctica
                    offset_x = random.randint(-80, 80)
                    offset_y = random.randint(-80, 80)

                    tx = lx + offset_x
                    ty = ly + offset_y

                else:

                    # Patrulla libre
                    if self.patrol_target is None:

                        self.patrol_target = (
                            tactical_manager.generate_patrol_point(
                                self
                            )
                        )

                    tx, ty = self.patrol_target
            # ---------------------------------
            # SEARCH
            # ---------------------------------

            elif self.state == EnemyState.SEARCH:

                if tactical_manager.last_known_player_position:

                    tx, ty = (
                        tactical_manager.last_known_player_position
                    )

                else:

                    if self.patrol_target is None:

                        self.patrol_target = (
                            tactical_manager.generate_patrol_point(
                                self
                            )
                        )

                    tx, ty = self.patrol_target

            # ---------------------------------
            # AMBUSH
            # ---------------------------------

            elif self.state == EnemyState.AMBUSH:

                tactical_target = (
                    tactical_manager.get_tactical_target(
                        self,
                        enemies,
                        tile_size
                    )
                )

                if tactical_target:

                    tx, ty = tactical_target

                else:

                    tx = player.rect.centerx
                    ty = player.rect.centery

            # ---------------------------------
            # FALLBACK
            # ---------------------------------

            else:

                tx = player.rect.centerx
                ty = player.rect.centery

            # =========================
            # GUARDAR TARGET
            # =========================

            # =========================
            # TARGET CAMBIÓ
            # =========================

            new_goal = (
                tx // tile_size,
                ty // tile_size
            )

            old_goal = (
                self.target_x // tile_size,
                self.target_y // tile_size
            ) if self.target_x and self.target_y else None

            if new_goal != old_goal:

                self.current_path = []
                self.path_index = 0
            self.target_x = tx
            self.target_y = ty

            self.target_lock_timer = (
                self.target_lock_duration
            )

            self.ai_timer = self.ai_interval

        # =========================
        # VALIDACIÓN
        # =========================

        if self.target_x is None or self.target_y is None:
            return

        # =========================
        # REPATH CONTROLADO
        # =========================

        if self.repath_timer <= 0 or len(self.current_path) == 0:

            start_x = self.rect.centerx // tile_size
            start_y = self.rect.centery // tile_size

            goal_x = self.target_x // tile_size
            goal_y = self.target_y // tile_size

            # =========================
            # WALL SET
            # =========================

            wall_set = set()

            for wall in walls:

                wx = wall.rect.x // tile_size
                wy = wall.rect.y // tile_size

                wall_set.add((wx, wy))

            # =========================
            # PATHFINDING
            # =========================

            path = pathfinding.find_path(
                (start_x, start_y),
                (goal_x, goal_y),
                wall_set,
                map_width,
                map_height
            )

            if path:

                self.current_path = path
                self.path_index = 0

            self.repath_timer = self.repath_interval
        
        # =========================
        # DISPARO IA
        # =========================

        if (
            self.state in [
                EnemyState.ATTACK,
                EnemyState.HOLD
            ]
            and distance <= self.attack_range
        ):

            if self.shoot_cooldown <= 0:

                print("ENEMY SHOOT")

                self.shoot_cooldown = 90

        # =========================
        # MOVIMIENTO
        # =========================

        self.follow_path(tile_size)

        print(
            "STATE:", self.state,
            "| PATH:", len(self.current_path),
            "| INDEX:", self.path_index,
            "| AI:", self.ai_timer,
            "| LOCK:", self.target_lock_timer,
            "| REPATH:", self.repath_timer
        )