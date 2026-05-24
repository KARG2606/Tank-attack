from game.constants import TILE_SIZE

from entities.wall import Wall
from entities.player_tank import PlayerTank
from entities.enemy_tank import EnemyTank
from entities.objective import Objective


class LevelLoader:

    def __init__(self):

        self.walls = []

        self.enemies = []

        self.objectives = []

        self.player = None

        self.map_width = 0

        self.map_height = 0

    def load_level(self, path):

        with open(path, "r") as file:

            lines = file.readlines()

            self.map_height = len(lines)

            self.map_width = len(lines[0].strip())

        for row, line in enumerate(lines):

            for col, char in enumerate(line.strip()):

                x = col * TILE_SIZE
                y = row * TILE_SIZE

                if char == "#":

                    self.walls.append(
                        Wall(x, y, TILE_SIZE)
                    )

                elif char == "P":

                    self.player = PlayerTank(
                        x,
                        y,
                        TILE_SIZE
                    )

                elif char in ["1", "2", "3"]:

                    self.enemies.append(
                        EnemyTank(
                            x,
                            y,
                            TILE_SIZE,
                            enemy_type=int(char)
                        )
                    )

                elif char == "O":

                    self.objectives.append(
                        Objective(
                            x,
                            y,
                            TILE_SIZE
                        )
                    )