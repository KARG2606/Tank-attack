import math
import random

from entities.entity import Entity

from ai.enemy_state import EnemyState


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
    # IA principal
    # =========================
    def update(
        self,
        player,
        objectives,
        walls
    ):

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

            # Mantener posición táctica
            pass

        # =========================
        # RETREAT
        # =========================
        elif self.state == EnemyState.RETREAT:

            self.move_away_from(
                player.rect.centerx,
                player.rect.centery,
                walls
            )

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