import random


class AIController:

    def __init__(self, prolog_manager):
        self.prolog = prolog_manager

    # =========================
    # DECISION PRINCIPAL
    # =========================
    def decide(self, enemy, player, objectives, walls):

        distance = enemy.distance_to_player(player)

        # =========================
        # ATAQUE
        # =========================
        if distance < 120:
            return "ATTACK", player.rect.centerx, player.rect.centery

        # =========================
        # DEFENSA OBJETIVO
        # =========================
        if enemy.target_objective:
            obj = enemy.target_objective
            return "DEFEND", obj.rect.centerx, obj.rect.centery

        # =========================
        # PATRULLA (NUEVO)
        # =========================
        if enemy.patrol_target is None:
            enemy.generate_patrol_point()
        
        patrol_x, patrol_y = enemy.patrol_target

        return "PATROL", patrol_x, patrol_y