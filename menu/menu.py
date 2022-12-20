import pygame
import os
pygame.font.init()

money_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "money.png")), (20, 20))

class Button():
    def __init__(self, menu, img, name):
        self.name = name
        self.img = img
        self.x = menu.x
        self.y = menu.y
        self.menu = menu
        self.width = self.img.get_width()
        self.height = self.img.get_height()

    def click(self, X, Y):
        
        if X <= self.x + self.width and X >= self.x:
            if Y <= self.y + self.height and Y >= self.y:
                return True
        return False
    
    def draw(self, win):
        win.blit(self.img, (self.x, self.y))
    
    def update(self):
        self.x = self.menu.x
        self.y = self.menu.y        
        
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
        self.tower = tower

    def add_btn(self, img, name):
        self.items += 1
        btn_x = self.x - self.bg.get_width()/2 + 10
        btn_y = self.y - 75 + 10
        self.buttons.append(Button(self, img, name))
    
    def get_item_cost(self):
        return self.item_cost[self.tower.level - 1]
        
    def draw(self, win):
        win.blit(self.bg, (self.x - self.bg.get_width()/2, self.y - 80))
        for item in self.buttons:
            item.draw(win)
            win.blit(money_img, (item.x + item.width + 50, item.y + 20))
            text = self.font.render(str(self.item_cost[self.tower.level - 1]), 1, (255,255,255))    
            win.blit(text, (item.x + item.width + 30 - text.get_width()/2, item.y + money_img.get_height() - 8))
            
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
        for item in self.buttons:
            item.draw(win)
            win.blit(money_img, (item.x - 15, item.y + item.height + 10))
            text = self.font.render(str(item.cost), 1, (255,255,255))
            win.blit(text, (item.x + item.width/2 - text.get_width()/2 + 7, item.y + item.height + 5))
    
    