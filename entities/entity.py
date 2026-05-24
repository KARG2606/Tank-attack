import pygame


class Entity:

    def __init__(self, x, y, size, color):

        self.x = x
        self.y = y

        self.size = size

        self.color = color

        self.rect = pygame.Rect(
            self.x,
            self.y,
            self.size,
            self.size
        )

    def draw(self, surface):

        pygame.draw.rect(
            surface,
            self.color,
            self.rect
        )