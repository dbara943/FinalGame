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
        self.attack_imgs = []  # Animacja ataku na baze
        self.attacking = False
        self.attack_count = 0
        self.flipped = False
        self.reached_end = False
        self._imgs_copied = False
        self.dying = False
        self.dead = False
        self.die_count = 0
        self.hurt_timer = 0
        self.slow_timer = 0
        self.base_velocity = 3
        self.flash_timer = 0  # V1: bialy blysk przy trafieniu
        self.last_hit_by = None  # R5: wieza ktora zadala ostatni cios

    def draw(self, win):
        # Czyste rysowanie - bez zmiany stanu (stan zmienia update()).
        if self.img is None:
            return
        # V5: miekki cien pod wrogiem (gradientowy, nie twarda elipsa)
        self._draw_soft_shadow(win, self.x, self.y + 18, 50, 14)
        img_to_draw = self.img
        # V1: hit flash - biala sylwetka (maska, nie prostokat)
        if self.flash_timer > 0:
            if not hasattr(self, '_flash_cache') or self._flash_cache.get('img') is not self.img:
                mask = pygame.mask.from_surface(self.img)
                flash_surf = mask.to_surface(setcolor=(255, 255, 255, 200),
                                             unsetcolor=(0, 0, 0, 0))
                self._flash_cache = {'img': self.img, 'surf': flash_surf}
            img_to_draw = self._flash_cache['surf']
        # V2: wskaznik spowolnienia - subtelne krysztalki lodu u stop (nie zaslania modelu)
        if self.slow_timer > 0:
            # Male niebieskie romby u podstawy wroga
            for ox, oy in [(-12, 12), (0, 16), (12, 12)]:
                pts = [(self.x + ox, self.y + oy - 6),
                       (self.x + ox + 5, self.y + oy),
                       (self.x + ox, self.y + oy + 6),
                       (self.x + ox - 5, self.y + oy)]
                pygame.draw.polygon(win, (150, 210, 255, 200), pts)
                pygame.draw.polygon(win, (220, 240, 255, 255), pts, 1)
        win.blit(img_to_draw, (self.x - img_to_draw.get_width()/2, self.y - img_to_draw.get_height()/2 - 35))
        if not self.dying:
            self.draw_health_bar(win)

    def _draw_soft_shadow(self, win, cx, cy, w, h):
        """Miekki cien z gradientem (3 warstwy)."""
        for i, (alpha, scale) in enumerate([(30, 1.0), (25, 0.8), (20, 0.6)]):
            sw, sh = int(w * scale), int(h * scale)
            shadow = pygame.Surface((sw, sh), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha), shadow.get_rect())
            win.blit(shadow, (cx - sw // 2, cy - sh // 2))

    def update(self):
        """Logika wroga: animacje, ruch, timery. Wywolywane z Game.update_game_logic()."""
        if self.flash_timer > 0:
            self.flash_timer -= 1
        # Atak na baze - animacja ataku zamiast natychmiastowego znikniecia
        if self.attacking:
            if self.attack_imgs:
                self.attack_count += 1
                idx = min(self.attack_count // 4, len(self.attack_imgs) - 1)
                self.img = self.attack_imgs[idx]
                if self.attack_count >= len(self.attack_imgs) * 4:
                    self.reached_end = True
                    self.attacking = False
            else:
                self.reached_end = True
                self.attacking = False
            return
        if self.dying:
            if self.die_count < len(self.die_imgs):
                self.img = self.die_imgs[self.die_count]
                self.die_count += 1
            else:
                self.dead = True
            return
        if self.hurt_timer > 0 and self.hurt_imgs:
            self.img = self.hurt_imgs[(6 - self.hurt_timer) % len(self.hurt_imgs)]
            self.hurt_timer -= 1
        else:
            # Animacja co 4 ticki (nie co klatke - wczesniej bylo za szybko)
            self._anim_tick = getattr(self, '_anim_tick', 0) + 1
            if self._anim_tick >= 4:
                self._anim_tick = 0
                self.animation_count += 1
                if self.animation_count >= len(self.imgs):
                    self.animation_count = 0
            if self.imgs:
                self.img = self.imgs[self.animation_count]
        if not self.dying:
            self.move()
        
    def draw_health_bar(self, win):
        # Nowoczesny pasek: zaokraglone tlo, elegancka zielen/czerwien
        bar_w, bar_h = 50, 8
        x = self.x - bar_w / 2
        y = self.y - 70
        ratio = max(0.0, min(1.0, self.health / self.max_health)) if self.max_health > 0 else 0
        # Tlo (ciemne, zaokraglone)
        bg = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (20, 20, 20, 200), bg.get_rect(), border_radius=4)
        win.blit(bg, (x, y))
        # Wypelnienie: zielen -> zolc -> czerwien w zaleznosci od HP
        fill_w = int(bar_w * ratio)
        if fill_w > 0:
            if ratio > 0.6:
                color = (76, 175, 80)      # elegancka zielen
            elif ratio > 0.3:
                color = (255, 193, 7)     # bursztyn
            else:
                color = (244, 67, 54)     # nowoczesna czerwien
            fg = pygame.Surface((fill_w, bar_h), pygame.SRCALPHA)
            pygame.draw.rect(fg, color, fg.get_rect(), border_radius=4)
            win.blit(fg, (x, y))

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
               # Koniec sciezki - atak na baze (animacja), nie natychmiastowe znikniecie
               if not self.attacking and not self.reached_end:
                   self.attacking = True
                   self.attack_count = 0
           else:
               self.path_pos += 1
       
    def hit(self, damage):
        if self.dying or self.dead:
            return False
        self.health -= damage
        self.hurt_timer = 6
        self.flash_timer = 4  # V1: blysk przy trafieniu
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
    