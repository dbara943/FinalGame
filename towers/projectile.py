import pygame
import math

class Projectile:
    """Lecacy pocisk z wiezy do wroga. Kazda wieza ma wlasny wyglad."""

    def __init__(self, x, y, img, target, damage, speed=9, splash_radius=0, slow_on_hit=False):
        self.x = x
        self.y = y
        self.img = img
        self.target = target
        self.damage = damage
        self.speed = speed
        self.splash_radius = splash_radius
        self.slow_on_hit = slow_on_hit
        self.done = False

    def move(self):
        # Cel zniknal (dotarl do bazy, umiera) -> pocisk gasnie.
        if self.target.reached_end or self.target.dying or self.target.dead:
            self.done = True
            return None
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist < 22:
            self.done = True
            return self.target
        self.x += dx / dist * self.speed
        self.y += dy / dist * self.speed
        return None

    def draw(self, win):
        # Obrot w strone celu.
        angle = math.degrees(math.atan2(-(self.target.y - self.y),
                                        self.target.x - self.x))
        rotated = pygame.transform.rotate(self.img, angle)
        win.blit(rotated,
                 (self.x - rotated.get_width() // 2,
                  self.y - rotated.get_height() // 2))
