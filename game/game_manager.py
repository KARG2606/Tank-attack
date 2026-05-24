import pygame

from game.constants import (
    LOGICAL_WIDTH,
    LOGICAL_HEIGHT,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    TITLE,
    BACKGROUND_COLOR,
    TILE_SIZE
)
from game.level_loader import LevelLoader


class GameManager:

    def __init__(self):

        pygame.init()

        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.RESIZABLE
        )

        self.game_surface = pygame.Surface(
            (LOGICAL_WIDTH, LOGICAL_HEIGHT)
        )

        pygame.display.set_caption(TITLE)

        self.clock = pygame.time.Clock()

        self.running = True

        self.load_level()

    def load_level(self):

        self.level_loader = LevelLoader()

        self.level_loader.load_level(
            "maps/level1.txt"
        )

        self.bullets = []

    def handle_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if event.key == pygame.K_r:
                    self.load_level()

    def update(self):

        # =========================
        # Jugador
        # =========================
        if self.level_loader.player:

            bullet = self.level_loader.player.update(
                self.level_loader.walls
            )

            if bullet:
                self.bullets.append(bullet)

        # =========================
        # Enemigos
        # =========================
        for enemy in self.level_loader.enemies:

            enemy.update(
            self.level_loader.player,
            self.level_loader.objectives,
            self.level_loader.walls
        )

        # =========================
        # Balas
        # =========================
        for bullet in self.bullets:

            bullet.update()

            # Colisión con muros
            for wall in self.level_loader.walls:

                if bullet.rect.colliderect(wall.rect):

                    bullet.active = False

            # Colisión con enemigos
            for enemy in self.level_loader.enemies:

                if bullet.owner == "PLAYER":

                    if bullet.rect.colliderect(enemy.rect):

                        bullet.active = False

                        if enemy in self.level_loader.enemies:
                            self.level_loader.enemies.remove(enemy)

            # Colisión con objetivos
            for objective in self.level_loader.objectives:

                if bullet.rect.colliderect(objective.rect):

                    bullet.active = False

                    if objective in self.level_loader.objectives:
                        self.level_loader.objectives.remove(objective)

        # Eliminar balas inactivas
        self.bullets = [
            bullet
            for bullet in self.bullets
            if bullet.active
        ]

    def draw(self):

        self.game_surface.fill(BACKGROUND_COLOR)

        # Tamaño real del mapa
        map_pixel_width = (
            self.level_loader.map_width * TILE_SIZE
        )

        map_pixel_height = (
            self.level_loader.map_height * TILE_SIZE
        )

        # Centrar mapa
        offset_x = (
            (LOGICAL_WIDTH - map_pixel_width) // 2
        )

        offset_y = (
            (LOGICAL_HEIGHT - map_pixel_height) // 2
        )

        # =========================
        # Dibujar muros
        # =========================
        for wall in self.level_loader.walls:

            draw_rect = wall.rect.copy()

            draw_rect.x += offset_x
            draw_rect.y += offset_y

            pygame.draw.rect(
                self.game_surface,
                wall.color,
                draw_rect
            )

        # =========================
        # Dibujar enemigos
        # =========================
        for enemy in self.level_loader.enemies:

            draw_rect = enemy.rect.copy()

            draw_rect.x += offset_x
            draw_rect.y += offset_y

            pygame.draw.rect(
                self.game_surface,
                enemy.color,
                draw_rect
            )

        # =========================
        # Dibujar objetivos
        # =========================
        for objective in self.level_loader.objectives:

            draw_rect = objective.rect.copy()

            draw_rect.x += offset_x
            draw_rect.y += offset_y

            pygame.draw.rect(
                self.game_surface,
                objective.color,
                draw_rect
            )

        # =========================
        # Dibujar jugador
        # =========================
        if self.level_loader.player:

            player = self.level_loader.player

            draw_rect = player.rect.copy()

            draw_rect.x += offset_x
            draw_rect.y += offset_y

            pygame.draw.rect(
                self.game_surface,
                player.color,
                draw_rect
            )
        # =========================
        # Dibujar balas
        # =========================
        for bullet in self.bullets:

            draw_rect = bullet.rect.copy()

            draw_rect.x += offset_x
            draw_rect.y += offset_y

            pygame.draw.rect(
                self.game_surface,
                bullet.color,
                draw_rect
            )

        # Escalar a pantalla real
        scaled_surface = pygame.transform.scale(
            self.game_surface,
            (
                self.screen.get_width(),
                self.screen.get_height()
            )
        )

        # Dibujar en ventana
        self.screen.blit(scaled_surface, (0, 0))

        # Mostrar FPS
        fps = int(self.clock.get_fps())

        pygame.display.set_caption(
            f"{TITLE} - FPS: {fps}"
        )

        pygame.display.flip()

    def run(self):

        while self.running:

            self.clock.tick(FPS)

            self.handle_events()

            self.update()

            self.draw()

        pygame.quit()