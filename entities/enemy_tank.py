import math
import random

from entities.entity import Entity
from game.collision_manager import CollisionManager
from entities.bullet import Bullet


# =============================================================================
#  CONSTANTES DE COMPORTAMIENTO
# =============================================================================

BASE_LEASH_RADIUS     = 300   # Px máximos desde la base antes de regresar
PATROL_RADIUS_MIN     = 80    # Radio mínimo de patrulla
PATROL_RADIUS_MAX     = 160   # Radio máximo de patrulla
WAYPOINT_TOLERANCE    = 10    # Px para considerar que llegó a un waypoint
DETECT_RADIUS         = 220   # Px de detección del jugador
ATTACK_RADIUS         = 130   # Px para disparar
FLANK_ORBIT_RADIUS    = 110   # Radio de órbita tipo 3 (flanqueo fino)
SHOOT_COOLDOWN_FRAMES = 60    # Frames entre disparos

# Frames entre recálculos de path BFS.
# Tipo 3 recalcula más seguido porque persigue al jugador en movimiento.
PATH_REFRESH_TYPE3    = 30    # ~0.5 s a 60 fps
PATH_REFRESH_DEFAULT  = 60    # ~1 s a 60 fps

# Píxeles que debe avanzar el tanque antes de cambiar de eje (anti-diagonal)
DIR_LOCK_DISTANCE     = 20

# Velocidades por tipo
SPEED_BY_TYPE  = {1: 1.2, 2: 1.6, 3: 2.0}

# Colores por tipo
COLOR_BY_TYPE  = {1: (180, 60, 60), 2: (200, 120, 0), 3: (140, 0, 200)}

# Ángulos de emboscada para cada posible índice de tanque tipo 3 (en radianes).
# Si hay 3 tanques tipo 3, se reparten 120° entre sí alrededor del jugador.
AMBUSH_ANGLES = [0.0, 2.094, 4.189]   # 0°, 120°, 240°


# =============================================================================
#  ESTADOS DE LA IA
# =============================================================================

STATE_PATROL  = "PATROL"
STATE_CHASE   = "CHASE"
STATE_ATTACK  = "ATTACK"
STATE_RETURN  = "RETURN"
STATE_DEFEND  = "DEFEND"
STATE_FLANK   = "FLANK"
STATE_ASSAULT = "ASSAULT"


