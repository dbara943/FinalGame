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
        win.blit(self.bg, (self.x - self.bg.get_width()/2, self.y - 90))
        for item in self.buttons:
            item.draw(win)
            if item.name == "Sell":
                label = "+$" + str(self.tower.sell_value())
                color = (130, 255, 130)
            else:
                label = "$" + str(self.item_cost[self.tower.level - 1])
                color = (255, 255, 255)
            text = self.small_font.render(label, 1, color)
            win.blit(text, (item.x + item.width//2 - text.get_width()//2,
                            item.y + item.height + 4))
            
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
    
    