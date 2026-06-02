import os

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
from game.assets import Assets
from prolog.prolog_manager import PrologManager
from util.generador_aleatorio import GeneradorAleatorio
from logic.ai_controller import AIController
from logic.tactical_manager import TacticalManager
from logic.pathfinding import Pathfinding


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


# Botón principal en coordenadas lógicas (1280×720). Lo bastante ancho
# para que entre "SIGUIENTE" en mayúsculas con margen.
START_BUTTON_RECT = pygame.Rect(
    LOGICAL_WIDTH // 2 - 220,
    LOGICAL_HEIGHT // 2 + 20,
    440,
    80,
)

# Música de fondo. Buscamos cualquiera de estos archivos en resourses/.
# El primero que exista se carga; si ninguno existe el juego va en silencio.
MUSIC_CANDIDATES = (
    "music.ogg",
    "music.mp3",
    "music.wav",
    "battle.ogg",
    "battle.mp3",
)

MUSIC_VOLUME_DEFAULT = 0.3  # suave


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

        # Fuente específica para botones (más chica que la big_font
        # para que el texto no rebase el borde).
        self.button_font = pygame.font.SysFont(
            "Arial", 44, bold=True
        )

        # Sprites cargados una sola vez.
        self.assets = Assets()
        self._level_background = None

        # Música de fondo (autodescubierta en resourses/).
        self._music_loaded = False
        self._music_muted = False
        self._music_volume = MUSIC_VOLUME_DEFAULT
        self._init_audio()

        self.generador = GeneradorAleatorio()

        self.prolog_manager = PrologManager()

        # Capas lógicas de IA (decisión + coordinación + pathfinding).
        self.ai_controller = AIController(self.prolog_manager)
        self.tactical_manager = TacticalManager()
        self.pathfinding = Pathfinding()

        self._current_level_idx = 0
        self.level_loader = None
        self.bullets = []

        # Cada cuántos frames se consulta a Prolog la nueva decisión.
        self._prolog_query_interval = 60  # 1 segundo a 60 FPS
        self._prolog_query_timer = 0

    # =========================
    # Audio
    # =========================
    def _init_audio(self):
        """
        Inicializa el mixer y carga la primera pista que encuentre en
        resourses/ entre los nombres candidatos. Si no hay nada, el
        juego corre en silencio sin romper.
        """
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error:
            return

        for name in MUSIC_CANDIDATES:
            path = os.path.join("resourses", name)
            if not os.path.isfile(path):
                continue
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(self._music_volume)
                pygame.mixer.music.play(loops=-1)
                self._music_loaded = True
                return
            except pygame.error:
                continue

    def _toggle_mute(self):
        if not self._music_loaded:
            return
        self._music_muted = not self._music_muted
        pygame.mixer.music.set_volume(
            0 if self._music_muted else self._music_volume
        )

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

        # Regenera el grafo Prolog y limpia el caché de rutas.
        self.prolog_manager.generate_graph(self.level_loader)
        self.prolog_manager.clear_cache()

        # Reinicia memoria táctica (último avistamiento del jugador).
        self.tactical_manager = TacticalManager()

        # Empareja cada enemigo con un objetivo a custodiar.
        self._pair_enemies_with_objectives()

        self.bullets = []
        self.state = STATE_PLAYING

    def _pair_enemies_with_objectives(self):
        """Asigna a cada enemigo el objetivo más cercano sin asignar."""
        assigned = set()
        for enemy in self.level_loader.enemies:
            best = None
            best_dist = float("inf")
            for obj in self.level_loader.objectives:
                if id(obj) in assigned:
                    continue
                dx = obj.rect.centerx - enemy.rect.centerx
                dy = obj.rect.centery - enemy.rect.centery
                d = dx * dx + dy * dy
                if d < best_dist:
                    best_dist = d
                    best = obj
            if best is not None:
                enemy.target_objective = best
                assigned.add(id(best))

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

                elif event.key == pygame.K_m:
                    self._toggle_mute()

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

            # Memoria táctica compartida (TacticalManager).
            self.tactical_manager.update(self.level_loader.player)

        # =========================
        # Consulta a Prolog la decisión de cada enemigo cada N frames.
        # =========================
        self._prolog_query_timer -= 1
        if self._prolog_query_timer <= 0:
            self._prolog_query_timer = self._prolog_query_interval
            self.prolog_manager.sync_state(self.level_loader)
            for idx, enemy in enumerate(self.level_loader.enemies):
                enemy.prolog_action = (
                    self.prolog_manager.consultar_accion(idx)
                )
                # Si Prolog dice atacar, este enemigo vio al jugador y
                # avisa a sus aliados (coordinación — puntos extra).
                if enemy.prolog_action == "atacar":
                    self.prolog_manager.asentar_avistamiento(idx)

        for enemy in self.level_loader.enemies:

            enemy_bullet = enemy.update(
                self.level_loader.player,
                self.level_loader.objectives,
                self.level_loader.walls,
                self.level_loader.enemies,
                self.ai_controller,
                self.tactical_manager,
                self.pathfinding,
                TILE_SIZE,
                self.level_loader.map_width,
                self.level_loader.map_height,
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

        text = self.button_font.render(label, True, (255, 255, 255))
        text_rect = text.get_rect(center=rect.center)
        self.game_surface.blit(text, text_rect)

    def _draw_level(self):

        self.game_surface.fill(BACKGROUND_COLOR)

        map_pixel_width = self.level_loader.map_width * TILE_SIZE
        map_pixel_height = self.level_loader.map_height * TILE_SIZE

        offset_x = (LOGICAL_WIDTH - map_pixel_width) // 2
        offset_y = (LOGICAL_HEIGHT - map_pixel_height) // 2

        # Fondo del mapa.
        if (
            self._level_background is None
            or self._level_background.get_size()
            != (map_pixel_width, map_pixel_height)
        ):
            self._level_background = self.assets.background_scaled(
                map_pixel_width, map_pixel_height
            )
        self.game_surface.blit(
            self._level_background, (offset_x, offset_y)
        )

        # Muros.
        for wall in self.level_loader.walls:
            self.game_surface.blit(
                self.assets.wall,
                (wall.rect.x + offset_x, wall.rect.y + offset_y),
            )

        # Objetivos.
        for objective in self.level_loader.objectives:
            sprite = self.assets.objective_sprite_for(objective)
            self.game_surface.blit(
                sprite,
                (
                    objective.rect.x + offset_x,
                    objective.rect.y + offset_y,
                ),
            )

        # Enemigos (con halo de rol debajo para reconocerlos).
        for enemy in self.level_loader.enemies:
            center = (
                enemy.rect.centerx + offset_x,
                enemy.rect.centery + offset_y,
            )
            self._draw_halo(center, enemy.color)

            sprite = self.assets.tank_sprite_for(
                enemy, enemy.enemy_type
            )
            rect = sprite.get_rect(center=center)
            self.game_surface.blit(sprite, rect)

        # Jugador (halo verde + parpadeo si invulnerable).
        if self.level_loader.player:
            player = self.level_loader.player
            blink_visible = (
                not player.is_invulnerable
                or (pygame.time.get_ticks() // 80) % 2 == 0
            )
            if blink_visible:
                center = (
                    player.rect.centerx + offset_x,
                    player.rect.centery + offset_y,
                )
                self._draw_halo(center, (60, 220, 80))

                sprite = self.assets.tank_sprite_for(
                    player, "player"
                )
                rect = sprite.get_rect(center=center)
                self.game_surface.blit(sprite, rect)

        # Balas (cuadritos blancos — no hay sprite específico).
        for bullet in self.bullets:
            r = bullet.rect.copy()
            r.x += offset_x
            r.y += offset_y
            pygame.draw.rect(self.game_surface, bullet.color, r)

    def _draw_halo(self, center, color):
        """
        Disco semitransparente bajo un tanque para distinguirlo
        del resto (color del rol).
        """
        radius = TILE_SIZE // 2 + 4
        halo = pygame.Surface(
            (radius * 2, radius * 2), pygame.SRCALPHA
        )
        pygame.draw.circle(
            halo, (*color, 140), (radius, radius), radius
        )
        rect = halo.get_rect(center=center)
        self.game_surface.blit(halo, rect)

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
