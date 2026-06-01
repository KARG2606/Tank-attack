import math
import random

from entities.entity import Entity
from entities.bullet import Bullet

from ai.enemy_state import EnemyState


# Cooldown de disparo por tipo (frames a 60 FPS).
# Tipo 1: rápido, ráfaga corta. Tipo 2: medio. Tipo 3: lento pero pesado.
SHOOT_COOLDOWN_BY_TYPE = {
    1: 60,
    2: 90,
    3: 120,
}


class EnemyTank(Entity):

    def __init__(
        self,
        x,
        y,
        size,
        enemy_type=1
    ):

        self.enemy_type = enemy_type

        # =========================
        # Colores por tipo
        # =========================
        if enemy_type == 1:
            color = (200, 0, 0)
            self.speed = 1

        elif enemy_type == 2:
            color = (0, 120, 255)
            self.speed = 1

        else:
            color = (255, 120, 0)
            self.speed = 2

        super().__init__(
            x,
            y,
            size,
            color
        )

        # =========================
        # FSM
        # =========================
        self.state = EnemyState.DEFEND

        self.direction = "DOWN"

        # =========================
        # IA
        # =========================
        self.target_objective = None

        self.detection_range = 220

        self.move_timer = 0

        self.current_direction = None

        # =========================
        # Disparo
        # =========================
        self._shoot_cooldown = 0
        self._shoot_cooldown_max = SHOOT_COOLDOWN_BY_TYPE.get(
            enemy_type, 90
        )

    # =========================
    # Distancia jugador
    # =========================
    def distance_to_player(
        self,
        player
    ):

        dx = (
            player.rect.centerx
            - self.rect.centerx
        )

        dy = (
            player.rect.centery
            - self.rect.centery
        )

        return math.sqrt(dx * dx + dy * dy)
    
    def collide_with_walls(
        self,
        walls
    ):

        for wall in walls:

            if self.rect.colliderect(wall.rect):

                return True

        return False

    # =========================
    # FSM
    # =========================
    def update_state(
        self,
        player
    ):

        distance = self.distance_to_player(
            player
        )

        # =========================
        # Muy cerca → RETREAT
        # =========================
        if distance < 80:

            self.state = EnemyState.RETREAT

        # =========================
        # Distancia ataque
        # =========================
        elif distance <= self.detection_range:

            self.state = EnemyState.ATTACK

        # =========================
        # Defender objetivo
        # =========================
        else:

            self.state = EnemyState.DEFEND

    # =========================
    # Movimiento
    # =========================
    def move_towards(
        self,
        target_x,
        target_y,
        walls
    ):

        # =========================
        # Recalcular dirección
        # =========================
        if self.move_timer <= 0:

            dx = (
                target_x
                - self.rect.centerx
            )

            dy = (
                target_y
                - self.rect.centery
            )

            if abs(dx) > abs(dy):

                if dx > 0:
                    self.current_direction = "RIGHT"

                else:
                    self.current_direction = "LEFT"

            else:

                if dy > 0:
                    self.current_direction = "DOWN"

                else:
                    self.current_direction = "UP"

            self.move_timer = 15

        else:

            self.move_timer -= 1

        # =========================
        # Guardar posición previa
        # =========================
        old_x = self.rect.x
        old_y = self.rect.y

        # =========================
        # Movimiento
        # =========================
        if self.current_direction == "RIGHT":

            self.rect.x += self.speed

        elif self.current_direction == "LEFT":

            self.rect.x -= self.speed

        elif self.current_direction == "DOWN":

            self.rect.y += self.speed

        elif self.current_direction == "UP":

            self.rect.y -= self.speed

        # =========================
        # Colisión
        # =========================
        if self.collide_with_walls(walls):

            # Volver atrás
            self.rect.x = old_x
            self.rect.y = old_y

            # Cambiar dirección después
            self.move_timer = 0

        self.direction = self.current_direction

        self.x = self.rect.x
        self.y = self.rect.y
        
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

        bullet_size = self.size // 4

        bullet_x = (
            self.rect.centerx - bullet_size // 2
        )

        bullet_y = (
            self.rect.centery - bullet_size // 2
        )

        return Bullet(
            bullet_x,
            bullet_y,
            bullet_size,
            self._direction_to(player),
            "ENEMY"
        )

    # =========================
    # IA principal
    # =========================
    def update(
        self,
        player,
        objectives,
        walls
    ):

        if self._shoot_cooldown > 0:
            self._shoot_cooldown -= 1

        # =========================
        # Elegir objetivo cercano
        # =========================
        if not self.target_objective:

            closest_distance = 999999

            for objective in objectives:

                dx = (
                    objective.rect.centerx
                    - self.rect.centerx
                )

                dy = (
                    objective.rect.centery
                    - self.rect.centery
                )

                distance = math.sqrt(
                    dx * dx + dy * dy
                )

                if distance < closest_distance:

                    closest_distance = distance

                    self.target_objective = objective

        # =========================
        # FSM
        # =========================
        self.update_state(player)

        # =========================
        # DEFEND
        # =========================
        if self.state == EnemyState.DEFEND:

            if self.target_objective:

                self.move_towards(
                    self.target_objective.rect.centerx,
                    self.target_objective.rect.centery,
                    walls
                )

        # =========================
        # ATTACK
        # =========================
        elif self.state == EnemyState.ATTACK:

            # Mantiene posición táctica y dispara hacia el jugador.
            return self.shoot(player)

        # =========================
        # RETREAT
        # =========================
        elif self.state == EnemyState.RETREAT:

            self.move_away_from(
                player.rect.centerx,
                player.rect.centery,
                walls
            )

        return None

    def move_away_from(
        self,
        target_x,
        target_y,
        walls
    ):

        dx = (
            self.rect.centerx
            - target_x
        )

        dy = (
            self.rect.centery
            - target_y
        )

        if abs(dx) > abs(dy):

            if dx > 0:
                self.current_direction = "RIGHT"

            else:
                self.current_direction = "LEFT"

        else:

            if dy > 0:
                self.current_direction = "DOWN"

            else:
                self.current_direction = "UP"

        old_x = self.rect.x
        old_y = self.rect.y

        if self.current_direction == "RIGHT":

            self.rect.x += self.speed

        elif self.current_direction == "LEFT":

            self.rect.x -= self.speed

        elif self.current_direction == "DOWN":

            self.rect.y += self.speed

        elif self.current_direction == "UP":

            self.rect.y -= self.speed

        if self.collide_with_walls(walls):

            self.rect.x = old_x
            self.rect.y = old_y

        self.direction = self.current_direction

        self.x = self.rect.x
        self.y = self.rect.y