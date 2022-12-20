import pygame
from .tower import Tower
import os
import math
import time
from menu.menu import Menu
import random

menu_bg = pygame.transform.scale(pygame.image.load(os.path.join("images", "menu.png")), (150, 75))
upgrade_btn = pygame.transform.scale(pygame.image.load(os.path.join("images", "upgrade.png")), (50, 50))
tower_imgs1 = []
archer_imgs1 = []
pygame.mixer.init()
sound_1 = pygame.mixer.Sound("sounds/1.wav")
sound_2 = pygame.mixer.Sound("sounds/2.wav")
sound_3 = pygame.mixer.Sound("sounds/3.wav")
sound_4 = pygame.mixer.Sound("sounds/4.wav")
sound_5 = pygame.mixer.Sound("sounds/5.wav")
pygame.mixer.Sound.set_volume(sound_1, 1)
pygame.mixer.Sound.set_volume(sound_2, 0.1)
pygame.mixer.Sound.set_volume(sound_3, 0.5)
pygame.mixer.Sound.set_volume(sound_4, 0.5)
pygame.mixer.Sound.set_volume(sound_5, 0.5)

# load archer tower
tower_imgs1.append(pygame.transform.scale(
    pygame.image.load(os.path.join("images/turrets/towers", str(1) + ".png" )), (64, 64)))       

# load projectile shooter
archer_imgs1.append(pygame.transform.scale(
    pygame.image.load(os.path.join("images/turrets/projectiles", str(1) + ".png" )), (25, 25))) 

