"""
Editor mínimo de pantallas para Tank-Attack.

Uso:
    python3 -m ui.editor_pantallas [archivo.txt]

Si no se pasa archivo, se crea un mapa nuevo de 40x22 vacío con muros
en el borde. El archivo se guarda en la ruta original o, si no había,
en maps/mapa_nuevo.txt.

Controles:
    Clic izquierdo : cicla el contenido de la celda
                     (. -> # -> P -> O -> Q -> 1 -> 2 -> 3 -> .)
    Clic derecho   : pone la celda vacía (.)
    S              : guarda (si el mapa es válido)
    R              : recarga desde disco
    V              : valida y muestra los errores en consola
    ESC            : salir
"""

import os
import sys

import pygame

from util.generador_aleatorio import GeneradorAleatorio


VALID_CHARS = {".", "#", "P", "O", "Q", "1", "2", "3"}

CYCLE = [".", "#", "P", "O", "Q", "1", "2", "3"]

COLORS = {
    ".": (40, 40, 40),
    "#": (120, 120, 120),
    "P": (0, 200, 0),
    "O": (240, 220, 0),
    "Q": (240, 90, 200),
    "1": (200, 0, 0),
    "2": (0, 120, 255),
    "3": (255, 120, 0),
}

DEFAULT_COLS = 40
DEFAULT_ROWS = 22
CELL_PIXELS = 24

PALETTE_HEIGHT = 60
STATUS_HEIGHT = 36


