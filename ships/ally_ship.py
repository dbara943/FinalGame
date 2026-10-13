"""Sojuszniczy statek (Call the Cavalry): wplywa ZAWSZE z lewej, wyplywa w prawo.
Najpierw unieszkodliwia piracki statek, potem (50%/fale) ostrzeliwuje wrogow
pociskami mozdzierzowymi."""
import pygame
import math
import random
import time


class AllyShip:
    AWAY, IN, FIRING, OUT = "away", "in", "firing", "out"

    def __init__(self, img_path, screen_w=1124):
        self.base_img = pygame.image.load(img_path)
        self.screen_w = screen_w
        self.x = -200
        self.y = 620  # na wodzie
        self.fire_x = 420  # pozycja ostrzalu
        self.state = AllyShip.AWAY
        self.speed = 4.0
        self._t0 = time.time()
        self.cannon_flash = 0
        self.mode = None  # "cripple" lub "strike"

    def sail_in(self, mode, fire_x=420):
        """Wplywa z lewej. mode: 'cripple' (atak na pirata) lub 'strike' (wrogowie)."""
        self.mode = mode
        self.fire_x = fire_x
        w = self.base_img.get_width()
        self.x = -w // 2
        self.state = AllyShip.IN

    def sail_out(self):
        if self.state in (AllyShip.IN, AllyShip.FIRING):
            self.state = AllyShip.OUT

    def update(self):
        if self.cannon_flash > 0:
            self.cannon_flash -= 1
        if self.state == AllyShip.IN:
            self.x += self.speed
            if self.x >= self.fire_x:
                self.x = self.fire_x
                self.state = AllyShip.FIRING
        elif self.state == AllyShip.OUT:
            self.x += self.speed
            if self.x > self.screen_w + 200:
                self.state = AllyShip.AWAY
                self.mode = None

    def draw(self, win):
        if self.state == AllyShip.AWAY:
            return
        t = time.time() - self._t0
        bob = math.sin(t * 2.0) * 6
        rot = math.sin(t * 1.5) * 1.5
        img = pygame.transform.rotate(self.base_img, rot)
        win.blit(img, (self.x - img.get_width() // 2,
                       self.y - img.get_height() // 2 + bob))
        # Kilwater gdy plynie
        if self.state in (AllyShip.IN, AllyShip.OUT):
            wake = pygame.Surface((120, 20), pygame.SRCALPHA)
            for i in range(3):
                alpha = max(0, 70 - i * 22)
                pygame.draw.ellipse(wake, (255, 255, 255, alpha),
                                    (i * 30, 5 + i * 2, 60 - i * 15, 10 - i * 2))
            win.blit(wake, (self.x - 60 - 60, self.y + 20 + bob))
        # Blysk armat przy strzale
        if self.cannon_flash > 0:
            fx = self.x + 80
            fy = self.y - 20 + bob
            r = self.cannon_flash * 2
            flash = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(flash, (255, 200, 80, 180), (r, r), r)
            pygame.draw.circle(flash, (255, 255, 200, 220), (r, r), r // 2)
            win.blit(flash, (fx - r, fy - r))
