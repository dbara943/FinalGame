import pygame
import random
import math
import time
import os

class Ship:
    """Statek desantowy: przyplywa na kazda fale (losowo z lewej/prawej),
    cumuje w porcie, desantuje wrogow i odplywa."""

    IN, DOCKED, OUT, AWAY = "in", "docked", "out", "away"

    def __init__(self, img_path, dock_x, dock_y, screen_w=1124):
        self.base_img = pygame.image.load(img_path)
        self.dock_x = dock_x
        self.dock_y = dock_y
        self.screen_w = screen_w
        self.x = dock_x
        self.y = dock_y
        self.state = Ship.AWAY
        self.speed = 3.5
        self.img = self.base_img
        self.from_left = True
        self._t0 = time.time()
        # Armaty
        self.cannon_cooldown = 0
        self.cannon_flash = 0  # timer blysku przy strzale

    def sail_in(self):
        """Rozpoczyna przyplyniecie - losowo z lewej albo z prawej."""
        self.from_left = random.choice([True, False])
        w = self.base_img.get_width()
        if self.from_left:
            self.x = -w // 2
            # sprite bazowy patrzy w lewo -> odwracamy do kierunku ruchu
            self.img = pygame.transform.flip(self.base_img, True, False)
        else:
            self.x = self.screen_w + w // 2
            self.img = self.base_img
        self.y = self.dock_y
        self.state = Ship.IN

    def sail_out(self):
        if self.state == Ship.DOCKED:
            self.state = Ship.OUT

    def update(self):
        if self.state == Ship.IN:
            step = self.speed if self.dock_x > self.x else -self.speed
            if abs(self.dock_x - self.x) <= self.speed:
                self.x = self.dock_x
                self.state = Ship.DOCKED
            else:
                self.x += step
        elif self.state == Ship.OUT:
            # Statek plynie przodem w kierunku ruchu (wczesniej plynal tylem)
            if self.from_left:
                # Plynie w lewo - sprite bazowy patrzy w lewo
                self.img = self.base_img
                step = -self.speed
            else:
                # Plynie w prawo - odwrocony sprite
                self.img = pygame.transform.flip(self.base_img, True, False)
                step = self.speed
            self.x += step
            w = self.base_img.get_width()
            if self.x < -w or self.x > self.screen_w + w:
                self.state = Ship.AWAY

    def draw(self, win):
        if self.state == Ship.AWAY:
            return
        # Delikatne kolysanie na falach
        bob = math.sin((time.time() - self._t0) * 2.0) * 4
        win.blit(self.img, (self.x - self.img.get_width() // 2,
                            self.y - self.img.get_height() // 2 + bob))
        # Blysk armat przy strzale
        if self.cannon_flash > 0:
            self.cannon_flash -= 1
            flash_size = self.cannon_flash * 2
            fx = self.x + (30 if self.from_left else -30)
            fy = self.y - 20 + bob
            pygame.draw.circle(win, (255, 200, 100, 200), (int(fx), int(fy)), flash_size)
            pygame.draw.circle(win, (255, 255, 200, 150), (int(fx), int(fy)), flash_size // 2)