class WoodenTower(Tower):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.tower_imgs = tower_imgs1[:]
        self.archer_imgs = archer_imgs1[:]
        self.archer_count = 0
        self.range = 125
        self.inRange = False
        self.left = True
        self.timer = time.time()      
        self.damage = 1
        self.width = 0
        self.menu = Menu(self, self.x, self.y, menu_bg, [250, "MAX"])
        self.menu.add_btn(upgrade_btn, "Upgrade")                      
        self.moving = False
        self.name = "woodenTower"
        
    def get_upgrade_cost(self):
        return self.menu.get_item_cost()

    def draw(self, win):
        super().draw_radius(win)
        super().draw(win)  
        
        if self.inRange and not self.moving:     
            self.archer_count+= 1
            if self.archer_count >= len(self.archer_imgs) * 10:
                self.archer_count = 0
        else:
            self.archer_count = 0
            
        archer = self.archer_imgs[self.archer_count//10]
        if self.left == True:
            add = -25
        else:
            add = -archer.get_width() + 10
        win.blit(archer, ((self.x + self.width/2 + add + 10), (self.y - archer.get_height() - 5)))       
        
    def change_range(self, r):
        self.range = r

    def attack(self, enemies):
        money = 0
        self.inRange = False
        enemy_closest = []

        for enemy in enemies:
            x = enemy.x
            y = enemy.y
            dis = math.sqrt((self.x - x)**2 + (self.y - y)**2)
            if dis < self.range:
                self.inRange = True
                enemy_closest.append(enemy)
        enemy_closest.sort(key= lambda x: x.x)
        
        if len(enemy_closest) > 0:            
            first_enemy = enemy_closest[0]
            if time.time() - self.timer >= 1:
                self.timer = time.time()
                
                sound_2.play()
                    
                if first_enemy.hit(self.damage) == True:
                    sound_3.play()
                    money = first_enemy.money
                    enemies.remove(first_enemy)
                  
            if first_enemy.x > self.x and not (self.left):
                self.left = True
                for x, img in enumerate(self.archer_imgs):
                    self.archer_imgs[x] = pygame.transform.flip(img, True, False)
            elif self.left and first_enemy.x < self.x:
                self.left = False
                for x, img in enumerate(self.archer_imgs):
                    self.archer_imgs[x] = pygame.transform.flip(img, True, False)
        return money
"""
METAL TOWER 
"""
menu_bg = pygame.transform.scale(pygame.image.load(os.path.join("images", "menu.png")), (150, 75))
upgrade_btn = pygame.transform.scale(pygame.image.load(os.path.join("images", "upgrade.png")), (50, 50))
tower_imgs2 = []
archer_imgs2 = []
                    
# load archer tower
tower_imgs2.append(pygame.transform.scale(
    pygame.image.load(os.path.join("images/turrets/towers", str(2) + ".png" )), (64, 64)))       

# load projectile shooter
archer_imgs2.append(pygame.transform.scale(
    pygame.image.load(os.path.join("images/turrets/projectiles", str(2) + ".png" )), (25, 25))) 

class MetalTower(WoodenTower):
     def __init__(self, x, y):
        super().__init__(x, y)
        self.tower_imgs = tower_imgs2[:]
        self.archer_imgs = archer_imgs2[:]
        self.archer_count = 0
        self.range = 125
        self.inRange = False
        self.left = True
        self.timer = time.time()      
        self.damage = 3
        self.menu = Menu(self, self.x, self.y, menu_bg, [250, "MAX"])
        self.menu.add_btn(upgrade_btn, "Upgrade")   
        self.name = "metalTower"
"""
GOLDEN TOWER 
"""
menu_bg = pygame.transform.scale(pygame.image.load(os.path.join("images", "menu.png")), (150, 75))
upgrade_btn = pygame.transform.scale(pygame.image.load(os.path.join("images", "upgrade.png")), (50, 50))
tower_imgs3 = []
archer_imgs3 = []
                    
# load archer tower
tower_imgs3.append(pygame.transform.scale(
    pygame.image.load(os.path.join("images/turrets/towers", str(3) + ".png" )), (64, 64)))       

# load projectile shooter
archer_imgs3.append(pygame.transform.scale(
    pygame.image.load(os.path.join("images/turrets/projectiles", str(3) + ".png" )), (25, 25))) 

class GoldenTower(WoodenTower):
     def __init__(self, x, y):
        super().__init__(x, y)
        self.tower_imgs = tower_imgs3[:]
        self.archer_imgs = archer_imgs3[:]
        self.archer_count = 0
        self.range = 125
        self.inRange = False
        self.left = True
        self.timer = time.time()      
        self.damage = 5
        self.menu = Menu(self, self.x, self.y, menu_bg, [250, "MAX"])
        self.menu.add_btn(upgrade_btn, "Upgrade") 
        self.name = "goldenTower"  
"""
FIRE TOWER 
"""
menu_bg = pygame.transform.scale(pygame.image.load(os.path.join("images", "menu.png")), (150, 75))
upgrade_btn = pygame.transform.scale(pygame.image.load(os.path.join("images", "upgrade.png")), (50, 50))
tower_imgs4 = []
archer_imgs4 = []
                    
# load archer tower
tower_imgs4.append(pygame.transform.scale(
    pygame.image.load(os.path.join("images/turrets/towers", str(4) + ".png" )), (64, 64)))       

# load projectile shooter
archer_imgs4.append(pygame.transform.scale(
    pygame.image.load(os.path.join("images/turrets/projectiles", str(4) + ".png" )), (25, 25))) 

class FireTower(WoodenTower):
     def __init__(self, x, y):
        super().__init__(x, y)
        self.tower_imgs = tower_imgs4[:]
        self.archer_imgs = archer_imgs4[:]
        self.archer_count = 0
        self.range = 125
        self.inRange = False
        self.left = True
        self.timer = time.time()      
        self.damage = 8
        self.menu = Menu(self, self.x, self.y, menu_bg, [250, "MAX"])
        self.menu.add_btn(upgrade_btn, "Upgrade")           
        self.name = "fireTower"
"""
BLAZE TOWER 
"""
menu_bg = pygame.transform.scale(pygame.image.load(os.path.join("images", "menu.png")), (150, 75))
upgrade_btn = pygame.transform.scale(pygame.image.load(os.path.join("images", "upgrade.png")), (50, 50))
tower_imgs5 = []
archer_imgs5 = []
                    
# load archer tower
tower_imgs5.append(pygame.transform.scale(
    pygame.image.load(os.path.join("images/turrets/towers", str(5) + ".png" )), (64, 64)))       

# load projectile shooter
archer_imgs5.append(pygame.transform.scale(
    pygame.image.load(os.path.join("images/turrets/projectiles", str(5) + ".png" )), (25, 25))) 

class BlazeTower(WoodenTower):
     def __init__(self, x, y):
        super().__init__(x, y)
        self.tower_imgs = tower_imgs5[:]
        self.archer_imgs = archer_imgs5[:]
        self.archer_count = 0
        self.range = 125
        self.inRange = False
        self.left = True
        self.timer = time.time()      
        self.damage = 10       
        self.menu = Menu(self, self.x, self.y, menu_bg, [250, "MAX"])
        self.menu.add_btn(upgrade_btn, "Upgrade")   
        self.name = "blazeTower"