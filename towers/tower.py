import pygame
import math
from menu.menu import Menu
import os

menu_bg = pygame.transform.scale(pygame.image.load(os.path.join("images", "menu.png")), (240, 110))
upgrade_btn = pygame.transform.scale(pygame.image.load(os.path.join("images", "upgrade.png")), (50, 50))
sell_btn = pygame.transform.scale(pygame.image.load(os.path.join("images", "sell.png")), (50, 50))

class Tower:
    buy_price = 0
    upgrade_costs = [250, 500]  # domyslne koszty ulepszen (lvl 1->2, 2->3); klasy je nadpisuja
    # Obrazenia z upgradu: drozsze wieze zyskuja wiecej (wczesniej plaskie +2 dla
    # wszystkich - upgrade Blaze'a za 1500 dawal tyle samo co upgrade Woodena za 150).
    upgrade_dmg = 2

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
        # Cache na gorace petle (wydajnosc) - bez getattr
        self._synergy = 1.0
        self._link = None  # typ linku sasiada tego samego typu ("wood"/"metal"/...)
        self._rain_mod = 1.0
        self._target_buf = []  # reuzywalny bufor celow (bez alokacji co tick)
        self._setup_menu()
        self.tower_imgs = []
        self.damage = 1
        self._img_cache = {}
        self.target_priority = "first"  # first, strong, weak, last
        # Umiejetnosc aktywna
        self.ability_cooldown = 0  # klatki do gotowosci
        self.ability_max_cooldown = 1800  # 30s przy 60 FPS
        self.ability_active = 0  # klatki pozostalego czasu dzialania
        self.attack_cooldown = 0  # tick-based cooldown ataku (dziala z speed)
        self.current_target = None  # R3: aktualny cel (do linii celowania)
        self.kills = 0  # R5: licznik zabojstw tej wiezy

    def _setup_menu(self):
        # Koszty ulepszen zaleza od klasy wiezy (nie stale 250/500 dla wszystkich)
        costs = list(getattr(type(self), "upgrade_costs", [250, 500])) + ["MAX"]
        self.menu = Menu(self, self.x, self.y, menu_bg, costs)
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
        # Cien usuniety na prosbe gracza
        # Tint przy stawianiu: lekko zielony (OK) / czerwony (zle miejsce) zamiast kolka
        placement = getattr(self, '_placement_valid', None)
        if placement is not None:
            tinted = img.copy()
            wash = pygame.Surface(img.get_size(), pygame.SRCALPHA)
            wash.fill((0, 255, 0, 150) if placement else (255, 0, 0, 150))  # Warcraft: mocny wash
            tinted.blit(wash, (0, 0))
            img = tinted
        win.blit(img, (self.x-img.get_width()//2, self.y-img.get_height()//2))
        # U7: gwiazdki poziomu nad wieza
        for i in range(self.level):
            sx = self.x - (self.level - 1) * 9 + i * 18
            sy = self.y - img.get_height() // 2 - 14
            pts = []
            for k in range(10):
                ang = math.pi / 5 * k - math.pi / 2
                r = 7 if k % 2 == 0 else 3
                pts.append((sx + r * math.cos(ang), sy + r * math.sin(ang)))
            pygame.draw.polygon(win, (255, 215, 0), pts)
            pygame.draw.polygon(win, (180, 140, 0), pts, 1)


        if self.selected:
            # R3: linia celowania do aktualnego celu
            tgt = getattr(self, 'current_target', None)
            if tgt is not None and not tgt.dying and not tgt.dead and not tgt.reached_end:
                # Przerywana linia
                steps = 20
                for i in range(0, steps, 2):
                    t1 = i / steps
                    t2 = (i + 1) / steps
                    x1 = int(self.x + (tgt.x - self.x) * t1)
                    y1 = int(self.y - 20 + (tgt.y - (self.y - 20)) * t1)
                    x2 = int(self.x + (tgt.x - self.x) * t2)
                    y2 = int(self.y - 20 + (tgt.y - (self.y - 20)) * t2)
                    pygame.draw.line(win, (255, 100, 100, 200), (x1, y1), (x2, y2), 2)
            # Menu rysowane osobno na samym wierzchu przez game.py (nieprzykryte przez inne wieze)

    def draw_radius(self, win):
        if self.selected or getattr(self, 'moving', False):
            # Nowoczesny okrag: subtelne wypelnienie + jasna obwiednia
            r = self.range
            surface = pygame.Surface((r*2, r*2), pygame.SRCALPHA, 32)
            # Wypelnienie - bardzo delikatne
            pygame.draw.circle(surface, (100, 200, 255, 35), (r, r), r, 0)
            # Obwiednia - jasna, cienka
            pygame.draw.circle(surface, (150, 220, 255, 160), (r, r), r, 2)
            # Wewnetrzna linia przerywana dla stylu
            for angle in range(0, 360, 15):
                rad = math.radians(angle)
                x1 = r + int((r - 8) * math.cos(rad))
                y1 = r + int((r - 8) * math.sin(rad))
                x2 = r + int((r - 2) * math.cos(rad))
                y2 = r + int((r - 2) * math.sin(rad))
                pygame.draw.line(surface, (150, 220, 255, 90), (x1, y1), (x2, y2), 2)
            win.blit(surface, (self.x - r, self.y - r))

    def click(self, X, Y):
        # Caly sprite jest klikalny (wczesniej tylko prawa polowa).
        img = self.get_level_img()
        if abs(X - self.x) <= img.get_width() // 2 and abs(Y - self.y) <= img.get_height() // 2:
            return True
        return False

    def sell_value(self, rate=0.7):
        # Zwrot % tego, co wlozono w wieze (zakup + ulepszenia).
        # Stawka zalezy od trudnosci: EASY 80%, NORMAL 70%, HARD 60%.
        return int(self.total_spent * rate)

    def upgrade(self, cost=0):
        if self.level < self.max_level:
            self.total_spent += cost
            self.level += 1
            # Obrazenia z upgradu skaluja sie z klasa wiezy (upgrade_dmg), nie plaskie +2
            self.damage += getattr(type(self), "upgrade_dmg", 2)
            self.range += 12
            # A5: efekt ulepszenia (flaga do game.py)
            self._upgrade_fx = True

    def get_upgrade_cost(self):
        return self.price[self.level - 1]

    def get_synergy_bonus(self, towers):
        """Stary plaski bonus +15% obrazen - ZASTAPIONY unikatowymi linkami
        (get_link_type). Zostawione dla kompatybilnosci: zwraca 1.0."""
        return 1.0

    _LINK_KEYS = {"WoodenTower": "wood", "MetalTower": "metal",
                  "GoldenTower": "gold", "FireTower": "fire",
                  "BlazeTower": "blaze"}

    def get_link_type(self, towers):
        """Link sasiada: wieza tego samego typu w promieniu 100px ->
        klucz unikatowego bonusu dla tego typu (None gdy brak sasiada).
        Bonusy: Wood +30% szybkostrzelnosci, Metal +25% zasiegu i dluzsze
        spowolnienie, Gold +50% zlota za zabojstwa, Fire +70% splash,
        Blaze lancuch na 2. wroga (50% dmg)."""
        for tw in towers:
            if tw is self:
                continue
            if type(tw).__name__ == type(self).__name__:
                dx, dy = tw.x - self.x, tw.y - self.y
                if dx*dx + dy*dy < 10000:
                    return self._LINK_KEYS.get(type(self).__name__)
        return None

    def move(self, x, y):
        self.x = x
        self.y = y
        self.menu.x = x
        self.menu.y = y
        self.menu.update()
