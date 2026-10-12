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
        
    def draw(self, win):
        # Nowoczesny panel: rysowany programowo, bez grafiki tła
        tw = self.tower
        panel_w, panel_h = 230, 150
        px = self.x - panel_w // 2
        py = self.y - 120
        
        # Tło panelu
        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (12, 20, 36, 235), bg.get_rect(), border_radius=14)
        pygame.draw.rect(bg, (90, 140, 200, 120), bg.get_rect(), 2, border_radius=14)
        win.blit(bg, (px, py))
        
        # Nazwa wieży i poziom (kropki)
        name_font = pygame.font.SysFont("segoe ui, calibri, arial", 18, bold=True)
        name_text = tw.name if hasattr(tw, 'name') else "Wieza"
        label = name_font.render(name_text, True, (255, 255, 255))
        win.blit(label, (px + 14, py + 10))
        # Kropki poziomu
        for i in range(tw.max_level):
            cx = px + panel_w - 20 - i * 18
            cy = py + 20
            color = (255, 215, 0) if i < tw.level else (70, 90, 120)
            pygame.draw.circle(win, color, (cx, cy), 6)
        
        # Przyciski rysowane jako nowoczesne prostokąty
        btn_y = py + 44
        btn_h = 36
        # Upgrade
        up_cost = self.item_cost[tw.level - 1] if tw.level < tw.max_level else "MAX"
        self._draw_modern_btn(win, px + 12, btn_y, 100, btn_h, "UPGRADE", 
                              str(up_cost), (46, 134, 193), tw.level >= tw.max_level)
        # Sell
        sell_val = tw.sell_value()
        self._draw_modern_btn(win, px + 118, btn_y, 100, btn_h, "SELL",
                              f"+${sell_val}", (46, 160, 90), False)
        
        # Statystyki wieży
        stat_font = pygame.font.SysFont("segoe ui, calibri, arial", 15)
        # Q8: DPS = obrazenia / czas przeladowania
        dps = tw.damage  # 1 strzal na sekunde
        stats = f"DMG {tw.damage}  RNG {tw.range}  DPS {dps}"
        slabel = stat_font.render(stats, True, (170, 190, 210))
        win.blit(slabel, (px + panel_w//2 - slabel.get_width()//2, py + 92))
        kfont = pygame.font.SysFont("segoe ui, calibri, arial", 13)
        klabel = kfont.render(f"KILLS {tw.kills}", True, (255, 215, 0))
        win.blit(klabel, (px + panel_w//2 - klabel.get_width()//2, py + 110))
        
        # Aktualizuj pozycje klikalne przycisków
        if len(self.buttons) >= 2:
            self.buttons[0].x, self.buttons[0].y = px + 12, btn_y
            self.buttons[0].width, self.buttons[0].height = 100, btn_h
            self.buttons[1].x, self.buttons[1].y = px + 118, btn_y
            self.buttons[1].width, self.buttons[1].height = 100, btn_h
    
    def _draw_modern_btn(self, win, x, y, w, h, title, sub, color, disabled):
        btn = pygame.Surface((w, h), pygame.SRCALPHA)
        bg_color = (50, 60, 80, 255) if disabled else (*color, 255)
        pygame.draw.rect(btn, bg_color, btn.get_rect(), border_radius=9)
        if not disabled:
            pygame.draw.rect(btn, (255, 255, 255, 60), btn.get_rect(), 1, border_radius=9)
        win.blit(btn, (x, y))
        tfont = pygame.font.SysFont("segoe ui, calibri, arial", 14, bold=True)
        sfont = pygame.font.SysFont("segoe ui, calibri, arial", 13)
        tcol = (140, 150, 165) if disabled else (255, 255, 255)
        scol = (140, 150, 165) if disabled else (255, 255, 200)
        t = tfont.render(title, True, tcol)
        s = sfont.render(str(sub), True, scol)
        win.blit(t, (x + w//2 - t.get_width()//2, y + 4))
        win.blit(s, (x + w//2 - s.get_width()//2, y + 19))
            
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
    
    