class EnemyTank(Entity):

    # Contador de clase para asignar índices de emboscada únicos a tipo 3
    _type3_counter = 0

    def __init__(self, x, y, size, tank_type=1):
        color = COLOR_BY_TYPE.get(tank_type, (180, 60, 60))
        super().__init__(x, y, size, color)

        self.tank_type = tank_type
        self.speed     = SPEED_BY_TYPE.get(tank_type, 1.2)
        self.direction = "DOWN"
        self.state     = STATE_PATROL

        # --- Base asignada ---
        self.home_base = None
        self.base_lost = False

        # --- Patrulla ---
        self.patrol_points = []
        self.patrol_index  = 0
        self._generate_patrol_points()

        # --- Flanqueo orbital (tipo 3, fallback sin path) ---
        self.flank_dir = random.choice([-1, 1])
        self.flank_angle = random.uniform(0, 2 * math.pi)

        # --- Índice de emboscada (tipo 3): ángulo único por tanque ---
        if tank_type == 3:
            self.ambush_index = EnemyTank._type3_counter % len(AMBUSH_ANGLES)
            EnemyTank._type3_counter += 1
        else:
            self.ambush_index = 0

        # --- Disparo ---
        self.shoot_cooldown = 0

        # --- Pathfinding ---
        # path: lista de (px, py) centros de tile a seguir
        self._path          = []
        self._path_index    = 0
        self._path_timer    = 0   # Frames desde el último recálculo
        # Último destino para el que se calculó el path (en píxeles)
        self._path_goal     = None
        # Wall set y parámetros de mapa (inyectados por GameManager)
        self.wall_set       = None
        self.map_width      = 0
        self.map_height     = 0
        self.tile_size      = 32

        # --- Bloqueo de eje (anti-diagonal) ---
        self._locked_axis   = None   # "H" | "V"
        self._dist_in_axis  = 0.0

    # =========================================================================
    #  CONFIGURACIÓN DE PATHFINDING (llamar desde GameManager tras cargar nivel)
    # =========================================================================

    def setup_pathfinding(self, wall_set, map_width, map_height, tile_size):
        self.wall_set   = wall_set
        self.map_width  = map_width
        self.map_height = map_height
        self.tile_size  = tile_size

    # =========================================================================
    #  PATRULLA
    # =========================================================================

    def _generate_patrol_points(self, num_points=6):
        self.patrol_points = []
        if self.home_base is None:
            cx, cy = self.rect.centerx, self.rect.centery
        else:
            cx, cy = self.home_base.rect.centerx, self.home_base.rect.centery

        radius = random.randint(PATROL_RADIUS_MIN, PATROL_RADIUS_MAX)
        for i in range(num_points):
            angle = (2 * math.pi / num_points) * i + random.uniform(-0.3, 0.3)
            self.patrol_points.append((
                cx + radius * math.cos(angle),
                cy + radius * math.sin(angle)
            ))

    def assign_base(self, base):
        self.home_base = base
        self._generate_patrol_points()

    @property
    def patrol_target(self):
        if not self.patrol_points:
            return None
        return self.patrol_points[self.patrol_index % len(self.patrol_points)]

    def _advance_patrol(self):
        if self.patrol_points:
            self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)

    # =========================================================================
    #  DISTANCIAS
    # =========================================================================

    def distance_to_player(self, player):
        return math.hypot(
            player.rect.centerx - self.rect.centerx,
            player.rect.centery - self.rect.centery
        )

    def distance_to_point(self, x, y):
        return math.hypot(x - self.rect.centerx, y - self.rect.centery)

    def distance_to_base(self):
        if self.home_base is None:
            return 0
        return self.distance_to_point(
            self.home_base.rect.centerx,
            self.home_base.rect.centery
        )

    # =========================================================================
    #  PATHFINDING
    # =========================================================================

    def _request_path(self, pathfinding, goal_px, goal_py):
        """
        Pide un nuevo path BFS al módulo de pathfinding.
        Solo recalcula si el goal cambió de tile o el timer expiró.
        """
        if self.wall_set is None:
            return

        refresh = (
            PATH_REFRESH_TYPE3 if self.tank_type == 3
            else PATH_REFRESH_DEFAULT
        )

        # Determinar si hace falta recalcular
        goal_tile = (
            int(goal_px // self.tile_size),
            int(goal_py // self.tile_size)
        )
        needs_refresh = (
            self._path_timer >= refresh
            or self._path_goal != goal_tile
            or not self._path
        )

        if needs_refresh:
            new_path = pathfinding.find_path(
                self.rect.centerx, self.rect.centery,
                goal_px, goal_py,
                self.wall_set,
                self.map_width, self.map_height,
                self.tile_size
            )
            self._path       = new_path
            self._path_index = 0
            self._path_goal  = goal_tile
            self._path_timer = 0
        else:
            self._path_timer += 1

    def _next_path_waypoint(self):
        """
        Devuelve el siguiente waypoint del path activo,
        avanzando el índice si el tanque ya llegó al actual.
        Retorna None si el path está vacío o terminado.
        """
        while self._path_index < len(self._path):
            wp = self._path[self._path_index]
            if self.distance_to_point(*wp) < WAYPOINT_TOLERANCE:
                self._path_index += 1
            else:
                return wp
        return None

    # =========================================================================
    #  MOVIMIENTO  (un eje por frame — sin diagonal)
    # =========================================================================

    def _choose_axis(self, dx, dy):
        if (
            self._locked_axis is not None
            and self._dist_in_axis < DIR_LOCK_DISTANCE
        ):
            return self._locked_axis

        new_axis = "H" if abs(dx) >= abs(dy) else "V"
        if new_axis != self._locked_axis:
            self._locked_axis  = new_axis
            self._dist_in_axis = 0.0
        return self._locked_axis

    def _move_toward(self, tx, ty, walls):
        """
        Avanza hacia (tx, ty) en un solo eje.
        Si colisiona, intenta el eje alternativo para no quedarse pegado.
        """
        dx = tx - self.rect.centerx
        dy = ty - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist < 1:
            return

        ndx = dx / dist
        ndy = dy / dist
        axis = self._choose_axis(dx, dy)

        if axis == "H":
            step = ndx * self.speed
            self.rect.x += step
            if CollisionManager.check_wall_collision(self.rect, walls):
                self.rect.x -= step
                # Escape vertical
                step_v = ndy * self.speed
                self.rect.y += step_v
                if CollisionManager.check_wall_collision(self.rect, walls):
                    self.rect.y -= step_v
                else:
                    self._locked_axis  = "V"
                    self._dist_in_axis = 0.0
                    self.direction = "DOWN" if step_v > 0 else "UP"
            else:
                self.direction = "RIGHT" if step > 0 else "LEFT"
                self._dist_in_axis += abs(step)
        else:
            step = ndy * self.speed
            self.rect.y += step
            if CollisionManager.check_wall_collision(self.rect, walls):
                self.rect.y -= step
                # Escape horizontal
                step_h = ndx * self.speed
                self.rect.x += step_h
                if CollisionManager.check_wall_collision(self.rect, walls):
                    self.rect.x -= step_h
                else:
                    self._locked_axis  = "H"
                    self._dist_in_axis = 0.0
                    self.direction = "RIGHT" if step_h > 0 else "LEFT"
            else:
                self.direction = "DOWN" if step > 0 else "UP"
                self._dist_in_axis += abs(step)

        self.x = self.rect.x
        self.y = self.rect.y

    def _navigate_to(self, goal_px, goal_py, pathfinding, walls):
        """
        Mueve el tanque hacia (goal_px, goal_py) usando BFS.
        Sigue el waypoint más próximo del path; si no hay path,
        se mueve directamente (útil cuando ya está en línea de visión).
        """
        self._request_path(pathfinding, goal_px, goal_py)
        wp = self._next_path_waypoint()

        if wp is not None:
            self._move_toward(*wp, walls)
        else:
            # Path vacío: destino en la misma tile → movimiento directo
            self._move_toward(goal_px, goal_py, walls)

    # =========================================================================
    #  EMBOSCADA TIPO 3
    # =========================================================================

    def _ambush_target(self, player, enemies):
        """
        Calcula la posición de emboscada de ESTE tanque tipo 3.
        Cada tanque ocupa un ángulo distinto alrededor del jugador
        (separados 120° si hay 3 tanques), creando un cerco real.
        """
        # Contar cuántos tanques tipo 3 hay para distribuir ángulos
        t3_list = [e for e in enemies if e.tank_type == 3]
        n = max(len(t3_list), 1)
        angle_step = (2 * math.pi) / n
        angle = self.ambush_index * angle_step

        # Posición objetivo en el radio de flanqueo
        tx = player.rect.centerx + FLANK_ORBIT_RADIUS * math.cos(angle)
        ty = player.rect.centery + FLANK_ORBIT_RADIUS * math.sin(angle)
        return tx, ty

    # =========================================================================
    #  DISPARO
    # =========================================================================

    def try_shoot(self):
        if self.shoot_cooldown > 0:
            return None
        self.shoot_cooldown = SHOOT_COOLDOWN_FRAMES
        bullet_size = self.size // 4
        return Bullet(
            self.rect.centerx - bullet_size // 2,
            self.rect.centery - bullet_size // 2,
            bullet_size,
            self.direction,
            "ENEMY"
        )

    def _aim_at(self, tx, ty):
        """Actualiza self.direction apuntando a (tx, ty) sin moverse."""
        dx = tx - self.rect.centerx
        dy = ty - self.rect.centery
        if abs(dx) >= abs(dy):
            self.direction = "RIGHT" if dx > 0 else "LEFT"
        else:
            self.direction = "DOWN" if dy > 0 else "UP"

    # =========================================================================
    #  HELPERS DE ESTADO
    # =========================================================================

    def check_base_lost(self):
        if self.home_base is None:
            return self.base_lost
        return getattr(self.home_base, "destroyed", False)

    def nearest_base(self, objectives):
        active = [o for o in objectives if not getattr(o, "destroyed", False)]
        if not active:
            return None
        return min(active, key=lambda o: self.distance_to_point(
            o.rect.centerx, o.rect.centery
        ))

    # =========================================================================
    #  UPDATE PRINCIPAL
    # =========================================================================

    def update(self, player, objectives, walls, ai_state,
               pathfinding=None, enemies=None):
        """
        ai_state : dict devuelto por AIController.decide()
                   { "action": STATE_*, "target": (x,y)|None }
        pathfinding : instancia de Pathfinding (puede ser None en fallback)
        enemies     : lista completa de enemigos (para coordinar emboscada)

        Retorna una Bullet o None.
        """
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        action = ai_state.get("action", STATE_PATROL)
        target = ai_state.get("target", None)
        bullet = None
        pf     = pathfinding   # Alias corto

        # ------------------------------------------------------------------
        # PATROL — sigue waypoints de patrulla con pathfinding
        # ------------------------------------------------------------------
        if action == STATE_PATROL:
            pt = self.patrol_target
            if pt is not None:
                if self.distance_to_point(*pt) < WAYPOINT_TOLERANCE:
                    self._advance_patrol()
                elif pf:
                    self._navigate_to(*pt, pf, walls)
                else:
                    self._move_toward(*pt, walls)

        # ------------------------------------------------------------------
        # CHASE — perseguir al jugador por el mapa con pathfinding
        # ------------------------------------------------------------------
        elif action == STATE_CHASE:
            if target:
                if pf:
                    self._navigate_to(*target, pf, walls)
                else:
                    self._move_toward(*target, walls)

        # ------------------------------------------------------------------
        # ATTACK — apuntar y disparar sin moverse
        # ------------------------------------------------------------------
        elif action == STATE_ATTACK:
            self._aim_at(player.rect.centerx, player.rect.centery)
            bullet = self.try_shoot()

        # ------------------------------------------------------------------
        # RETURN — volver a la base con pathfinding
        # ------------------------------------------------------------------
        elif action == STATE_RETURN:
            if target:
                if pf:
                    self._navigate_to(*target, pf, walls)
                else:
                    self._move_toward(*target, walls)

        # ------------------------------------------------------------------
        # DEFEND — patrulla corta alrededor de la base
        # ------------------------------------------------------------------
        elif action == STATE_DEFEND:
            pt = self.patrol_target
            if pt is not None:
                if self.distance_to_point(*pt) < WAYPOINT_TOLERANCE:
                    self._advance_patrol()
                elif pf:
                    self._navigate_to(*pt, pf, walls)
                else:
                    self._move_toward(*pt, walls)

        # ------------------------------------------------------------------
        # FLANK — emboscada coordinada tipo 3
        # Cada tanque tipo 3 navega a su ángulo único alrededor del jugador.
        # Cuando llega a su posición, dispara. Si el jugador se mueve,
        # el path se recalcula (PATH_REFRESH_TYPE3 frames).
        # ------------------------------------------------------------------
        elif action == STATE_FLANK:
            e_list = enemies if enemies is not None else [self]
            amb_x, amb_y = self._ambush_target(player, e_list)
            dist_to_ambush = self.distance_to_point(amb_x, amb_y)

            if dist_to_ambush > WAYPOINT_TOLERANCE:
                # Moverse a la posición de emboscada
                if pf:
                    self._navigate_to(amb_x, amb_y, pf, walls)
                else:
                    self._move_toward(amb_x, amb_y, walls)

            # Disparar siempre que esté en rango, haya llegado o no
            self._aim_at(player.rect.centerx, player.rect.centery)
            bullet = self.try_shoot()

        # ------------------------------------------------------------------
        # ASSAULT — tipos 1/2 perdieron su base: persiguen sin límite
        # ------------------------------------------------------------------
        elif action == STATE_ASSAULT:
            if target:
                if pf:
                    self._navigate_to(*target, pf, walls)
                else:
                    self._move_toward(*target, walls)
            if self.distance_to_player(player) < ATTACK_RADIUS:
                self._aim_at(player.rect.centerx, player.rect.centery)
                bullet = self.try_shoot()

        return bullet
