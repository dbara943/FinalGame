import pygame
import math
import os
import random

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
        self.path = [
                     (322, 658), (362, 634), (445, 601), (542, 573),
                     (719, 556), (897, 535), (1011, 511), (1028, 490),
                     (1011, 478), (975, 473), (878, 459), (782, 444),
                     (684, 432), (598, 422), (511, 410), (425, 402),
                     (354, 393), (275, 379)]
        # Precompute kierunkow segmentow (wydajnosc) - bez sqrt co tick
        self._path_dirs = []
        for i in range(len(self.path) - 1):
            x1, y1 = self.path[i]
            x2, y2 = self.path[i + 1]
            dx, dy = x2 - x1, y2 - y1
            length = math.sqrt(dx*dx + dy*dy)
            if length == 0:
                self._path_dirs.append((0, 0))
            else:
                self._path_dirs.append((dx / length, dy / length))
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
        self.elite = False  # 6: elitarny wrog (3x HP, 5x zlota)

    def _apply_gold_filter(self, img):
        """Zloty filtr (grayscale -> zloto) - jak posag ze zlota."""
        gray = pygame.transform.grayscale(img)
        tinted = gray.copy()
        gold = pygame.Surface(img.get_size())
        gold.fill((255, 190, 50))
        tinted.blit(gold, (0, 0), special_flags=pygame.BLEND_MULT)
        shine = pygame.Surface(img.get_size())
        shine.fill((40, 25, 0))
        tinted.blit(shine, (0, 0), special_flags=pygame.BLEND_ADD)
        return tinted

    def make_elite(self):
        """6: Zamienia w elitarnego (3x HP, 5x zlota, wiekszy zlociutki model)."""
        if not self.elite:
            self.elite = True
            self.max_health *= 3
            self.health = self.max_health
            self.money *= 5
            # Kopia list (nie modyfikuj wspoldzielonych!)
            self.imgs = self.imgs[:]
            self.die_imgs = self.die_imgs[:]
            self.hurt_imgs = self.hurt_imgs[:]
            self._imgs_copied = True
            # Skalowanie 1.25x + zloty filtr NA STALE (pre-render, nie co klatke)
            for lst in (self.imgs, self.die_imgs, self.hurt_imgs):
                for i, img in enumerate(lst):
                    w, h = img.get_size()
                    scaled = pygame.transform.scale(img, (int(w * 1.25), int(h * 1.25)))
                    lst[i] = self._apply_gold_filter(scaled)

    def draw(self, win):
        # Czyste rysowanie - bez zmiany stanu (stan zmienia update()).
        if self.img is None:
            return
        # Culling: nie rysuj poza ekranem (wydajnosc)
        if self.x < -80 or self.x > 1204 or self.y < -80 or self.y > 800:
            return
        # 6: elitarni maja juz zloty filtr nalozony w make_elite() (pre-render)
        # _gold_marked (Golden Touch): tymczasowy tint
        is_golden = getattr(self, '_gold_marked', False) and not self.elite
        if is_golden:
            _gc = getattr(self, '_gold_cache', None)
            if not _gc or _gc.get('img') is not self.img:
                # Prawdziwy filtr zlota: grayscale -> pokoloruj na zloto
                # (jak posag ze zlota, nie tylko tint)
                gray = pygame.transform.grayscale(self.img)
                tinted = gray.copy()
                # Zlota paleta: ciemne -> braz, jasne -> jasne zloto
                gold = pygame.Surface(self.img.get_size())
                gold.fill((255, 190, 50))
                tinted.blit(gold, (0, 0), special_flags=pygame.BLEND_MULT)
                # Polysk
                shine = pygame.Surface(self.img.get_size())
                shine.fill((40, 25, 0))
                tinted.blit(shine, (0, 0), special_flags=pygame.BLEND_ADD)
                self._gold_cache = {'img': self.img, 'surf': tinted}
            img_to_draw = self._gold_cache['surf']
        else:
            img_to_draw = self.img
        # Slad lodu za spowolnionymi
        if self.slow_timer > 0 and random.random() < 0.2:
            # (rysowane przez game.py particles)
            pass
        # V5: cien usuniety na prosbe gracza
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
        win.blit(img_to_draw, (self.x - img_to_draw.get_width()/2, self.y - img_to_draw.get_height()/2))
        # Pasek HP tylko gdy ranny (wydajnosc) - pelne HP = brak paska
        if not self.dying and self.health < self.max_health:
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
            # A7: kurz za szybkimi wrogami (flaga do game.py)
            if self.velocity >= 4.0 and random.random() < 0.3:
                self._dust = True
        
    def draw_health_bar(self, win):
        # Nowoczesny pasek: zaokraglone tlo, elegancka zielen/czerwien
        bar_w, bar_h = 50, 8
        x = self.x - bar_w / 2
        y = self.y - 40
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
       # Kierunek z precompute (wydajnosc) - bez sqrt co tick
       if self.path_pos < len(self._path_dirs):
           dirn = self._path_dirs[self.path_pos]
       else:
           dirn = (0, 0)

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
    