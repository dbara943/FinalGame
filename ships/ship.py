import pygame
import random
import math
import time
import os

class Ship:
    """Statek desantowy: przyplywa na kazda fale (losowo z lewej/prawej),
    cumuje w porcie, desantuje wrogow i odplywa."""

    IN, DOCKED, OUT, AWAY, BOMBARD_SAIL, BOMBARD = "in", "docked", "out", "away", "bombard_sail", "bombard"

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
            # sprite bazowy patrzy w prawo = kierunek ruchu, bez flipa
            self.img = self.base_img
        else:
            self.x = self.screen_w + w // 2
            # plynie w lewo, odwracamy
            self.img = pygame.transform.flip(self.base_img, True, False)
        self.y = self.dock_y
        self.state = Ship.IN
        # Piracki fanfar przy wplynieciu
        try:
            snd = pygame.mixer.Sound(os.path.join("sounds", "music_pirate.wav"))
            snd.play()
        except:
            pass

    def sail_out(self):
        if self.state == Ship.DOCKED:
            self.state = Ship.OUT

    def sail_to_bombard(self, tx, ty):
        """Plynie na srodek oceanu przed bombardowaniem."""
        self.bombard_tx = tx
        self.bombard_ty = ty
        self.state = Ship.BOMBARD_SAIL

    def sail_out_from_bombard(self):
        """Odplywa poza mape po bombardowaniu."""
        # Plynie w strone z ktorej przypłynął
        self.state = Ship.OUT
        # Ustaw from_left tak zeby odplynal poza ekran
        if self.x < self.screen_w // 2:
            self.from_left = True  # odplynie w lewo
        else:
            self.from_left = False  # odplynie w prawo

    def update(self):
        if self.state == Ship.IN:
            step = self.speed if self.dock_x > self.x else -self.speed
            if abs(self.dock_x - self.x) <= self.speed:
                self.x = self.dock_x
                self.state = Ship.DOCKED
            else:
                self.x += step
        elif self.state == Ship.BOMBARD_SAIL:
            # Plynie do punktu bombardowania (srodek oceanu)
            dx = self.bombard_tx - self.x
            dy = self.bombard_ty - self.y
            dist = max(1, (dx*dx + dy*dy) ** 0.5)
            step = self.speed * 1.5  # szybciej niz normalnie
            if dist <= step:
                self.x = self.bombard_tx
                self.y = self.bombard_ty
                self.state = Ship.BOMBARD
            else:
                self.x += dx / dist * step
                self.y += dy / dist * step
                # Obróc sprite w kierunku ruchu
                if dx > 0:
                    self.img = self.base_img  # w prawo
                else:
                    self.img = pygame.transform.flip(self.base_img, True, False)  # w lewo
        elif self.state == Ship.BOMBARD:
            # Stoi w miejscu, gotowy do strzalu
            pass
        elif self.state == Ship.OUT:
            # Statek plynie przodem w kierunku ruchu
            if self.from_left:
                # Wraca w lewo - odwrocony sprite (bazowy patrzy w prawo)
                self.img = pygame.transform.flip(self.base_img, True, False)
                step = -self.speed
            else:
                # Wraca w prawo - bazowy sprite
                self.img = self.base_img
                step = self.speed
            self.x += step
            w = self.base_img.get_width()
            if self.x < -w or self.x > self.screen_w + w:
                self.state = Ship.AWAY

    def draw(self, win):
        if self.state == Ship.AWAY:
            return
        # Zywsze kolysanie na falach + rotacja
        t = time.time() - self._t0
        bob = math.sin(t * 2.0) * 6
        rot = math.sin(t * 1.5) * 1.5  # rotacja w stopniach
        # Obrocony sprite
        img = pygame.transform.rotate(self.img, rot)
        ix = self.x - img.get_width() // 2
        iy = self.y - img.get_height() // 2 + bob
        win.blit(img, (ix, iy))
        # Kilwater (smuga piany) gdy plynie
        if self.state in (Ship.IN, Ship.OUT, Ship.BOMBARD_SAIL):
            wake_alpha = int(60 + 30 * math.sin(t * 4))
            wake = pygame.Surface((120, 20), pygame.SRCALPHA)
            # Kierunek smugi przeciwny do ruchu
            if self.state == Ship.IN:
                wx = self.x - (60 if self.from_left else -60)
            else:
                wx = self.x + (60 if self.from_left else -60)
            for i in range(3):
                alpha = wake_alpha - i * 20
                if alpha > 0:
                    pygame.draw.ellipse(wake, (255, 255, 255, alpha),
                                      (i * 30, 5 + i * 2, 60 - i * 15, 10 - i * 2))
            win.blit(wake, (wx - 60, self.y + 20 + bob))
        # Bryzgi przy dziobie gdy plynie
        if self.state in (Ship.IN, Ship.OUT, Ship.BOMBARD_SAIL) and int(t * 3) % 2 == 0:
            bx = self.x + (100 if self.from_left else -100)
            by = self.y + 30 + bob
            for i in range(3):
                sx = bx + random.randint(-15, 15)
                sy = by + random.randint(-10, 5)
                pygame.draw.circle(win, (255, 255, 255, 120), (int(sx), int(sy)), 2)
        # Demoniczna runa (pulsujaca)
        rune_alpha = int(120 + 80 * math.sin(t * 2.5))
        rune_font = pygame.font.SysFont("arial", 22, bold=True)
        rune = rune_font.render("ᚱ", True, (180, 80, 255))
        rune.set_alpha(rune_alpha)
        win.blit(rune, (self.x - rune.get_width() // 2, self.y + 10 + bob))
        # Blysk armat przy strzale
        if self.cannon_flash > 0:
            self.cannon_flash -= 1
            flash_size = self.cannon_flash * 2
            fx = self.x + (30 if self.from_left else -30)
            fy = self.y - 20 + bob
            pygame.draw.circle(win, (255, 200, 100, 200), (int(fx), int(fy)), flash_size)
            pygame.draw.circle(win, (255, 255, 200, 150), (int(fx), int(fy)), flash_size // 2)
