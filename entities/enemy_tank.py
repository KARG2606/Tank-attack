import math
import random

from entities.entity import Entity
from entities.bullet import Bullet
from ai.enemy_state import EnemyState


# Cooldown de disparo por tipo (frames a 60 FPS).
SHOOT_COOLDOWN_BY_TYPE = {
    1: 60,
    2: 90,
    3: 120,
}

# Velocidad por tipo (px / frame). Tipo 1 ágil, tipo 3 contundente.
SPEED_BY_TYPE = {
    1: 3,
    2: 2,
    3: 2,
}


class EnemyTank(Entity):

    def __init__(self, x, y, size, enemy_type=1):

        self.enemy_type = enemy_type

        # =========================
        # Rol por tipo
        # =========================
        if enemy_type == 1:
            self.role = "ASSAULT"
            color = (200, 0, 0)
        elif enemy_type == 2:
            self.role = "DEFENDER"
            color = (0, 120, 255)
        else:
            self.role = "FLANKER"
            color = (0, 200, 100)

        super().__init__(x, y, size, color)

        # =========================
        # FSM y target
        # =========================
        self.state = EnemyState.PATROL
        self.target_objective = None

        # =========================
        # Ruta y path-following
        # =========================
        self.current_path = []
        self.path_index = 0

        self.repath_interval = 60
        self.repath_timer = random.randint(0, 60)

        self.ai_interval = 30
        self.ai_timer = 0

        self.target_lock_timer = 0
        self.target_lock_duration = 30

        # =========================
        # Movimiento y combate
        # =========================
        self.speed = SPEED_BY_TYPE.get(enemy_type, 2)

        self.target_x = None
        self.target_y = None
        self.patrol_target = None

        self.attack_range = 140
        self.too_close_range = 70
        self.detection_range = 150
        self.defense_radius = 220
        self.defense_patrol_radius = 80
        self.alerted = False

        self._shoot_cooldown = 0
        self._shoot_cooldown_max = SHOOT_COOLDOWN_BY_TYPE.get(
            enemy_type, 90
        )

        # =========================
        # Spawn y restricciones
        # =========================
        self.spawn_x = x
        self.spawn_y = y
        self.max_chase_distance = 250

        # Dirección visible (para el disparo).
        self.direction = "DOWN"

        # Última acción que devolvió Prolog (la setea GameManager).
        self.prolog_action = "patrullar"

    # =========================
    # Helpers de IA
    # =========================
    def distance_to_player(self, player):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        return math.sqrt(dx * dx + dy * dy)

    def generate_patrol_point(self):
        patrol_distance = 120
        offset_x = random.randint(-patrol_distance, patrol_distance)
        offset_y = random.randint(-patrol_distance, patrol_distance)
        self.patrol_target = (
            self.rect.centerx + offset_x,
            self.rect.centery + offset_y,
        )

    # =========================
    # Disparo
    # =========================
    def _direction_to(self, player):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        if abs(dx) > abs(dy):
            return "RIGHT" if dx > 0 else "LEFT"
        return "DOWN" if dy > 0 else "UP"

    def shoot(self, player):
        if self._shoot_cooldown > 0:
            return None

        self._shoot_cooldown = self._shoot_cooldown_max
        self.direction = self._direction_to(player)

        bullet_size = self.size // 4
        half = self.size // 2

        # La bala sale del cañón (borde del tanque en la dirección
        # de disparo), no del centro del chasis.
        if self.direction == "UP":
            bx = self.rect.centerx - bullet_size // 2
            by = self.rect.centery - half - bullet_size
        elif self.direction == "DOWN":
            bx = self.rect.centerx - bullet_size // 2
            by = self.rect.centery + half
        elif self.direction == "LEFT":
            bx = self.rect.centerx - half - bullet_size
            by = self.rect.centery - bullet_size // 2
        else:  # RIGHT
            bx = self.rect.centerx + half
            by = self.rect.centery - bullet_size // 2

        return Bullet(
            bx, by, bullet_size, self.direction, "ENEMY"
        )

    # =========================
    # Seguir ruta calculada
    # =========================
    def follow_path(self, tile_size):
        if not self.current_path:
            return

        if self.path_index >= len(self.current_path):
            self.current_path = []
            self.path_index = 0
            self.patrol_target = None
            self.target_lock_timer = 0
            return

        node = self.current_path[self.path_index]
        nx, ny = node

        target_x = (nx * tile_size) + (tile_size // 2)
        target_y = (ny * tile_size) + (tile_size // 2)

        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery

        if abs(dx) < 5 and abs(dy) < 5:
            self.path_index += 1
            return

        if abs(dx) > abs(dy):
            if dx > 0:
                self.rect.x += self.speed
                self.direction = "RIGHT"
            else:
                self.rect.x -= self.speed
                self.direction = "LEFT"
        else:
            if dy > 0:
                self.rect.y += self.speed
                self.direction = "DOWN"
            else:
                self.rect.y -= self.speed
                self.direction = "UP"

        self.x = self.rect.x
        self.y = self.rect.y

    # =========================
    # Update principal — devuelve Bullet o None
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
        map_height,
    ):

        # =========================
        # Invalida target si fue destruido
        # =========================
        if self.target_objective not in objectives:
            self.target_objective = None

        # =========================
        # Timers
        # =========================
        self.repath_timer -= 1
        self.ai_timer -= 1
        self.target_lock_timer -= 1
        self._shoot_cooldown -= 1
        distance = self.distance_to_player(player)

        spawn_distance = math.sqrt(
            (self.rect.centerx - self.spawn_x) ** 2
            + (self.rect.centery - self.spawn_y) ** 2
        )

        # =========================
        # Decisión (cada self.ai_interval frames)
        # Prioridad: lo que dijo Prolog. Si no aplica, lógica del rol.
        # =========================
        if self.ai_timer <= 0 and self.target_lock_timer <= 0:

            tx, ty = self._aplicar_accion_prolog(
                player, objectives, enemies,
                tactical_manager, tile_size, distance,
            )

            if tx is None:
                # Fallback: lógica específica del rol.
                if self.role == "DEFENDER":
                    tx, ty = self._decide_defender(
                        player, objectives, distance
                    )
                elif self.role == "ASSAULT":
                    tx, ty = self._decide_assault(
                        player, distance, spawn_distance
                    )
                else:
                    tx, ty = self._decide_flanker(
                        player, distance, spawn_distance,
                        tactical_manager, enemies, tile_size,
                    )

            new_goal = (tx // tile_size, ty // tile_size)
            old_goal = (
                self.target_x // tile_size,
                self.target_y // tile_size,
            ) if (
                self.target_x is not None and self.target_y is not None
            ) else None

            if new_goal != old_goal:
                self.current_path = []
                self.path_index = 0

            self.target_x = tx
            self.target_y = ty
            self.target_lock_timer = self.target_lock_duration
            self.ai_timer = self.ai_interval

        if self.target_x is None or self.target_y is None:
            return None

        # =========================
        # Repath cuando hace falta
        # =========================
        if self.repath_timer <= 0 or not self.current_path:
            start = (
                self.rect.centerx // tile_size,
                self.rect.centery // tile_size,
            )
            goal = (
                int(self.target_x) // tile_size,
                int(self.target_y) // tile_size,
            )

            wall_set = {
                (w.rect.x // tile_size, w.rect.y // tile_size)
                for w in walls
            }

            path = pathfinding.find_path(
                start, goal, wall_set, map_width, map_height
            )

            if path:
                self.current_path = path
                self.path_index = 0

            self.repath_timer = self.repath_interval

        # =========================
        # Disparo: solo en ATTACK/HOLD y dentro de rango
        # =========================
        bullet = None
        if (
            self.state in (EnemyState.ATTACK, EnemyState.HOLD)
            and distance <= self.attack_range
        ):
            bullet = self.shoot(player)

        # =========================
        # Movimiento
        # =========================
        self.follow_path(tile_size)

        return bullet

    # =========================
    # Decisión guiada por Prolog
    # =========================
    def _aplicar_accion_prolog(
        self, player, objectives, enemies,
        tactical_manager, tile_size, distance,
    ):
        """
        Traduce la acción que devolvió Prolog en un (target_x, target_y)
        y deja seteado self.state. Devuelve (None, None) si no aplica y
        toca caer al fallback del rol.
        """
        accion = self.prolog_action

        if accion == "atacar":
            self.state = EnemyState.ATTACK
            return player.rect.centerx, player.rect.centery

        if accion == "retroceder":
            self.state = EnemyState.RETREAT
            dx = self.rect.centerx - player.rect.centerx
            dy = self.rect.centery - player.rect.centery
            return (
                self.rect.centerx + dx,
                self.rect.centery + dy,
            )

        if accion == "emboscar":
            self.state = EnemyState.AMBUSH
            tactical = tactical_manager.get_tactical_target(
                self, enemies, tile_size
            )
            if tactical:
                return tactical
            offsets = [(-120, 0), (120, 0), (0, -120), (0, 120)]
            ox, oy = random.choice(offsets)
            return (
                player.rect.centerx + ox,
                player.rect.centery + oy,
            )

        if accion == "defender" and self.target_objective in objectives:
            obj = self.target_objective
            self.state = EnemyState.DEFEND
            return obj.rect.centerx, obj.rect.centery

        # 'patrullar' o desconocido → que decida el rol.
        return None, None

    # =========================
    # Decisiones por rol (fallback cuando Prolog dice patrullar)
    # =========================
    def _decide_defender(self, player, objectives, distance):
        if self.target_objective in objectives:
            obj = self.target_objective
            player_to_obj = math.sqrt(
                (player.rect.centerx - obj.rect.centerx) ** 2
                + (player.rect.centery - obj.rect.centery) ** 2
            )
            dist_to_obj = math.sqrt(
                (obj.rect.centerx - self.rect.centerx) ** 2
                + (obj.rect.centery - self.rect.centery) ** 2
            )

            if player_to_obj < self.defense_radius:
                self.patrol_target = None
                self.alerted = True

                if distance > self.attack_range:
                    self.state = EnemyState.ATTACK
                    return (player.rect.centerx, player.rect.centery)

                if distance < self.too_close_range:
                    self.state = EnemyState.RETREAT
                    dx = self.rect.centerx - player.rect.centerx
                    dy = self.rect.centery - player.rect.centery
                    return (
                        self.rect.centerx + dx,
                        self.rect.centery + dy,
                    )

                self.state = EnemyState.HOLD
                return (self.rect.centerx, self.rect.centery)

            self.alerted = False
            if dist_to_obj > 80:
                self.state = EnemyState.DEFEND
                return (obj.rect.centerx, obj.rect.centery)

            self.state = EnemyState.PATROL
            if self.patrol_target is None:
                self.generate_patrol_point()
            return self.patrol_target

        # objetivo destruido → atacar
        self.state = EnemyState.ATTACK
        return (player.rect.centerx, player.rect.centery)

    def _decide_assault(self, player, distance, spawn_distance):
        if distance < self.detection_range:
            self.alerted = True
        elif distance > self.detection_range * 1.5:
            self.alerted = False

        if self.alerted:
            if spawn_distance > self.max_chase_distance:
                self.alerted = False

            if distance > self.attack_range:
                self.state = EnemyState.ATTACK
                return (player.rect.centerx, player.rect.centery)

            if distance < self.too_close_range:
                self.state = EnemyState.RETREAT
                dx = self.rect.centerx - player.rect.centerx
                dy = self.rect.centery - player.rect.centery
                return (
                    self.rect.centerx + dx,
                    self.rect.centery + dy,
                )

            self.state = EnemyState.HOLD
            return (self.rect.centerx, self.rect.centery)

        # patrulla / defensa pasiva
        obj = self.target_objective
        if obj is None:
            self.state = EnemyState.PATROL
            if self.patrol_target is None:
                self.generate_patrol_point()
            return self.patrol_target

        self.state = EnemyState.DEFEND
        if self.patrol_target is None or not self.current_path:
            offset_x = random.randint(
                -self.defense_patrol_radius,
                self.defense_patrol_radius,
            )
            offset_y = random.randint(
                -self.defense_patrol_radius,
                self.defense_patrol_radius,
            )
            self.patrol_target = (
                obj.rect.centerx + offset_x,
                obj.rect.centery + offset_y,
            )
        return self.patrol_target

    def _decide_flanker(
        self, player, distance, spawn_distance,
        tactical_manager, enemies, tile_size,
    ):
        if distance < self.detection_range * 1.5:
            self.alerted = True
        elif distance > self.detection_range * 2:
            self.alerted = False

        if self.alerted:
            if spawn_distance > self.max_chase_distance:
                self.alerted = False

            self.state = EnemyState.AMBUSH

            tactical = tactical_manager.get_tactical_target(
                self, enemies, tile_size
            )
            if tactical:
                return tactical

            offsets = [(-120, 0), (120, 0), (0, -120), (0, 120)]
            offset = random.choice(offsets)
            return (
                player.rect.centerx + offset[0],
                player.rect.centery + offset[1],
            )

        self.state = EnemyState.PATROL
        if self.patrol_target is None:
            self.generate_patrol_point()
        return self.patrol_target
