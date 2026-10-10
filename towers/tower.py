import pygame
from menu.menu import Menu
import os

menu_bg = pygame.transform.scale(pygame.image.load(os.path.join("images", "menu.png")), (240, 110))
upgrade_btn = pygame.transform.scale(pygame.image.load(os.path.join("images", "upgrade.png")), (50, 50))
sell_btn = pygame.transform.scale(pygame.image.load(os.path.join("images", "sell.png")), (50, 50))

class Tower:
    buy_price = 0

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 0
        self.height = 0
        self.sell_price = [0,0,0]
        self.price = [0,0,0]
        self.level = 1
        self.max_level = 3
        self.selected = False
        self.total_spent = self.buy_price
        self._setup_menu()
        self.tower_imgs = []
        self.damage = 1
        self._img_cache = {}
        self.target_priority = "first"  # first, strong, weak, last
        # Umiejetnosc aktywna
        self.ability_cooldown = 0  # klatki do gotowosci
        self.ability_max_cooldown = 1800  # 30s przy 60 FPS
        self.ability_active = 0  # klatki pozostalego czasu dzialania

    def _setup_menu(self):
        self.menu = Menu(self, self.x, self.y, menu_bg, [250, 500, "MAX"])
        self.menu.add_btn(upgrade_btn, "Upgrade", dx=-65, dy=-45)
        self.menu.add_btn(sell_btn, "Sell", dx=15, dy=-45)

    def get_level_img(self):
        # Wieze maja jeden obrazek bazowy; wyzsze poziomy sa powiekszone,
        # zeby widac bylo roznice (kiedys upgrade w ogole nie dzialal,
        # bo kod wymagal osobnego obrazka na poziom).
        if self.level not in self._img_cache:
            base = self.tower_imgs[0]
            scale = 1 + 0.18 * (self.level - 1)
            w = int(base.get_width() * scale)
            h = int(base.get_height() * scale)
            self._img_cache[self.level] = pygame.transform.scale(base, (w, h))
        return self._img_cache[self.level]

    def draw(self, win):
        img = self.get_level_img()
        win.blit(img, (self.x-img.get_width()//2, self.y-img.get_height()//2))

        if self.selected:
            self.menu.draw(win)

    def draw_radius(self, win):
        if self.selected or getattr(self, 'moving', False):
            # Powierzchnia 2x zasieg wystarczy (wczesniej byla 4x za duza).
            surface = pygame.Surface((self.range*2, self.range*2), pygame.SRCALPHA, 32)
            pygame.draw.circle(surface, (128,128,128, 128), (self.range, self.range), self.range, 0)
            win.blit(surface, (self.x - self.range, self.y - self.range))

    def click(self, X, Y):
        # Caly sprite jest klikalny (wczesniej tylko prawa polowa).
        img = self.get_level_img()
        if abs(X - self.x) <= img.get_width() // 2 and abs(Y - self.y) <= img.get_height() // 2:
            return True
        return False

    def sell_value(self):
        # Zwrot 70% tego, co wlozono w wieze (zakup + ulepszenia).
        return (self.total_spent * 7) // 10

    def upgrade(self, cost=0):
        if self.level < self.max_level:
            self.total_spent += cost
            self.level += 1
            self.damage += 2
            self.range += 12

    def get_upgrade_cost(self):
        return self.price[self.level - 1]

    def move(self, x, y):
        self.x = x
        self.y = y
        self.menu.x = x
        self.menu.y = y
        self.menu.update()
