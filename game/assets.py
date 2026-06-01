import os

import pygame

from game.constants import TILE_SIZE


ASSETS_DIR = "resourses"

DIRECTIONS = ("UP", "RIGHT", "DOWN", "LEFT")

# Pygame rota en sentido antihorario. Asumimos que el sprite original
# apunta hacia ARRIBA. Para apuntar a la derecha, rotamos -90°, etc.
ROTATIONS = {
    "UP": 0,
    "RIGHT": -90,
    "DOWN": 180,
    "LEFT": 90,
}


def _path(filename):
    return os.path.join(ASSETS_DIR, filename)


class Assets:
    """
    Carga todas las imágenes una sola vez. Debe instanciarse DESPUÉS de
    pygame.display.set_mode(), para que convert/convert_alpha funcionen.
    """

    def __init__(self):

        self.player = self._load_tank("jugador.png")

        self.enemy = {
            1: self._load_tank("enemigo1.png"),
            2: self._load_tank("enemigo2.png"),
            3: self._load_tank("enemigo3.png"),
        }

        self.objective_tipo1 = self._load_objective(
            tint=(255, 240, 90)
        )
        self.objective_tipo2 = self._load_objective(
            tint=(255, 90, 200)
        )

        self.wall = self._load_tile("muro.jpg")
        self.background = self._load_background("bg.jpg")

    # =========================
    # Cargadores
    # =========================

    def _load_tile(self, filename):
        img = pygame.image.load(_path(filename)).convert()
        return pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))

    def _load_tank(self, filename):
        img = pygame.image.load(_path(filename)).convert_alpha()
        scaled = pygame.transform.smoothscale(
            img, (TILE_SIZE, TILE_SIZE)
        )
        # Pre-rotaciones para las 4 direcciones cardinales.
        return {
            d: pygame.transform.rotate(scaled, ROTATIONS[d])
            for d in DIRECTIONS
        }

    def _load_objective(self, tint):
        img = pygame.image.load(_path("objetivo.png")).convert_alpha()
        scaled = pygame.transform.smoothscale(
            img, (TILE_SIZE, TILE_SIZE)
        )
        if tint is None:
            return scaled

        tinted = scaled.copy()
        tinted.fill(tint, special_flags=pygame.BLEND_MULT)
        return tinted

    def _load_background(self, filename):
        return pygame.image.load(_path(filename)).convert()

    # =========================
    # Accesores cómodos para draw
    # =========================

    def tank_sprite_for(self, entity, kind):
        """
        Devuelve la imagen rotada según entity.direction.
        kind = 'player' | int (1, 2, 3 para tipo de enemigo).
        """
        direction = getattr(entity, "direction", "UP")
        if direction not in DIRECTIONS:
            direction = "UP"

        if kind == "player":
            return self.player[direction]

        return self.enemy[kind][direction]

    def objective_sprite_for(self, objective):
        if getattr(objective, "tipo", 1) == 1:
            return self.objective_tipo1
        return self.objective_tipo2

    def background_scaled(self, width, height):
        return pygame.transform.scale(
            self.background, (width, height)
        )
