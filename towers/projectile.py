import pygame
import math

class Projectile:
    """Lecacy pocisk z wiezy do wroga. Kazda wieza ma wlasny wyglad."""

    def __init__(self, x, y, img, target, damage, speed=9, splash_radius=0, slow_on_hit=False, damage_type="physical", source_tower=None, special=None):
        self.x = x
        self.y = y
        self.img = img
        self.target = target
        self.damage = damage
        self.speed = speed
        self.splash_radius = splash_radius
        self.slow_on_hit = slow_on_hit
        self.damage_type = damage_type
        self.source_tower = source_tower  # R5: wieza ktora wystrzelila
        self.special = special  # Nazwa efektu specjalnego (frost_nova, meteor, itd.)
        self.done = False
        self.trail = []  # Smuga za pociskiem specjalnym

    @staticmethod
    def make_special_img(color, size=32, glow=True):
        """Tworzy charakterystyczny pocisk specjalny (swiecaca kula)."""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        if glow:
            # Zewnetrzna poswiata
            for r, alpha in [(c, 60), (int(c*0.7), 120), (int(c*0.45), 255)]:
                pygame.draw.circle(surf, (*color, alpha), (c, c), r)
        else:
            pygame.draw.circle(surf, (*color, 255), (c, c), c // 2)
        # Jasny srodek
        pygame.draw.circle(surf, (255, 255, 255, 230), (c, c), size // 6)
        return surf

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
        # Smuga za pociskiem specjalnym
        if self.special:
            self.trail.append((self.x, self.y))
            if len(self.trail) > 8:
                self.trail.pop(0)
        return None

    def draw(self, win):
        # Smuga
        if self.special and self.trail:
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(100 * (i + 1) / len(self.trail))
                size = 6 + i
                s = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 255, 255, alpha), (size//2, size//2), size//2)
                win.blit(s, (tx - size//2, ty - size//2))
        # Obrot w strone celu.
        angle = math.degrees(math.atan2(-(self.target.y - self.y),
                                        self.target.x - self.x))
        rotated = pygame.transform.rotate(self.img, angle)
        win.blit(rotated,
                 (self.x - rotated.get_width() // 2,
                  self.y - rotated.get_height() // 2))
