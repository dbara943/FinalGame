import pygame
import random
import math
import os

_coin_img = None

def _get_coin_img():
    """Grafika zlotej monety (ladowana raz, leniwie - modul importowany
    przed ustawieniem trybu wideo w niektorych testach)."""
    global _coin_img
    if _coin_img is None:
        try:
            _coin_img = pygame.image.load(os.path.join("images", "coin.png")).convert_alpha()
        except Exception:
            _coin_img = False  # brak pliku -> proceduralny fallback w draw()
    return _coin_img or None

class ParticleSystem:
    """Prosty system czasteczek do eksplozji, iskier, kurzu itd."""
    MAX_PARTICLES = 400  # limit chroniacy przed spadkami FPS przy masakrze
    def __init__(self):
        self.particles = []  # [x, y, vx, vy, life, max_life, color, size, gravity]
        self._circle_cache = {}  # cache sprite'ow (size, alpha) - wydajnosc

    def burst(self, x, y, color, count=12, speed=3, life=30, size=4, gravity=0.1):
        # Nie przekraczaj limitu - odrzucaj nadwyzke zamiast lagowac
        allowed = self.MAX_PARTICLES - len(self.particles)
        if allowed <= 0:
            return
        for _ in range(min(count, allowed)):
            ang = random.uniform(0, math.pi * 2)
            sp = random.uniform(speed * 0.3, speed)
            self.particles.append([
                x, y,
                math.cos(ang) * sp, math.sin(ang) * sp,
                life, life, color, random.randint(size//2, size), gravity
            ])

    def update(self):
        # Iteracja od konca (bez kopiowania listy)
        for i in range(len(self.particles) - 1, -1, -1):
            p = self.particles[i]
            p[0] += p[2]
            p[1] += p[3]
            p[3] += p[8]  # gravity
            p[4] -= 1
            if p[4] <= 0:
                del self.particles[i]

    def draw(self, win):
        # Cache kolistych sprite'ow (rozmiar + poziom alfy) - brak alokacji co klatke
        for x, y, vx, vy, life, max_life, color, size, grav in self.particles:
            alpha_bucket = int(15 * life / max_life)  # 16 poziomow
            key = (size, alpha_bucket)
            s = self._circle_cache.get(key)
            if s is None:
                s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                a = int(255 * alpha_bucket / 15)
                c = (*color[:3], a)
                pygame.draw.circle(s, c, (size, size), size)
                self._circle_cache[key] = s
                # Ogranicz rozmiar cache
                if len(self._circle_cache) > 64:
                    self._circle_cache.clear()
            win.blit(s, (x - size, y - size))

class FloatingCoin:
    """Zlota moneta lecaca do HUD po zabiciu (obrot jak wirujaca moneta)."""
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
        img = _get_coin_img()
        size = 26
        if img is not None:
            # Wirowanie: szerokosc pulsuje jak obracajaca sie moneta (3 pelne obroty)
            squash = 0.25 + 0.75 * abs(math.sin(p * math.pi * 3))
            wpx = max(4, int(size * squash))
            coin = pygame.transform.smoothscale(img, (wpx, size))
        else:
            # Fallback proceduralny: zlote kolko z obramowaniem
            coin = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(coin, (255, 200, 60), (size // 2, size // 2), size // 2)
            pygame.draw.circle(coin, (190, 140, 30), (size // 2, size // 2), size // 2, 2)
        win.blit(coin, (int(x) - coin.get_width() // 2, int(y) - coin.get_height() // 2))

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
