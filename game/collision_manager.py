class CollisionManager:

    @staticmethod
    def check_wall_collision(rect, walls):

        for wall in walls:

            if rect.colliderect(wall.rect):
                return True

        return False