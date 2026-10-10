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
    def __init__(self, x, y, img, name, cost):
        self.name = name
        self.img = img
        self.x = x
        self.y = y
        self.width = self.img.get_width()
        self.height = self.img.get_height()
        self.cost = cost
                
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
        self.font = pygame.font.SysFont("arial", 30)
        self.small_font = pygame.font.SysFont("arial", 20)
        self.tower = tower

    def add_btn(self, img, name, dx=0, dy=0):
        self.items += 1
        self.buttons.append(Button(self, img, name, dx, dy))
    
    def get_item_cost(self):
        return self.item_cost[self.tower.level - 1]
        
    def draw(self, win):
        # Nowoczesny panel: rysowany programowo, bez grafiki tła
        tw = self.tower
        panel_w, panel_h = 200, 130
        px = self.x - panel_w // 2
        py = self.y - 110
        
        # Tło panelu
        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (12, 20, 36, 235), bg.get_rect(), border_radius=14)
        pygame.draw.rect(bg, (90, 140, 200, 120), bg.get_rect(), 2, border_radius=14)
        win.blit(bg, (px, py))
        
        # Nazwa wieży i poziom (kropki)
        name_font = pygame.font.SysFont("arial", 18, bold=True)
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
        self._draw_modern_btn(win, px + 12, btn_y, 86, btn_h, "UPGRADE", 
                              str(up_cost), (46, 134, 193), tw.level >= tw.max_level)
        # Sell
        sell_val = tw.sell_value()
        self._draw_modern_btn(win, px + 102, btn_y, 86, btn_h, "SELL",
                              f"+${sell_val}", (46, 160, 90), False)
        
        # Statystyki wieży
        stat_font = pygame.font.SysFont("arial", 15)
        stats = f"DMG {tw.damage}  |  RNG {tw.range}"
        slabel = stat_font.render(stats, True, (170, 190, 210))
        win.blit(slabel, (px + panel_w//2 - slabel.get_width()//2, py + 92))
        
        # Aktualizuj pozycje klikalne przycisków
        if len(self.buttons) >= 2:
            self.buttons[0].x, self.buttons[0].y = px + 12, btn_y
            self.buttons[0].width, self.buttons[0].height = 86, btn_h
            self.buttons[1].x, self.buttons[1].y = px + 102, btn_y
            self.buttons[1].width, self.buttons[1].height = 86, btn_h
    
    def _draw_modern_btn(self, win, x, y, w, h, title, sub, color, disabled):
        btn = pygame.Surface((w, h), pygame.SRCALPHA)
        bg_color = (50, 60, 80, 255) if disabled else (*color, 255)
        pygame.draw.rect(btn, bg_color, btn.get_rect(), border_radius=9)
        if not disabled:
            pygame.draw.rect(btn, (255, 255, 255, 60), btn.get_rect(), 1, border_radius=9)
        win.blit(btn, (x, y))
        tfont = pygame.font.SysFont("arial", 14, bold=True)
        sfont = pygame.font.SysFont("arial", 13)
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
        self.font = pygame.font.SysFont("comicsans", 25)

    def add_btn(self, img, name, cost):
        self.items += 1
        btn_x = self.x - 20
        btn_y = self.y -60 + (self.items-1)*75
        self.buttons.append(VerticalButton(btn_x, btn_y, img, name, cost))

    def get_item_cost(self, name):
        for btn in self.buttons:
            if btn.name == name:
                return btn.cost
        return -1

    def draw(self, win):
        win.blit(self.bg, (self.x - self.bg.get_width()/2, self.y-120))
        coin = pygame.transform.scale(money_img, (22, 22))
        for item in self.buttons:
            item.draw(win)
            # Moneta i cena jako jedna wycentrowana grupa pod przyciskiem
            text = self.font.render(str(item.cost), 1, (255,255,255))
            group_w = coin.get_width() + 6 + text.get_width()
            gx = item.x + item.width/2 - group_w/2
            gy = item.y + item.height + 8
            win.blit(coin, (gx, gy))
            win.blit(text, (gx + coin.get_width() + 6, gy - 2))
    
    