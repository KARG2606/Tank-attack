from entities.entity import Entity


class Wall(Entity):

    def __init__(self, x, y, size):

        super().__init__(
            x,
            y,
            size,
            (120, 120, 120)
        )