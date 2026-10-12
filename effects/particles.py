import pygame
import random
import math

class ParticleSystem:
    """Prosty system czasteczek do eksplozji, iskier, kurzu itd."""
    def __init__(self):
        self.particles = []  # [x, y, vx, vy, life, max_life, color, size, gravity]

    def burst(self, x, y, color, count=12, speed=3, life=30, size=4, gravity=0.1):
        for _ in range(count):
            ang = random.uniform(0, math.pi * 2)
            sp = random.uniform(speed * 0.3, speed)
            self.particles.append([
                x, y,
                math.cos(ang) * sp, math.sin(ang) * sp,
                life, life, color, random.randint(size//2, size), gravity
            ])

    def update(self):
        for p in self.particles[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += p[8]  # gravity
            p[4] -= 1
            if p[4] <= 0:
                self.particles.remove(p)

    def draw(self, win):
        for x, y, vx, vy, life, max_life, color, size, grav in self.particles:
            alpha = int(255 * life / max_life)
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            c = (*color[:3], alpha) if len(color) == 3 else (*color[:3], alpha)
            pygame.draw.circle(s, c, (size, size), size)
            win.blit(s, (x - size, y - size))

class FloatingCoin:
    """Banknot dolarowy lecacy do HUD po zabiciu."""
    def __init__(self, x, y, target_x, target_y, amount):
        self.x, self.y = x, y
        self.tx, self.ty = target_x, target_y
        self.amount = amount
        self.t = 0
        self.duration = 40
        self.sx, self.sy = x, y

    def update(self):
        self.t += 1
        return self.t >= self.duration

    def draw(self, win):
        p = self.t / self.duration
        # Krzywa: w gore potem do celu
        x = self.sx + (self.tx - self.sx) * p
        y = self.sy + (self.ty - self.sy) * p - math.sin(p * math.pi) * 60
        # Banknot dolarowy (obrocony lekko w locie)
        w, h = 22, 12
        bill = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(bill, (85, 160, 85), bill.get_rect(), border_radius=2)
        pygame.draw.rect(bill, (45, 110, 45), bill.get_rect(), 2, border_radius=2)
        pygame.draw.circle(bill, (200, 230, 200), (w // 2, h // 2), 4)
        pygame.draw.circle(bill, (45, 110, 45), (w // 2, h // 2), 4, 1)
        ang = 25 * math.sin(p * math.pi * 2)
        bill = pygame.transform.rotate(bill, ang)
        win.blit(bill, (int(x) - bill.get_width() // 2, int(y) - bill.get_height() // 2))

class Shockwave:
    """Rozchodzacy sie krag."""
    def __init__(self, x, y, max_r=80, color=(255, 200, 100), life=25):
        self.x, self.y = x, y
        self.max_r = max_r
        self.color = color
        self.life = life
        self.max_life = life

    def update(self):
        self.life -= 1
        return self.life <= 0

    def draw(self, win):
        p = 1 - self.life / self.max_life
        r = int(self.max_r * p)
        alpha = int(200 * (1 - p))
        if r > 0:
            s = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (r+2, r+2), r, 3)
            win.blit(s, (self.x - r - 2, self.y - r - 2))
