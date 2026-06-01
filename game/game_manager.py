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
from util.generador_aleatorio import GeneradorAleatorio


LEVELS = [
    "maps/level1.txt",
    "maps/level2.txt",
    "maps/level3.txt",
]

STATE_MENU = "MENU"
STATE_PLAYING = "PLAYING"
STATE_LEVEL_CLEAR = "LEVEL_CLEAR"
STATE_WIN = "WIN"
STATE_GAME_OVER = "GAME_OVER"


# Botón "INICIAR" en coordenadas lógicas (1280×720).
START_BUTTON_RECT = pygame.Rect(
    LOGICAL_WIDTH // 2 - 160,
    LOGICAL_HEIGHT // 2 + 20,
    320,
    72,
)


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

        self.state = STATE_MENU

        self.hud_font = pygame.font.SysFont(
            "Arial", 24, bold=True
        )

        self.big_font = pygame.font.SysFont(
            "Arial", 64, bold=True
        )

        self.title_font = pygame.font.SysFont(
            "Arial", 96, bold=True
        )

        self.generador = GeneradorAleatorio()

        self.prolog_manager = PrologManager()

        self._current_level_idx = 0
        self.level_loader = None
        self.bullets = []

    # =========================
    # Flujo de niveles
    # =========================
    def _start_game(self):
        self._current_level_idx = 0
        self._load_current_level()

    def _load_current_level(self):

        path = LEVELS[self._current_level_idx]

        self.level_loader = LevelLoader()
        self.level_loader.load_level(path)

        # Aleatoriza posiciones de objetivos y enemigos.
        self.generador.aleatorizar_nivel(self.level_loader)

        # Regenera el grafo Prolog para el mapa actual.
        self.prolog_manager.generate_graph(self.level_loader)

        self.bullets = []
        self.state = STATE_PLAYING

    def _advance_after_clear(self):
        self._current_level_idx += 1

        if self._current_level_idx >= len(LEVELS):
            self.state = STATE_WIN
        else:
            self._load_current_level()

    # =========================
    # Conversión mouse → coords lógicas
    # =========================
    def _to_logical(self, pos):
        sx = max(1, self.screen.get_width())
        sy = max(1, self.screen.get_height())
        return (
            pos[0] * LOGICAL_WIDTH // sx,
            pos[1] * LOGICAL_HEIGHT // sy,
        )

    # =========================
    # Eventos
    # =========================
    def handle_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    self.running = False

                elif self.state == STATE_MENU and event.key in (
                    pygame.K_RETURN, pygame.K_SPACE
                ):
                    self._start_game()

                elif self.state == STATE_LEVEL_CLEAR and event.key in (
                    pygame.K_RETURN, pygame.K_SPACE
                ):
                    self._advance_after_clear()

                elif self.state in (STATE_WIN, STATE_GAME_OVER) and event.key == pygame.K_r:
                    self.state = STATE_MENU

                elif self.state == STATE_PLAYING and event.key == pygame.K_r:
                    self._load_current_level()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                logical_pos = self._to_logical(event.pos)

                if self.state == STATE_MENU and START_BUTTON_RECT.collidepoint(logical_pos):
                    self._start_game()

                elif self.state == STATE_LEVEL_CLEAR and START_BUTTON_RECT.collidepoint(logical_pos):
                    self._advance_after_clear()

    # =========================
    # Update
    # =========================
    def update(self):

        if self.state != STATE_PLAYING:
            return

        if self.level_loader.player:

            bullet = self.level_loader.player.update(
                self.level_loader.walls
            )

            if bullet:
                self.bullets.append(bullet)

        for enemy in self.level_loader.enemies:

            enemy_bullet = enemy.update(
                self.level_loader.player,
                self.level_loader.objectives,
                self.level_loader.walls
            )

            if enemy_bullet:
                self.bullets.append(enemy_bullet)

        player = self.level_loader.player

        for bullet in self.bullets:

            bullet.update()

            for wall in self.level_loader.walls:

                if bullet.rect.colliderect(wall.rect):
                    bullet.active = False

            if bullet.owner == "PLAYER":

                for enemy in self.level_loader.enemies:

                    if bullet.rect.colliderect(enemy.rect):

                        bullet.active = False

                        if enemy in self.level_loader.enemies:
                            self.level_loader.enemies.remove(enemy)

                for objective in self.level_loader.objectives:

                    if bullet.rect.colliderect(objective.rect):

                        bullet.active = False

                        if objective in self.level_loader.objectives:
                            self.level_loader.objectives.remove(objective)

            elif bullet.owner == "ENEMY":

                if (
                    player
                    and bullet.rect.colliderect(player.rect)
                ):
                    if player.take_damage():
                        bullet.active = False

        self.bullets = [b for b in self.bullets if b.active]

        # =========================
        # Condiciones de fin
        # =========================
        if not self.level_loader.objectives:

            if self._current_level_idx + 1 >= len(LEVELS):
                self.state = STATE_WIN
            else:
                self.state = STATE_LEVEL_CLEAR

        elif player and player.lives <= 0:
            self.state = STATE_GAME_OVER

    # =========================
    # Dibujo
    # =========================
    def draw(self):

        if self.state == STATE_MENU:
            self._draw_menu()
        else:
            self._draw_level()
            self._draw_hud()
            self._draw_overlay()

        scaled_surface = pygame.transform.scale(
            self.game_surface,
            (
                self.screen.get_width(),
                self.screen.get_height()
            )
        )

        self.screen.blit(scaled_surface, (0, 0))

        fps = int(self.clock.get_fps())
        pygame.display.set_caption(f"{TITLE} - FPS: {fps}")

        pygame.display.flip()

    def _draw_menu(self):

        self.game_surface.fill((15, 25, 40))

        title = self.title_font.render(
            "TANK ATTACK", True, (240, 220, 0)
        )
        title_rect = title.get_rect(
            center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 - 120)
        )
        self.game_surface.blit(title, title_rect)

        subtitle = self.hud_font.render(
            "Destruye todos los objetivos enemigos en 3 niveles",
            True,
            (200, 200, 200),
        )
        subtitle_rect = subtitle.get_rect(
            center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 - 40)
        )
        self.game_surface.blit(subtitle, subtitle_rect)

        self._draw_button(
            START_BUTTON_RECT,
            "INICIAR",
            base_color=(40, 140, 60),
            hover_color=(60, 180, 80),
        )

        hint = self.hud_font.render(
            "Enter / Espacio / clic para empezar    ESC para salir",
            True,
            (160, 160, 160),
        )
        hint_rect = hint.get_rect(
            center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 60)
        )
        self.game_surface.blit(hint, hint_rect)

    def _draw_button(self, rect, label, base_color, hover_color):

        mouse_logical = self._to_logical(pygame.mouse.get_pos())
        hovered = rect.collidepoint(mouse_logical)
        color = hover_color if hovered else base_color

        pygame.draw.rect(self.game_surface, color, rect, border_radius=12)
        pygame.draw.rect(
            self.game_surface, (255, 255, 255), rect, width=3, border_radius=12
        )

        text = self.big_font.render(label, True, (255, 255, 255))
        text_rect = text.get_rect(center=rect.center)
        self.game_surface.blit(text, text_rect)

    def _draw_level(self):

        self.game_surface.fill(BACKGROUND_COLOR)

        map_pixel_width = self.level_loader.map_width * TILE_SIZE
        map_pixel_height = self.level_loader.map_height * TILE_SIZE

        offset_x = (LOGICAL_WIDTH - map_pixel_width) // 2
        offset_y = (LOGICAL_HEIGHT - map_pixel_height) // 2

        for wall in self.level_loader.walls:
            r = wall.rect.copy()
            r.x += offset_x
            r.y += offset_y
            pygame.draw.rect(self.game_surface, wall.color, r)

        for enemy in self.level_loader.enemies:
            r = enemy.rect.copy()
            r.x += offset_x
            r.y += offset_y
            pygame.draw.rect(self.game_surface, enemy.color, r)

        for objective in self.level_loader.objectives:
            r = objective.rect.copy()
            r.x += offset_x
            r.y += offset_y
            pygame.draw.rect(self.game_surface, objective.color, r)

        if self.level_loader.player:
            player = self.level_loader.player
            r = player.rect.copy()
            r.x += offset_x
            r.y += offset_y
            blink_visible = (
                not player.is_invulnerable
                or (pygame.time.get_ticks() // 80) % 2 == 0
            )
            if blink_visible:
                pygame.draw.rect(self.game_surface, player.color, r)

        for bullet in self.bullets:
            r = bullet.rect.copy()
            r.x += offset_x
            r.y += offset_y
            pygame.draw.rect(self.game_surface, bullet.color, r)

    def _draw_hud(self):

        if self.level_loader and self.level_loader.player:
            lives_text = self.hud_font.render(
                f"Vidas: {self.level_loader.player.lives}",
                True,
                (255, 255, 255),
            )
            self.game_surface.blit(lives_text, (16, 12))

        if self.level_loader:
            obj_text = self.hud_font.render(
                f"Objetivos: {len(self.level_loader.objectives)}",
                True,
                (255, 255, 255),
            )
            self.game_surface.blit(obj_text, (16, 40))

        nivel_text = self.hud_font.render(
            f"Nivel {self._current_level_idx + 1} / {len(LEVELS)}",
            True,
            (255, 255, 255),
        )
        self.game_surface.blit(
            nivel_text, (LOGICAL_WIDTH - 200, 12)
        )

    def _draw_overlay(self):

        if self.state == STATE_PLAYING:
            return

        overlay = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
        overlay.set_alpha(160)
        overlay.fill((0, 0, 0))
        self.game_surface.blit(overlay, (0, 0))

        if self.state == STATE_LEVEL_CLEAR:
            msg = f"Nivel {self._current_level_idx + 1} superado"
            color = (80, 255, 120)
            hint = "Enter / clic INICIAR para continuar"
            button_label = "SIGUIENTE"

        elif self.state == STATE_WIN:
            msg = "¡VICTORIA!"
            color = (80, 255, 120)
            hint = "R para volver al menú    ESC para salir"
            button_label = None

        else:  # GAME_OVER
            msg = "GAME OVER"
            color = (255, 80, 80)
            hint = "R para volver al menú    ESC para salir"
            button_label = None

        label = self.big_font.render(msg, True, color)
        label_rect = label.get_rect(
            center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 - 60)
        )
        self.game_surface.blit(label, label_rect)

        if button_label:
            self._draw_button(
                START_BUTTON_RECT,
                button_label,
                base_color=(40, 140, 60),
                hover_color=(60, 180, 80),
            )
            hint_y = LOGICAL_HEIGHT - 60
        else:
            hint_y = LOGICAL_HEIGHT // 2 + 40

        hint_label = self.hud_font.render(
            hint, True, (220, 220, 220)
        )
        hint_rect = hint_label.get_rect(
            center=(LOGICAL_WIDTH // 2, hint_y)
        )
        self.game_surface.blit(hint_label, hint_rect)

    def run(self):

        while self.running:

            self.clock.tick(FPS)

            self.handle_events()

            self.update()

            self.draw()

        pygame.quit()