class MapEditor:

    def __init__(self, path=None):

        self._path = path
        self._grid = self._load_or_create(path)

        self._rows = len(self._grid)
        self._cols = len(self._grid[0]) if self._grid else DEFAULT_COLS

        self._status = "Listo. Editar con clic izquierdo. S para guardar."
        self._status_color = (220, 220, 220)

        width = self._cols * CELL_PIXELS
        height = (
            PALETTE_HEIGHT
            + self._rows * CELL_PIXELS
            + STATUS_HEIGHT
        )

        pygame.init()
        self._screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(
            f"Editor — {self._path or 'mapa nuevo'}"
        )

        self._font = pygame.font.SysFont("Arial", 16, bold=True)
        self._cell_font = pygame.font.SysFont("Arial", 14, bold=True)

        self._clock = pygame.time.Clock()
        self._running = True

    def _load_or_create(self, path):
        if path and os.path.isfile(path):
            with open(path, "r") as f:
                lines = [line.rstrip("\n") for line in f.readlines()]
            return [list(line) for line in lines if line]

        # Mapa vacío con borde de muro y P al centro.
        grid = []
        for r in range(DEFAULT_ROWS):
            row = []
            for c in range(DEFAULT_COLS):
                if (
                    r == 0
                    or r == DEFAULT_ROWS - 1
                    or c == 0
                    or c == DEFAULT_COLS - 1
                ):
                    row.append("#")
                else:
                    row.append(".")
            grid.append(row)
        grid[DEFAULT_ROWS // 2][DEFAULT_COLS // 2] = "P"
        return grid

    def run(self):
        while self._running:
            self._clock.tick(60)
            self._handle_events()
            self._draw()
        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self._running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    self._running = False

                elif event.key == pygame.K_s:
                    self._save()

                elif event.key == pygame.K_r:
                    self._grid = self._load_or_create(self._path)
                    self._status = "Recargado desde disco."
                    self._status_color = (220, 220, 220)

                elif event.key == pygame.K_v:
                    errors = self._validate()
                    if errors:
                        print("Errores de validación:")
                        for e in errors:
                            print(f"  - {e}")
                        self._status = (
                            f"{len(errors)} error(es). Ver consola."
                        )
                        self._status_color = (255, 120, 120)
                    else:
                        print("Mapa válido.")
                        self._status = "Mapa válido."
                        self._status_color = (120, 255, 120)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                cell = self._mouse_to_cell(event.pos)
                if cell is None:
                    continue
                col, row = cell

                if event.button == 1:
                    current = self._grid[row][col]
                    idx = CYCLE.index(current) if current in CYCLE else 0
                    new_char = CYCLE[(idx + 1) % len(CYCLE)]
                    self._grid[row][col] = new_char

                elif event.button == 3:
                    self._grid[row][col] = "."

    def _mouse_to_cell(self, pos):
        mx, my = pos
        if my < PALETTE_HEIGHT:
            return None
        if my >= PALETTE_HEIGHT + self._rows * CELL_PIXELS:
            return None
        col = mx // CELL_PIXELS
        row = (my - PALETTE_HEIGHT) // CELL_PIXELS
        if 0 <= col < self._cols and 0 <= row < self._rows:
            return (col, row)
        return None

    def _draw(self):
        self._screen.fill((20, 20, 20))

        # Paleta arriba.
        x = 12
        for ch in CYCLE:
            color = COLORS[ch]
            pygame.draw.rect(
                self._screen, color,
                pygame.Rect(x, 16, 32, 32),
                border_radius=4,
            )
            label = self._cell_font.render(ch, True, (0, 0, 0))
            label_rect = label.get_rect(center=(x + 16, 16 + 16))
            self._screen.blit(label, label_rect)
            x += 44

        leyenda = self._font.render(
            "Paleta:  . vacío  # muro  P jugador  O obj1  Q obj2  1/2/3 enemigos",
            True,
            (200, 200, 200),
        )
        self._screen.blit(leyenda, (x + 16, 22))

        # Grid.
        for r in range(self._rows):
            for c in range(self._cols):
                ch = self._grid[r][c]
                color = COLORS.get(ch, (40, 40, 40))
                rect = pygame.Rect(
                    c * CELL_PIXELS,
                    PALETTE_HEIGHT + r * CELL_PIXELS,
                    CELL_PIXELS,
                    CELL_PIXELS,
                )
                pygame.draw.rect(self._screen, color, rect)
                pygame.draw.rect(
                    self._screen, (10, 10, 10), rect, width=1
                )

        # Barra de estado.
        status_y = PALETTE_HEIGHT + self._rows * CELL_PIXELS
        pygame.draw.rect(
            self._screen,
            (0, 0, 0),
            pygame.Rect(
                0, status_y, self._cols * CELL_PIXELS, STATUS_HEIGHT
            ),
        )
        status_text = self._font.render(
            self._status, True, self._status_color
        )
        self._screen.blit(status_text, (12, status_y + 8))

        pygame.display.flip()

    def _validate(self):
        errors = []

        if not self._grid:
            errors.append("El mapa está vacío.")
            return errors

        cols = len(self._grid[0])
        for i, row in enumerate(self._grid):
            if len(row) != cols:
                errors.append(
                    f"Fila {i + 1} tiene {len(row)} columnas (esperaba {cols})."
                )

        player_count = 0
        for r, row in enumerate(self._grid):
            for c, ch in enumerate(row):
                if ch not in VALID_CHARS:
                    errors.append(
                        f"Carácter inválido {ch!r} en fila {r + 1}, columna {c + 1}."
                    )
                if ch == "P":
                    player_count += 1

        if player_count == 0:
            errors.append("Falta posición del jugador (P).")
        elif player_count > 1:
            errors.append(
                f"Hay {player_count} jugadores; debe haber exactamente uno."
            )

        objetivos = sum(
            row.count("O") + row.count("Q") for row in self._grid
        )
        if objetivos == 0:
            errors.append(
                "No hay objetivos (O o Q). El nivel sería invencible."
            )

        # Alcanzabilidad: ¿el jugador puede llegar a todas las celdas no muro?
        if player_count == 1 and not errors:
            unreachable = self._unreachable_open_cells()
            if unreachable:
                errors.append(
                    f"Hay {len(unreachable)} celdas no muro aisladas "
                    "del jugador. Conecta esas zonas con pasillos."
                )

        return errors

    def _unreachable_open_cells(self):
        rows = len(self._grid)
        cols = len(self._grid[0])
        walls = set()
        start = None
        for r in range(rows):
            for c in range(cols):
                ch = self._grid[r][c]
                if ch == "#":
                    walls.add((c, r))
                elif ch == "P":
                    start = (c, r)
        if start is None:
            return []
        reachable = GeneradorAleatorio._bfs_reachable(
            start, walls, cols, rows
        )
        unreachable = []
        for r in range(rows):
            for c in range(cols):
                if self._grid[r][c] == "#":
                    continue
                if (c, r) not in reachable:
                    unreachable.append((c, r))
        return unreachable

    def _save(self):
        errors = self._validate()
        if errors:
            print("No se guarda. Errores:")
            for e in errors:
                print(f"  - {e}")
            self._status = (
                f"No guardado: {len(errors)} error(es). Ver consola."
            )
            self._status_color = (255, 120, 120)
            return

        path = self._path or "maps/mapa_nuevo.txt"
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            for row in self._grid:
                f.write("".join(row) + "\n")

        self._path = path
        pygame.display.set_caption(f"Editor — {path}")
        self._status = f"Guardado en {path}"
        self._status_color = (120, 255, 120)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    editor = MapEditor(path)
    editor.run()


if __name__ == "__main__":
    main()
