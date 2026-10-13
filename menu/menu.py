import pygame
import os
pygame.font.init()

money_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "money.png")), (20, 20))

class Button():
    def __init__(self, menu, img, name, dx=0, dy=0):
        self.name = name
        self.img = img
        self.menu = menu
        self.dx = dx
        self.dy = dy
        self.width = self.img.get_width()
        self.height = self.img.get_height()
        self.update()

    def click(self, X, Y):
        
        if X <= self.x + self.width and X >= self.x:
            if Y <= self.y + self.height and Y >= self.y:
                return True
        return False
    
    def draw(self, win):
        win.blit(self.img, (self.x, self.y))
    
    def update(self):
        self.x = self.menu.x + self.dx
        self.y = self.menu.y + self.dy
        
class VerticalButton(Button):
    def __init__(self, x, y, img, name, cost, damage=0):
        self.name = name
        self.img = img
        self.x = x
        self.y = y
        self.width = self.img.get_width()
        self.height = self.img.get_height()
        self.cost = cost
        self.damage = damage
                
class Menu():
    def __init__(self, tower, x, y, img, item_cost):
        self.x = x
        self.y = y
        self.width = img.get_width()
        self.height = img.get_height()
        self.item_names = []
        self.buttons = []
        self.item_cost = item_cost
        self.items = 0
        self.bg = img
        self.font = pygame.font.SysFont("segoe ui, calibri, arial", 30)
        self.small_font = pygame.font.SysFont("segoe ui, calibri, arial", 20)
        self.tower = tower

    def add_btn(self, img, name, dx=0, dy=0):
        self.items += 1
        self.buttons.append(Button(self, img, name, dx, dy))
    
    def get_item_cost(self):
        return self.item_cost[self.tower.level - 1]
        
    def draw(self, win, money=None):
        # Hologram HUD (wariant D) - kolor zalezny od typu wiezy
        tw = self.tower
        tname = type(tw).__name__
        colors = {
            "WoodenTower": (139, 90, 43),
            "MetalTower": (120, 150, 180),
            "GoldenTower": (212, 175, 55),
            "FireTower": (220, 80, 40),
            "BlazeTower": (180, 60, 200),
        }
        holo = colors.get(tname, (0, 255, 204))
        panel_w, panel_h = 240, 160
        px = self.x - panel_w // 2
        py = self.y - 210  # calkowicie nad wieza (wieza w pelni widoczna)
        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (8, 14, 22, 220), bg.get_rect(), border_radius=8)
        pygame.draw.rect(bg, (*holo, 255), bg.get_rect(), 2, border_radius=8)
        c = 12
        for cx, cy in [(0, 0), (panel_w, 0), (0, panel_h), (panel_w, panel_h)]:
            dx = -1 if cx == 0 else 1
            dy = -1 if cy == 0 else 1
            pygame.draw.line(bg, (*holo, 255), (cx, cy), (cx + dx*c, cy), 3)
            pygame.draw.line(bg, (*holo, 255), (cx, cy), (cx, cy + dy*c), 3)
        win.blit(bg, (px, py))
        tag_font = pygame.font.SysFont("consolas, monospace", 11)
        tag = tag_font.render("TOWER.EXE", True, holo)
        pygame.draw.rect(win, (8, 14, 22), (px + 8, py - 10, tag.get_width() + 8, 14))
        win.blit(tag, (px + 12, py - 8))
        name_font = pygame.font.SysFont("consolas, monospace", 15, bold=True)
        name_text = tw.name if hasattr(tw, 'name') else tname
        label = name_font.render(f"> {name_text.upper()}", True, holo)
        win.blit(label, (px + 14, py + 14))
        lvl, maxlvl = tw.level, tw.max_level
        bar_x, bar_y, bar_w, bar_h = px + 14, py + 36, panel_w - 28, 8
        pygame.draw.rect(win, (40, 50, 65), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        fill_w = int(bar_w * lvl / maxlvl)
        pygame.draw.rect(win, holo, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
        lvl_txt = tag_font.render(f"LV.{lvl}/{maxlvl}", True, holo)
        win.blit(lvl_txt, (px + panel_w - lvl_txt.get_width() - 14, py + 32))
        stat_font = pygame.font.SysFont("consolas, monospace", 12)
        slabel = stat_font.render(f"DMG {tw.damage}  RNG {tw.range}", True, holo)
        win.blit(slabel, (px + 14, py + 52))
        klabel = stat_font.render(f"KILLS {tw.kills}", True, holo)
        win.blit(klabel, (px + 14, py + 68))
        btn_y, btn_h = py + 92, 52
        is_max = tw.level >= tw.max_level
        if not is_max:
            up_cost = self.item_cost[tw.level - 1]
            # Wyszarzony gdy nie stac, ale zawsze widoczny koszt (bez -$)
            affordable = money is not None and money >= up_cost
            self._draw_holo_btn(win, px + 12, btn_y, 106, btn_h, "UPGRADE", f"${up_cost}",
                                holo, not affordable)
        else:
            self._draw_holo_btn(win, px + 12, btn_y, 106, btn_h, "MAX LEVEL", "", (100, 110, 120), True)
        sell_val = tw.sell_value()
        self._draw_holo_btn(win, px + 122, btn_y, 106, btn_h, "SELL", f"+${sell_val}", (255, 100, 100), False)
        if len(self.buttons) >= 2:
            if not is_max:
                self.buttons[0].x, self.buttons[0].y = px + 12, btn_y
                self.buttons[0].width, self.buttons[0].height = 106, btn_h
            else:
                self.buttons[0].x, self.buttons[0].y = -100, -100
                self.buttons[0].width, self.buttons[0].height = 0, 0
            self.buttons[1].x, self.buttons[1].y = px + 122, btn_y
            self.buttons[1].width, self.buttons[1].height = 106, btn_h

    def _draw_holo_btn(self, win, x, y, w, h, title, sub, color, disabled, sub_color=None):
        btn = pygame.Surface((w, h), pygame.SRCALPHA)
        r, g, b = color[0], color[1], color[2]
        if disabled:
            pygame.draw.rect(btn, (40, 45, 55, 180), btn.get_rect(), border_radius=6)
            pygame.draw.rect(btn, (80, 90, 100, 100), btn.get_rect(), 1, border_radius=6)
        else:
            pygame.draw.rect(btn, (r, g, b, 40), btn.get_rect(), border_radius=6)
            pygame.draw.rect(btn, (r, g, b, 255), btn.get_rect(), 2, border_radius=6)
        win.blit(btn, (x, y))
        tfont = pygame.font.SysFont("consolas, monospace", 13, bold=True)
        sfont = pygame.font.SysFont("consolas, monospace", 12)
        tcol = (120, 130, 140) if disabled else (r, g, b)
        t = tfont.render(title, True, tcol)
        win.blit(t, (x + w//2 - t.get_width()//2, y + 8))
        if sub:
            scol = sub_color if sub_color else tcol
            s = sfont.render(str(sub), True, scol)
            win.blit(s, (x + w//2 - s.get_width()//2, y + 28))

            
    def get_clicked(self, X, Y):
        for btn in self.buttons:
            if btn.click(X, Y):
                return btn.name
        return None

    def get_hovered(self, X, Y):
        """U9: zwraca nazwe przycisku pod kursorem (do podgladu zasiegu)."""
        for btn in self.buttons:
            if btn.click(X, Y):
                return btn.name
        return None
    
    def update(self):
        for btn in self.buttons:
            btn.update()
            
class VerticalMenu(Menu):
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.width = img.get_width()
        self.height = img.get_height()
        self.buttons = []
        self.items = 0
        self.bg = img
        self.font = pygame.font.SysFont("segoe ui, calibri, arial", 25)

    def add_btn(self, img, name, cost, damage=0):
        self.items += 1
        btn_x = self.x - 20
        btn_y = self.y -60 + (self.items-1)*75
        self.buttons.append(VerticalButton(btn_x, btn_y, img, name, cost, damage))

    def get_item_cost(self, name):
        for btn in self.buttons:
            if btn.name == name:
                return btn.cost
        return -1

    def get_rect(self):
        """Prostokat panelu sklepu (do przecigania i hover)."""
        panel_w = 200
        panel_h = len(self.buttons) * 78 + 50
        return pygame.Rect(self.x - panel_w // 2, self.y - 140, panel_w, panel_h)

    def draw(self, win, mouse_pos=None):
        # Nowoczesny sklep: ciemny panel, wyrownane ceny, bez niebieskiego tła
        # mouse_pos w wspolrzednych gry (po przeskalowaniu) - do hovera
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()
        panel_w = 200
        panel_h = len(self.buttons) * 78 + 50
        px = self.x - panel_w // 2
        py = self.y - 140

        # Przezroczystosc gdy mysz nie jest nad panelem
        mx, my = mouse_pos
        hovered_panel = self.get_rect().collidepoint(mx, my)
        alpha = 255 if hovered_panel else 110

        # Rysuj wszystko na osobnej powierzchni, potem naloz z alfa
        surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (10, 16, 28, 240), bg.get_rect(), border_radius=16)
        pygame.draw.rect(bg, (80, 120, 180, 100), bg.get_rect(), 2, border_radius=16)
        surf.blit(bg, (0, 0))

        # Naglowek SKLEP
        hfont = pygame.font.SysFont("segoe ui, calibri, arial", 18, bold=True)
        ht = hfont.render("SHOP", True, (200, 220, 240))
        surf.blit(ht, (panel_w//2 - ht.get_width()//2, 10))
        
        for idx, item in enumerate(self.buttons):
            bx = px + 15
            by = py + 42 + idx * 78
            # Tlo przycisku
            btn_bg = pygame.Surface((panel_w - 30, 68), pygame.SRCALPHA)
            # Hover efekt
            hovering = bx <= mx <= bx + panel_w - 30 and by <= my <= by + 68
            if hovering:
                pygame.draw.rect(btn_bg, (35, 50, 75, 255), btn_bg.get_rect(), border_radius=10)
            else:
                pygame.draw.rect(btn_bg, (22, 32, 50, 255), btn_bg.get_rect(), border_radius=10)
            surf.blit(btn_bg, (bx - px, by - py))
            # Ikona wiezy
            icon = pygame.transform.scale(item.img, (44, 44))
            surf.blit(icon, (bx + 8 - px, by + 12 - py))
            # Schludny layout: nazwa / obrazenia / cena - wszystko wyrownane
            nfont = pygame.font.SysFont("segoe ui, calibri, arial", 14, bold=True)
            dfont = pygame.font.SysFont("segoe ui, calibri, arial", 12)
            pfont = pygame.font.SysFont("segoe ui, calibri, arial", 14, bold=True)
            names = ["Wooden Tower", "Metal Tower", "Golden Tower", "Fire Tower", "Blaze Tower"]
            tx = bx + 60 - px  # wspolna lewa krawedz tekstu
            nm = nfont.render(names[idx] if idx < len(names) else item.name, True, (230, 235, 240))
            surf.blit(nm, (tx, by + 6 - py))
            dm = dfont.render(f"DMG {item.damage}", True, (170, 180, 190))
            surf.blit(dm, (tx, by + 26 - py))
            pt = pfont.render(f"$ {item.cost}", True, (255, 215, 0))
            surf.blit(pt, (tx, by + 44 - py))
            # Aktualizuj pozycje klikalna (wspolrzedne ekranu)
            item.x, item.y = bx, by
            item.width, item.height = panel_w - 30, 68
        # Naloz caly panel z przezroczystoscia
        if alpha < 255:
            surf.set_alpha(alpha)
        win.blit(surf, (px, py))
    
    