from entities.entity import Entity


class Objective(Entity):

    def __init__(self, x, y, size, color, tipo):

        super().__init__(x, y, size, color)

        self._tipo = tipo

    @property
    def tipo(self):
        return self._tipo


class ObjetivoTipo1(Objective):

    def __init__(self, x, y, size):

        super().__init__(
            x,
            y,
            size,
            (240, 220, 0),
            tipo=1
        )


class ObjetivoTipo2(Objective):

    def __init__(self, x, y, size):

        super().__init__(
            x,
            y,
            size,
            (240, 90, 200),
            tipo=2
        )
