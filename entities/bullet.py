import pygame

from entities.entity import Entity


class Bullet(Entity):

    def __init__(
        self,
        x,
        y,
        size,
        direction,
        owner
    ):

        super().__init__(
            x,
            y,
            size,
            (255, 255, 255)
        )

        self.direction = direction

        self.owner = owner

        self.speed = 6

        self.active = True

    def update(self):

        if self.direction == "UP":
            self.rect.y -= self.speed

        elif self.direction == "DOWN":
            self.rect.y += self.speed

        elif self.direction == "LEFT":
            self.rect.x -= self.speed

        elif self.direction == "RIGHT":
            self.rect.x += self.speed

        self.x = self.rect.x
        self.y = self.rect.y