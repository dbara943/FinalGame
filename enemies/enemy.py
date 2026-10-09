import pygame
import math

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
        self.flipped = False
        self.reached_end = False
        self._imgs_copied = False
    def draw(self, win):
        self.img = self.imgs[self.animation_count]
        self.animation_count += 1

        if self.animation_count >= len(self.imgs):
            self.animation_count = 0
                 
        win.blit(self.img, (self.x - self.img.get_width()/2, self.y - self.img.get_height()/2 - 35))
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
       elif dirn[0] > 0 and self.flipped:
           self.flipped = False
           for x, img in enumerate(self.imgs):
               self.imgs[x] = pygame.transform.flip(img, True, False)

       # Predkosc wroga (kiedys atrybut velocity byl ignorowany).
       # Dzielimy przez 3, zeby zachowac dotychczasowe tempo gry.
       step_len = self.velocity / 3.0
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
        self.health -= damage
        if self.health <= 0:
            return True
        return False
    