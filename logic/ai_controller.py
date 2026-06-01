import math


# =============================================================================
#  CONSTANTES (deben coincidir con enemy_tank.py)
# =============================================================================

BASE_LEASH_RADIUS = 300
DETECT_RADIUS     = 200
ATTACK_RADIUS     = 130

STATE_PATROL  = "PATROL"
STATE_CHASE   = "CHASE"
STATE_ATTACK  = "ATTACK"
STATE_RETURN  = "RETURN"
STATE_DEFEND  = "DEFEND"
STATE_FLANK   = "FLANK"
STATE_ASSAULT = "ASSAULT"


class AIController:
    """
    Controlador de IA para tanques enemigos.

    Tipos de tanques:
      1 → Defensor lento.  Patrulla su base. Si la pierde, pasa a ASSAULT.
      2 → Defensor rápido. Igual que tipo 1, radio de detección algo mayor.
      3 → Atacante puro.   Siempre persigue al jugador y lo flanquea.

    El método `decide` devuelve un dict:
        { "action": STATE_*, "target": (x, y) | None }

    La asignación inicial de bases se hace llamando a
        AIController.assign_bases(enemies, objectives)
    desde el GameManager al cargar el nivel y al destruirse una base.
    """

    def __init__(self, prolog_manager):
        self.prolog = prolog_manager

    # =========================================================================
    #  ASIGNACIÓN DE BASES
    # =========================================================================

    @staticmethod
    def assign_bases(enemies, objectives):
        """
        Asigna a cada tanque tipo 1/2 la base activa más cercana.
        Si no quedan bases activas, activa base_lost en todos los defensores.
        Los tanques tipo 3 nunca reciben base.
        """
        active_bases = [
            o for o in objectives
            if not getattr(o, "destroyed", False)
        ]

        for enemy in enemies:
            if enemy.tank_type == 3:
                continue

            # Si ya tiene base válida, no cambiar
            if (
                enemy.home_base is not None
                and not getattr(enemy.home_base, "destroyed", False)
            ):
                continue

            if not active_bases:
                # Sin bases: activar modo asalto directamente
                enemy.base_lost = True
                enemy.home_base = None
                continue

            # Asignar la más cercana
            nearest = min(
                active_bases,
                key=lambda o: math.hypot(
                    o.rect.centerx - enemy.rect.centerx,
                    o.rect.centery - enemy.rect.centery
                )
            )
            enemy.assign_base(nearest)
            enemy.base_lost = False   # Asegurarse de limpiar el flag

    # =========================================================================
    #  CONSULTA A PROLOG
    # =========================================================================

    def _query_prolog(self, enemy, player, distance):
        """
        Consulta al motor Prolog para validar/refinar la decisión.

        Hechos dinámicos que se insertan por consulta:
          tank_type(Type)
          distance_to_player(Distance)
          base_destroyed(BaseId, 0|1)

        Se espera que Prolog responda con: recommended_action(Action)
        donde Action es uno de los STATE_* definidos arriba.
        """
        try:
            self.prolog.assertz(f"tank_type({enemy.tank_type})")
            self.prolog.assertz(f"distance_to_player({int(distance)})")

            base_id = id(enemy.home_base) if enemy.home_base else 0
            base_destroyed = (
                1 if getattr(enemy.home_base, "destroyed", False) else 0
            )
            self.prolog.assertz(f"base_destroyed({base_id}, {base_destroyed})")

            result = list(self.prolog.query("recommended_action(Action)"))

            self.prolog.retract(f"tank_type({enemy.tank_type})")
            self.prolog.retract(f"distance_to_player({int(distance)})")
            self.prolog.retract(f"base_destroyed({base_id}, {base_destroyed})")

            if result:
                return result[0].get("Action", None)

        except Exception:
            pass

        return None

    # =========================================================================
    #  LÓGICA TIPO 3  (atacante/flanqueador)
    # =========================================================================

    def _decide_type3(self, enemy, player, distance):
        """
        Tipo 3: siempre ataca.
        - En rango de disparo → FLANK (orbita y dispara)
        - Fuera de rango     → CHASE
        """
        if distance < ATTACK_RADIUS:
            return {
                "action": STATE_FLANK,
                "target": (player.rect.centerx, player.rect.centery)
            }
        return {
            "action": STATE_CHASE,
            "target": (player.rect.centerx, player.rect.centery)
        }

    # =========================================================================
    #  LÓGICA TIPOS 1 y 2  (defensores)
    # =========================================================================

    def _decide_defender(self, enemy, player, distance):
        """
        Prioridades en orden:

        1. base_lost == True  → ASSAULT  (perseguir al jugador sin límite)
        2. En rango de ataque → ATTACK
        3. Jugador detectado y dentro del leash → CHASE
        4. Leash superado → RETURN a la base
        5. Jugador rondando la base → DEFEND (patrulla corta)
        6. Normal → PATROL
        """

        # ------------------------------------------------------------------
        # 1. Comprobar si la base fue destruida.
        #    Casos:
        #      a) home_base es None y base_lost ya estaba en True
        #         (seteado por assign_bases cuando no quedan bases)
        #      b) home_base existe pero tiene destroyed == True
        # ------------------------------------------------------------------
        if enemy.base_lost:
            return {
                "action": STATE_ASSAULT,
                "target": (player.rect.centerx, player.rect.centery)
            }

        if enemy.home_base is not None and getattr(
            enemy.home_base, "destroyed", False
        ):
            enemy.base_lost = True
            enemy.home_base = None
            return {
                "action": STATE_ASSAULT,
                "target": (player.rect.centerx, player.rect.centery)
            }

        # ------------------------------------------------------------------
        # 2. Ataque directo
        # ------------------------------------------------------------------
        if distance < ATTACK_RADIUS:
            return {
                "action": STATE_ATTACK,
                "target": (player.rect.centerx, player.rect.centery)
            }

        dist_to_base = enemy.distance_to_base()

        # ------------------------------------------------------------------
        # 3. Perseguir: jugador detectado y tanque dentro del leash
        # ------------------------------------------------------------------
        if distance < DETECT_RADIUS and dist_to_base < BASE_LEASH_RADIUS:
            return {
                "action": STATE_CHASE,
                "target": (player.rect.centerx, player.rect.centery)
            }

        # ------------------------------------------------------------------
        # 4. Regresar a la base si se alejó demasiado
        # ------------------------------------------------------------------
        if dist_to_base > BASE_LEASH_RADIUS:
            bx = enemy.home_base.rect.centerx
            by = enemy.home_base.rect.centery
            return {
                "action": STATE_RETURN,
                "target": (bx, by)
            }

        # ------------------------------------------------------------------
        # 5. Defender: el jugador está rondando la base
        # ------------------------------------------------------------------
        dist_player_to_base = math.hypot(
            player.rect.centerx - enemy.home_base.rect.centerx,
            player.rect.centery - enemy.home_base.rect.centery
        )
        if dist_player_to_base < BASE_LEASH_RADIUS:
            return {
                "action": STATE_DEFEND,
                "target": (
                    enemy.home_base.rect.centerx,
                    enemy.home_base.rect.centery
                )
            }

        # ------------------------------------------------------------------
        # 6. Patrulla normal
        # ------------------------------------------------------------------
        return {
            "action": STATE_PATROL,
            "target": enemy.patrol_target
        }

    # =========================================================================
    #  PUNTO DE ENTRADA PRINCIPAL
    # =========================================================================

    def decide(self, enemy, player, objectives, walls):
        """
        Decide la acción del tanque para este frame.

        Parámetros:
            enemy      : EnemyTank
            player     : PlayerTank
            objectives : lista de bases/objetivos del mapa
            walls      : lista de paredes (no usado aquí, pero disponible)

        Retorna:
            dict { "action": STATE_*, "target": (x, y) | None }
        """
        distance = enemy.distance_to_player(player)

        # --- Consulta opcional a Prolog (tiene prioridad si responde) ---
        prolog_action = self._query_prolog(enemy, player, distance)
        if prolog_action in (
            STATE_PATROL, STATE_CHASE, STATE_ATTACK,
            STATE_RETURN, STATE_DEFEND, STATE_FLANK, STATE_ASSAULT
        ):
            return {
                "action": prolog_action,
                "target": (player.rect.centerx, player.rect.centery)
            }

        # --- Tipo 3: atacante puro ---
        if enemy.tank_type == 3:
            return self._decide_type3(enemy, player, distance)

        # --- Tipos 1 y 2: defensores ---
        # Guardia: si base_lost no está activo pero la base fue destruida,
        # assign_bases ya debería haberlo manejado; si no, corregir aquí.
        if (
            not enemy.base_lost
            and enemy.home_base is None
            and enemy.tank_type in (1, 2)
        ):
            new_base = enemy.nearest_base(objectives)
            if new_base:
                enemy.assign_base(new_base)
            else:
                # No quedan bases → asalto
                enemy.base_lost = True

        return self._decide_defender(enemy, player, distance)
