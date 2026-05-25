import random


class TacticalManager:

    def __init__(self):

        # =========================
        # MEMORIA COMPARTIDA
        # =========================

        self.last_known_player_position = None

        # Cada cuánto actualiza inteligencia global
        self.update_interval = 120  # 2 segundos a 60 FPS
        self.update_timer = 0

        # =========================
        # OFFSETS TÁCTICOS
        # =========================

        self.attack_offsets = [
            (0, 0),      # directo
            (-3, 0),     # izquierda
            (3, 0),      # derecha
            (0, -3),     # arriba
            (0, 3)       # abajo
        ]

    # =========================
    # ACTUALIZAR MEMORIA GLOBAL
    # =========================

    def update(self, player):

        self.update_timer -= 1

        if self.update_timer <= 0:

            # =========================
            # GUARDAR ÚLTIMA POSICIÓN
            # =========================

            self.last_known_player_position = (
                player.rect.centerx,
                player.rect.centery
            )

            self.update_timer = self.update_interval

    # =========================
    # ASIGNAR TARGET TÁCTICO
    # =========================

    def get_tactical_target(
        self,
        enemy,
        enemies,
        tile_size
    ):

        # =========================
        # SI NO HAY MEMORIA
        # =========================

        if self.last_known_player_position is None:

            return None

        # =========================
        # FILTRAR MISMO TIPO
        # =========================

        same_type_enemies = [

            e for e in enemies

            if e.enemy_type == enemy.enemy_type
        ]

        # =========================
        # ORDEN FIJO
        # =========================

        same_type_enemies.sort(
            key=lambda e: (e.rect.x, e.rect.y)
        )

        # =========================
        # ÍNDICE DEL TANQUE
        # =========================

        try:
            index = same_type_enemies.index(enemy)

        except ValueError:
            index = 0

        # =========================
        # OFFSET TÁCTICO
        # =========================

        offset = self.attack_offsets[
            index % len(self.attack_offsets)
        ]

        px, py = self.last_known_player_position

        target_x = px + (offset[0] * tile_size)
        target_y = py + (offset[1] * tile_size)

        return target_x, target_y

    # =========================
    # GENERAR PUNTO PATRULLA
    # =========================

    def generate_patrol_point(self, enemy):

        patrol_x = (
            enemy.rect.centerx
            + random.randint(-120, 120)
        )

        patrol_y = (
            enemy.rect.centery
            + random.randint(-120, 120)
        )

        return patrol_x, patrol_y