import pygame

from entities.entity import Entity

from game.collision_manager import CollisionManager

from entities.bullet import Bullet


class PlayerTank(Entity):

    MAX_LIVES = 3
    INVULN_FRAMES = 90

    def __init__(self, x, y, size):

        super().__init__(
            x,
            y,
            size,
            (0, 200, 0)
        )

        self.speed = 2

        self.direction = "UP"

        self.shoot_cooldown = 0

        self._spawn_x = x
        self._spawn_y = y

        self._lives = PlayerTank.MAX_LIVES
        self._invuln_timer = 0

    @property
    def lives(self):
        return self._lives

    @property
    def is_invulnerable(self):
        return self._invuln_timer > 0

    def take_damage(self):

        if self._invuln_timer > 0:
            return False

        self._lives -= 1

        if self._lives > 0:
            self._respawn()

        return True

    def _respawn(self):

        self.rect.x = self._spawn_x
        self.rect.y = self._spawn_y

        self.x = self._spawn_x
        self.y = self._spawn_y

        self._invuln_timer = PlayerTank.INVULN_FRAMES

    def move(self, dx, dy, walls):

        # Movimiento horizontal
        self.rect.x += dx

        if CollisionManager.check_wall_collision(
            self.rect,
            walls
        ):
            self.rect.x -= dx

        # Movimiento vertical
        self.rect.y += dy

        if CollisionManager.check_wall_collision(
            self.rect,
            walls
        ):
            self.rect.y -= dy

        # Actualizar posición lógica
        self.x = self.rect.x
        self.y = self.rect.y

    def shoot(self):

        bullet_size = self.size // 4

        bullet_x = (
            self.rect.centerx
            - bullet_size // 2
        )

        bullet_y = (
            self.rect.centery
            - bullet_size // 2
        )

        return Bullet(
            bullet_x,
            bullet_y,
            bullet_size,
            self.direction,
            "PLAYER"
        )

    def update(self, walls):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        if self._invuln_timer > 0:
            self._invuln_timer -= 1

        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0

        # Arriba
        if keys[pygame.K_w] or keys[pygame.K_UP]:

            dy = -self.speed

            self.direction = "UP"

        # Abajo
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:

            dy = self.speed

            self.direction = "DOWN"

        # Izquierda
        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:

            dx = -self.speed

            self.direction = "LEFT"

        # Derecha
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:

            dx = self.speed

            self.direction = "RIGHT"

        self.move(dx, dy, walls)

        if keys[pygame.K_SPACE]:

            if self.shoot_cooldown == 0:

                self.shoot_cooldown = 45

                return self.shoot()

        return None