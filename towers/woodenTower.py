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
        """Rapid Fire: wystrzeliwuje serie 3 pociskow naraz."""
        if self.ability_cooldown > 0:
            return False
        self.ability_cooldown = self.ability_max_cooldown
        # Znajdz cel
        target = self.current_target
        if target is None or target.dying or target.dead:
            # Szukaj dowolnego wroga w zasiegu
            for en in enemies:
                if not en.dying and not en.dead and not en.reached_end:
                    if math.hypot(en.x - self.x, en.y - self.y) < self.range:
                        target = en
                        break
        if target:
            for i in range(3):
                img = Projectile.make_special_img((255, 220, 80), 20)
                projectiles.append(Projectile(
                    self.x + (i-1)*10, self.y - 30,
                    img, target, self.damage,
                    speed=14, source_tower=self, special="rapid"))
        return True
        
    def get_upgrade_cost(self):
        return self.menu.get_item_cost()

    def draw(self, win):
        super().draw_radius(win)
        super().draw(win)  
        
        # Kierunkowa animacja przeladowania (proca):
        # - pocisk widoczny na wiezy gdy gotowa
        # - celuje w strone wroga (offset w kierunku celu)
        # - po strzale znika (pusta), wraca podczas reloadu
        tgt = getattr(self, 'current_target', None)
        reloading = self.attack_cooldown > 0
        
        if reloading and self.attack_cooldown > 45:
            # Pierwsze 15 tickow po strzale: pusta wieza
            return
        
        if self.inRange and not self.moving:     
            self.archer_count += 1
            if self.archer_count >= len(self.archer_imgs) * 10:
                self.archer_count = 0
        else:
            self.archer_count = 0
        
        proj_img = self.archer_imgs[self.archer_count // 10]
        
        # Pozycja pocisku: celowanie w strone wroga
        px, py = self.x, self.y - 35
        if tgt is not None and not tgt.dying and not tgt.dead:
            # Kat do celu
            dx = tgt.x - self.x
            dy = tgt.y - (self.y - 35)
            dist = math.hypot(dx, dy)
            if dist > 0:
                # Offset w kierunku celu (jak napieta proca)
                pull = 12 if not reloading else 6
                px = self.x + (dx / dist) * pull
                py = (self.y - 35) + (dy / dist) * pull
                # Obrot pocisku w kierunku celu
                angle = math.degrees(math.atan2(-dy, dx))
                proj_img = pygame.transform.rotate(proj_img, angle)
        
        # Animacja ladowania: pocisk rosnie podczas reloadu
        if reloading:
            progress = 1.0 - (self.attack_cooldown / 60.0)
            scale = 0.5 + 0.5 * progress
            w = int(proj_img.get_width() * scale)
            h = int(proj_img.get_height() * scale)
            if w > 0 and h > 0:
                proj_img = pygame.transform.scale(proj_img, (w, h))
        
        win.blit(proj_img, (px - proj_img.get_width() // 2, py - proj_img.get_height() // 2))       
        
    def change_range(self, r):
        self.range = r

    def attack(self, enemies, projectiles):
        self.inRange = False
        self.current_target = None
        enemy_closest = []
        shot_fired = False

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
            self.current_target = first_enemy  # R3: zapamietaj cel
            cooldown_ticks = 60  # 1s
            if self.attack_cooldown <= 0:
                self.attack_cooldown = cooldown_ticks
                sound_2.play()
                dmg = self.damage
                splash = getattr(self, 'splash_radius', 0)
                # Pocisk leci do wroga zamiast natychmiastowego hita.
                projectiles.append(Projectile(
                    self.x, self.y - 30,
                    self.archer_imgs[0], first_enemy, dmg,
                    splash_radius=splash,
                    slow_on_hit=getattr(self, 'slow_on_hit', False),
                    damage_type=getattr(self, 'damage_type', 'physical'),
                    source_tower=self))
                shot_fired = True
                  
            # Lucznik zwraca sie w strone wroga (wczesniej byl odwrocony).
            if first_enemy.x < self.x and not self.facing_left:
                self.facing_left = True
                for x, img in enumerate(self.archer_imgs):
                    self.archer_imgs[x] = pygame.transform.flip(img, True, False)
            elif first_enemy.x > self.x and self.facing_left:
                self.facing_left = False
                for x, img in enumerate(self.archer_imgs):
                    self.archer_imgs[x] = pygame.transform.flip(img, True, False)
        return shot_fired
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
        """Frost Nova: wystrzeliwuje lodowy pocisk - spowalnia wszystkich w zasiegu."""
        if self.ability_cooldown > 0:
            return False
        self.ability_cooldown = self.ability_max_cooldown
        target = self.current_target
        if target is None or target.dying or target.dead:
            for en in enemies:
                if not en.dying and not en.dead and not en.reached_end:
                    if math.hypot(en.x - self.x, en.y - self.y) < self.range:
                        target = en
                        break
        if target:
            img = Projectile.make_special_img((120, 200, 255), 40)
            projectiles.append(Projectile(
                self.x, self.y - 30, img, target, 5,
                speed=10, source_tower=self, special="frost_nova"))
            return True
        return False
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
        """Golden Touch: wystrzeliwuje zlote pociski - oznaczaja wrogow (2x kasa)."""
        if self.ability_cooldown > 0:
            return False
        self.ability_cooldown = self.ability_max_cooldown
        # Oznacza do 5 wrogow w zasiegu zlotymi pociskami
        marked = 0
        for en in enemies:
            if marked >= 5:
                break
            if en.dying or en.dead or en.reached_end:
                continue
            if math.hypot(en.x - self.x, en.y - self.y) < self.range * 1.5:
                img = Projectile.make_special_img((255, 215, 0), 24)
                projectiles.append(Projectile(
                    self.x, self.y - 30, img, en, self.damage,
                    speed=12, source_tower=self, special="golden"))
                marked += 1
        return marked > 0  
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
        """Meteor: wystrzeliwuje ogromny meteor (3x obrazen, duzy splash)."""
        if self.ability_cooldown > 0:
            return False
        self.ability_cooldown = self.ability_max_cooldown
        target = self.current_target
        if target is None or target.dying or target.dead:
            # Najsilniejszy wrog
            best = None
            best_hp = 0
            for en in enemies:
                if not en.dying and not en.dead and not en.reached_end:
                    if en.max_health > best_hp:
                        best_hp = en.max_health
                        best = en
            target = best
        if target:
            img = Projectile.make_special_img((255, 120, 40), 48)
            projectiles.append(Projectile(
                self.x, self.y - 30, img, target, self.damage,
                speed=8, source_tower=self, special="meteor"))
            return True
        return False
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
        """Armageddon: wystrzeliwuje pocisk zaglady - rani wszystkich wrogow."""
        if self.ability_cooldown > 0:
            return False
        self.ability_cooldown = self.ability_max_cooldown
        # Cel: srodek mapy (pocisk eksploduje i rani wszystkich)
        target = self.current_target
        if target is None or target.dying or target.dead:
            for en in enemies:
                if not en.dying and not en.dead and not en.reached_end:
                    target = en
                    break
        if target:
            img = Projectile.make_special_img((200, 80, 255), 56)
            projectiles.append(Projectile(
                self.x, self.y - 30, img, target, 30,
                speed=7, source_tower=self, special="armageddon"))
            return True
        return False