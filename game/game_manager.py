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
from prolog.prolog_manager import PrologManager
from logic.ai_controller import AIController
from logic.tactical_manager import TacticalManager
from logic.pathfinding import Pathfinding


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

        self.clock        = pygame.time.Clock()
        self.running      = True

        self.prolog_manager   = PrologManager()
        self.tactical_manager = TacticalManager()
        self.ai_controller    = AIController(self.prolog_manager)
        self.pathfinding      = Pathfinding()

        self.load_level()

    # =========================================================================
    #  CARGA DE NIVEL
    # =========================================================================

    def load_level(self):

        self.level_loader = LevelLoader()
        self.level_loader.load_level("maps/level1.txt")

        self.bullets = []

        self.prolog_manager.generate_graph(self.level_loader)

        # Limpiar cache de pathfinding al recargar (muros nuevos)
        self.pathfinding.clear_cache()

        # Construir wall_set una sola vez para todo el nivel
        self._wall_set = Pathfinding.build_wall_set(
            self.level_loader.walls,
            TILE_SIZE
        )

        # Inyectar datos de pathfinding en cada tanque enemigo
        for enemy in self.level_loader.enemies:
            enemy.setup_pathfinding(
                self._wall_set,
                self.level_loader.map_width,
                self.level_loader.map_height,
                TILE_SIZE
            )

        # Asignar base más cercana a tipos 1 y 2
        AIController.assign_bases(
            self.level_loader.enemies,
            self.level_loader.objectives
        )

    # =========================================================================
    #  EVENTOS
    # =========================================================================

    def handle_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if event.key == pygame.K_r:
                    self.load_level()
                    self.prolog_manager.clear_cache()

    # =========================================================================
    #  UPDATE
    # =========================================================================

    def update(self):

        # --- Jugador ---
        if self.level_loader.player:
            bullet = self.level_loader.player.update(
                self.level_loader.walls
            )
            if bullet:
                self.bullets.append(bullet)

        # --- Enemigos ---
        self.tactical_manager.update(self.level_loader.player)

        for enemy in self.level_loader.enemies[:]:

            ai_state = self.ai_controller.decide(
                enemy,
                self.level_loader.player,
                self.level_loader.objectives,
                self.level_loader.walls
            )

            bullet = enemy.update(
                self.level_loader.player,
                self.level_loader.objectives,
                self.level_loader.walls,
                ai_state,
                pathfinding=self.pathfinding,
                enemies=self.level_loader.enemies
            )

            if bullet:
                self.bullets.append(bullet)

        # --- Balas ---
        for bullet in self.bullets:

            bullet.update()

            # Colisión con muros
            if bullet.active:
                for wall in self.level_loader.walls:
                    if bullet.rect.colliderect(wall.rect):
                        bullet.active = False
                        break

            # Colisión con enemigos (bala del jugador)
            if bullet.active and bullet.owner == "PLAYER":
                for enemy in self.level_loader.enemies:
                    if bullet.rect.colliderect(enemy.rect):
                        bullet.active = False
                        self.level_loader.enemies.remove(enemy)
                        break

            # Colisión con jugador (bala enemiga)
            if (
                bullet.active
                and bullet.owner == "ENEMY"
                and self.level_loader.player
            ):
                if bullet.rect.colliderect(self.level_loader.player.rect):
                    bullet.active = False
                    # Aquí puedes restar vida al jugador

            # Colisión con objetivos
            if bullet.active:
                for objective in self.level_loader.objectives[:]:
                    if bullet.rect.colliderect(objective.rect):
                        bullet.active = False
                        objective.destroyed = True
                        self.level_loader.objectives.remove(objective)
                        # Reasignar bases; tipos sin base → ASSAULT
                        AIController.assign_bases(
                            self.level_loader.enemies,
                            self.level_loader.objectives
                        )
                        break

        self.bullets = [b for b in self.bullets if b.active]

    # =========================================================================
    #  DRAW
    # =========================================================================

    def draw(self):

        self.game_surface.fill(BACKGROUND_COLOR)

        map_pixel_width  = self.level_loader.map_width  * TILE_SIZE
        map_pixel_height = self.level_loader.map_height * TILE_SIZE
        offset_x = (LOGICAL_WIDTH  - map_pixel_width)  // 2
        offset_y = (LOGICAL_HEIGHT - map_pixel_height) // 2

        for wall in self.level_loader.walls:
            pygame.draw.rect(
                self.game_surface, wall.color,
                wall.rect.move(offset_x, offset_y)
            )

        for objective in self.level_loader.objectives:
            pygame.draw.rect(
                self.game_surface, objective.color,
                objective.rect.move(offset_x, offset_y)
            )

        for enemy in self.level_loader.enemies:
            pygame.draw.rect(
                self.game_surface, enemy.color,
                enemy.rect.move(offset_x, offset_y)
            )

        if self.level_loader.player:
            pygame.draw.rect(
                self.game_surface, self.level_loader.player.color,
                self.level_loader.player.rect.move(offset_x, offset_y)
            )

        for bullet in self.bullets:
            pygame.draw.rect(
                self.game_surface, bullet.color,
                bullet.rect.move(offset_x, offset_y)
            )

        scaled_surface = pygame.transform.scale(
            self.game_surface,
            (self.screen.get_width(), self.screen.get_height())
        )
        self.screen.blit(scaled_surface, (0, 0))

        pygame.display.set_caption(
            f"{TITLE} - FPS: {int(self.clock.get_fps())}"
        )
        pygame.display.flip()

    # =========================================================================
    #  LOOP PRINCIPAL
    # =========================================================================

    def run(self):

        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()

        pygame.quit()
