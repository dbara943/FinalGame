import pygame
import math
import os

def load_anim(folder_num, anim_name, size=(64, 64)):
    """Laduje klatki animacji wroga (np. 'die', 'hurt').
    Pliki: images/enemies/<folder>/<folder>_enemies_1_<anim>_0XX.png"""
    frames = []
    for x in range(20):
        fname = "%d_enemies_1_%s_0%02d.png" % (folder_num, anim_name, x)
        path = os.path.join("images/enemies", str(folder_num), fname)
        if os.path.exists(path):
            frames.append(pygame.transform.scale(pygame.image.load(path), size))
    return frames

class Enemy:    
    def __init__(self):
        self.width = 64
        self.height = 64
        self.animation_count = 0
        self.health = 1
        self.max_health = 0
        self.velocity = 3
        # Punkty dobrane do namalowanej drogi: dolna droga w prawo,
        # zakret w gore, gorna droga z powrotem do bazy.
        self.path = [(300, 600), (325, 640), (340, 635), (380, 620), (440, 600),
                     (535, 575), (700, 560), (850, 543), (980, 512),
                     (1040, 462), (1000, 415), (800, 412), (600, 414),
                     (400, 410), (300, 375)]
        self.x = self.path[0][0]
        self.y = self.path[0][1]        
        self.img = None
        self.dis = 0
        self.path_pos = 0
        self.move_count = 0
        self.move_dis = 0
        self.imgs = []
        self.die_imgs = []
        self.hurt_imgs = []
        self.flipped = False
        self.reached_end = False
        self._imgs_copied = False
        self.dying = False
        self.dead = False
        self.die_count = 0
        self.hurt_timer = 0
        self.slow_timer = 0
        self.base_velocity = 3
    def draw(self, win):
        if self.dying:
            if self.die_count < len(self.die_imgs):
                self.img = self.die_imgs[self.die_count]
                self.die_count += 1
            else:
                self.dead = True
                return
        elif self.hurt_timer > 0 and self.hurt_imgs:
            self.img = self.hurt_imgs[(6 - self.hurt_timer) % len(self.hurt_imgs)]
            self.hurt_timer -= 1
        else:
            self.img = self.imgs[self.animation_count]
            self.animation_count += 1
            if self.animation_count >= len(self.imgs):
                self.animation_count = 0
                 
        win.blit(self.img, (self.x - self.img.get_width()/2, self.y - self.img.get_height()/2 - 35))
        if not self.dying:
            self.draw_health_bar(win)
            self.move()
        
    def draw_health_bar(self, win):
        length = 50
        move_by = round(length / self.max_health)
        health_bar = move_by * self.health
        
        pygame.draw.rect(win, (255,0,0), (self.x - 30, self.y-70, length, 10), 0)
        pygame.draw.rect(win, (0,255,0), (self.x - 30, self.y-70, health_bar, 10), 0)

    def collide(self, X, Y):
        if X <= self.x + self.width and X >= self.x:
            if Y <= self.y + self.height and Y >= self.y:
                return True
        return False
    
    def move(self):
       if self.reached_end:
           return
       # Kazdy wrog dostaje wlasna kopie obrazkow - wczesniej wszystkie
       # instancje tego samego typu dzielily jedna liste i odwracanie
       # jednego odwracalo wszystkie.
       if not self._imgs_copied:
           self.imgs = self.imgs[:]
           self.die_imgs = self.die_imgs[:]
           self.hurt_imgs = self.hurt_imgs[:]
           self._imgs_copied = True
       x1, y1 = self.path[self.path_pos]
       if self.path_pos + 1 >= len(self.path):
           x2, y2 = self.path[self.path_pos]
       else:
           x2, y2 = self.path[self.path_pos + 1]

       dx, dy = x2 - x1, y2 - y1
       length = math.sqrt(dx**2 + dy**2)
       if length == 0:
           dirn = (0, 0)
       else:
           dirn = (dx / length, dy / length)

       if dirn[0] < 0 and not(self.flipped):
           self.flipped = True
           for x, img in enumerate(self.imgs):
               self.imgs[x] = pygame.transform.flip(img, True, False)
           for x, img in enumerate(self.die_imgs):
               self.die_imgs[x] = pygame.transform.flip(img, True, False)
           for x, img in enumerate(self.hurt_imgs):
               self.hurt_imgs[x] = pygame.transform.flip(img, True, False)
       elif dirn[0] > 0 and self.flipped:
           self.flipped = False
           for x, img in enumerate(self.imgs):
               self.imgs[x] = pygame.transform.flip(img, True, False)
           for x, img in enumerate(self.die_imgs):
               self.die_imgs[x] = pygame.transform.flip(img, True, False)
           for x, img in enumerate(self.hurt_imgs):
               self.hurt_imgs[x] = pygame.transform.flip(img, True, False)

       # Predkosc wroga (kiedys atrybut velocity byl ignorowany).
       # Dzielimy przez 3, zeby zachowac dotychczasowe tempo gry.
       # Spowolnienie (slow) zmniejsza predkosc o polowe.
       current_vel = self.velocity
       if self.slow_timer > 0:
           current_vel = self.velocity * 0.5
           self.slow_timer -= 1
       step_len = current_vel / 3.0
       dist_to_target = math.sqrt((x2 - self.x)**2 + (y2 - self.y)**2)
       step_len = min(step_len, dist_to_target)
       self.x += dirn[0] * step_len
       self.y += dirn[1] * step_len
       self.dis += step_len

       # Dotarl do punktu docelowego?
       if dist_to_target <= self.velocity / 3.0 + 1:
           if self.path_pos + 1 >= len(self.path):
               self.reached_end = True
           else:
               self.path_pos += 1
       
    def hit(self, damage):
        if self.dying or self.dead:
            return False
        self.health -= damage
        self.hurt_timer = 6
        if self.health <= 0:
            self.dying = True
            self.die_count = 0
            return True
        return False

    def apply_slow(self, duration=60):
        """Naklada spowolnienie na wroga (duration w klatkach)."""
        if not self.dying and not self.dead:
            # Impostor jest odporny na spowolnienie
            if getattr(self, 'slow_immune', False):
                return
            self.slow_timer = duration

    def get_damage_mult(self, damage_type):
        """Mnoznik obrazen uwzgledniajacy opornosci (R13)."""
        resistances = getattr(self, 'resistances', {})
        return resistances.get(damage_type, 1.0)
    