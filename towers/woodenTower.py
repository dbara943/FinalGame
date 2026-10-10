import pygame
from .tower import Tower
from .projectile import Projectile
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
    buy_price = 100
    ability_name = "Rapid Fire"
    ability_desc = "2x szybkosc ataku przez 5s"
    def __init__(self, x, y):
        super().__init__(x, y)
        self.tower_imgs = tower_imgs1[:]
        self.archer_imgs = archer_imgs1[:]
        self.archer_count = 0
        self.range = 125
        self.inRange = False
        self.facing_left = False
        self.timer = time.time()      
        self.damage = 1
        self.width = 0
        self._setup_menu()
        self.moving = False
        self.name = "woodenTower"

    def activate_ability(self, enemies, projectiles):
        """Rapid Fire: 2x szybkosc ataku przez 5 sekund."""
        if self.ability_cooldown > 0:
            return False
        self.ability_cooldown = self.ability_max_cooldown
        self.ability_active = 300  # 5s przy 60 FPS
        self._rapid_fire = True
        return True
        
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
        # Lucznik przechyla sie w strone wroga (wczesniej w przeciwna).
        add = -32 if self.facing_left else -12
        win.blit(archer, ((self.x + self.width/2 + add + 10), (self.y - archer.get_height() - 5)))       
        
    def change_range(self, r):
        self.range = r

    def attack(self, enemies, projectiles):
        self.inRange = False
        enemy_closest = []

        for enemy in enemies:
            if enemy.dying or enemy.dead or enemy.reached_end:
                continue
            x = enemy.x
            y = enemy.y
            dis = math.sqrt((self.x - x)**2 + (self.y - y)**2)
            if dis < self.range:
                self.inRange = True
                enemy_closest.append(enemy)
        # Sortowanie wedlug priorytetu celowania
        if self.target_priority == "first":
            enemy_closest.sort(key=lambda x: (x.path_pos, x.dis), reverse=True)
        elif self.target_priority == "last":
            enemy_closest.sort(key=lambda x: (x.path_pos, x.dis))
        elif self.target_priority == "strong":
            enemy_closest.sort(key=lambda x: x.max_health, reverse=True)
        elif self.target_priority == "weak":
            enemy_closest.sort(key=lambda x: x.max_health)
        # Celuj we wroga najbliżej bazy (najdalszy na ścieżce).
        
        if len(enemy_closest) > 0:            
            first_enemy = enemy_closest[0]
            # Rapid Fire: 2x szybkosc ataku
            cooldown = 0.5 if getattr(self, '_rapid_fire', False) and self.ability_active > 0 else 1.0
            if time.time() - self.timer >= cooldown:
                self.timer = time.time()
                sound_2.play()
                # Meteor: 3x obrazen, duzy splash
                dmg = self.damage
                splash = getattr(self, 'splash_radius', 0)
                if getattr(self, '_meteor_ready', False):
                    dmg = self.damage * 3
                    splash = 120
                    self._meteor_ready = False
                # Pocisk leci do wroga zamiast natychmiastowego hita.
                projectiles.append(Projectile(
                    self.x, self.y - 30,
                    self.archer_imgs[0], first_enemy, dmg,
                    splash_radius=splash,
                    slow_on_hit=getattr(self, 'slow_on_hit', False),
                    damage_type=getattr(self, 'damage_type', 'physical')))
                  
            # Lucznik zwraca sie w strone wroga (wczesniej byl odwrocony).
            if first_enemy.x < self.x and not self.facing_left:
                self.facing_left = True
                for x, img in enumerate(self.archer_imgs):
                    self.archer_imgs[x] = pygame.transform.flip(img, True, False)
            elif first_enemy.x > self.x and self.facing_left:
                self.facing_left = False
                for x, img in enumerate(self.archer_imgs):
                    self.archer_imgs[x] = pygame.transform.flip(img, True, False)
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
    buy_price = 200
    ability_name = "Frost Nova"
    ability_desc = "Spowalnia wszystkich wrogow w zasiegu"
    def __init__(self, x, y):
        super().__init__(x, y)
        self.tower_imgs = tower_imgs2[:]
        self.archer_imgs = archer_imgs2[:]
        self.archer_count = 0
        self.range = 125
        self.inRange = False
        self.facing_left = False
        self.timer = time.time()      
        self.damage = 3
        self.slow_on_hit = True  # Spowalnia trafionych wrogow
        self._setup_menu()
        self.name = "metalTower"

    def activate_ability(self, enemies, projectiles):
        """Frost Nova: spowalnia wszystkich wrogow w zasiegu na 4s."""
        if self.ability_cooldown > 0:
            return False
        self.ability_cooldown = self.ability_max_cooldown
        import math
        for en in enemies:
            if en.dying or en.dead or en.reached_end:
                continue
            dist = math.sqrt((en.x - self.x)**2 + (en.y - self.y)**2)
            if dist < self.range * 1.5:
                en.apply_slow(240)  # 4s
        return True
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
    buy_price = 300
    ability_name = "Golden Touch"
    ability_desc = "Podwojna kasa za zabojstwa przez 10s"
    def __init__(self, x, y):
        super().__init__(x, y)
        self.tower_imgs = tower_imgs3[:]
        self.archer_imgs = archer_imgs3[:]
        self.archer_count = 0
        self.range = 125
        self.inRange = False
        self.facing_left = False
        self.timer = time.time()      
        self.damage = 5
        self._setup_menu()
        self.name = "goldenTower"

    def activate_ability(self, enemies, projectiles):
        """Golden Touch: podwojna kasa za zabojstwa przez 10s (globalnie)."""
        if self.ability_cooldown > 0:
            return False
        self.ability_cooldown = self.ability_max_cooldown
        # Ustaw flage globalna w grze - obsluga w game.py
        self._gold_rush = True
        self.ability_active = 600  # 10s
        return True  
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
    buy_price = 400
    ability_name = "Meteor"
    ability_desc = "Potężny pocisk 3x obrażenia, duży splash"
    damage_type = "fire"
    def __init__(self, x, y):
        super().__init__(x, y)
        self.tower_imgs = tower_imgs4[:]
        self.archer_imgs = archer_imgs4[:]
        self.archer_count = 0
        self.range = 125
        self.inRange = False
        self.facing_left = False
        self.timer = time.time()      
        self.damage = 8
        self.splash_radius = 60  # Obrazenia obszarowe
        self._setup_menu()
        self.name = "fireTower"

    def activate_ability(self, enemies, projectiles):
        """Meteor: nastepny pocisk zadaje 3x obrazen z duzym splash."""
        if self.ability_cooldown > 0:
            return False
        self.ability_cooldown = self.ability_max_cooldown
        self._meteor_ready = True
        return True
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
    buy_price = 500
    ability_name = "Armageddon"
    ability_desc = "Obrażenia dla WSZYSTKICH wrogów na mapie"
    damage_type = "fire"
    def __init__(self, x, y):
        super().__init__(x, y)
        self.tower_imgs = tower_imgs5[:]
        self.archer_imgs = archer_imgs5[:]
        self.archer_count = 0
        self.range = 125
        self.inRange = False
        self.facing_left = False
        self.timer = time.time()      
        self.damage = 10
        self.splash_radius = 80  # Wieksze obrazenia obszarowe
        self._setup_menu()
        self.name = "blazeTower"

    def activate_ability(self, enemies, projectiles):
        """Armageddon: 30 obrazen dla wszystkich wrogow na mapie."""
        if self.ability_cooldown > 0:
            return False
        self.ability_cooldown = self.ability_max_cooldown
        for en in enemies:
            if not en.dying and not en.dead and not en.reached_end:
                en.hit(30)
        return True