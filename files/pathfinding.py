from collections import deque


class Pathfinding:

    def __init__(self):
        pass

    # =========================
    # BFS
    # =========================

    def find_path(
        self,
        start,
        goal,
        walls,
        map_width,
        map_height
    ):

        queue = deque()

        queue.append((start, [start]))

        visited = set()

        visited.add(start)

        while queue:

            current, path = queue.popleft()

            if current == goal:
                return path

            x, y = current

            neighbors = [
                (x + 1, y),
                (x - 1, y),
                (x, y + 1),
                (x, y - 1)
            ]

            for nx, ny in neighbors:

                # límites
                if not (
                    0 <= nx < map_width
                    and 0 <= ny < map_height
                ):
                    continue

                # muros
                if (nx, ny) in walls:
                    continue

                # visitados
                if (nx, ny) in visited:
                    continue

                visited.add((nx, ny))

                queue.append(
                    (
                        (nx, ny),
                        path + [(nx, ny)]
                    )
                )

        return []