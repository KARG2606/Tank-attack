import pygame

pygame.init()

# Resolución lógica del juego
LOGICAL_WIDTH = 1280
LOGICAL_HEIGHT = 720

# FPS
FPS = 60

# Título
TITLE = "Tank Attack"

# Colores
BACKGROUND_COLOR = (20, 20, 20)

# Resolución monitor
SCREEN_INFO = pygame.display.Info()

SCREEN_WIDTH = SCREEN_INFO.current_w
SCREEN_HEIGHT = SCREEN_INFO.current_h

#fase 2
TILE_SIZE = 32