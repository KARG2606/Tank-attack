from enum import Enum


class EnemyState(Enum):

    DEFEND = 1
    ATTACK = 2
    RETREAT = 3

    PATROL = 4
    SEARCH = 5
    AMBUSH = 6
    HOLD = 7