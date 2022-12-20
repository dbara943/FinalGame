import pygame
from menu.menu import Menu
import os

menu_bg = pygame.transform.scale(pygame.image.load(os.path.join("images", "menu.png")), (150, 75))
upgrade_btn = pygame.transform.scale(pygame.image.load(os.path.join("images", "upgrade.png")), (50, 50))

class Tower:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 0
        self.height = 0
        self.sell_price = [0,0,0]
        self.price = [0,0,0]
        self.level = 1
        self.selected = False
        self.menu = Menu(self, self.x, self.y, menu_bg, [250, 500, "MAX"])
        self.menu.add_btn(upgrade_btn, "Upgrade")
        self.tower_imgs = []
        self.damage = 1
        
    def draw(self, win):
        img = self.tower_imgs[self.level-1]
        win.blit(img, (self.x-img.get_width()//2, self.y-img.get_height()//2))
    
        if self.selected:
            self.menu.draw(win)
    
    def draw_radius(self, win):
        if self.selected: 
            surface = pygame.Surface((self.range*4, self.range*4), pygame.SRCALPHA, 32)
            pygame.draw.circle(surface, (128,128,128, 128), (self.range, self.range), self.range, 0)   
            win.blit(surface, (self.x - self.range, self.y - self.range))
    
    def click(self, X, Y):
        img = self.tower_imgs[self.level - 1]
        if X - img.get_width()//2 <= self.x  + self.width and X >= self.x:
            if Y - img.get_height()//2 <= self.y + self.height and Y >= self.y:
                return True 
        return False
    
    def sell(self):
        return self.sell_price[self.level-1]

    def upgrade(self):
        if self.level < len(self.tower_imgs):   
            self.level += 1
            self.damage += 1
    
    def get_upgrade_cost(self):
        return self.price[self.level - 1]
    
    def move(self, x, y):
        self.x = x
        self.y = y
        self.menu.x = x
        self.menu.y = y
        self.menu.update()