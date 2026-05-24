from entities.entity import Entity


class Objective(Entity):

    def __init__(self, x, y, size):

        super().__init__(
            x,
            y,
            size,
            (240, 220, 0)
        )