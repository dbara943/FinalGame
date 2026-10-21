import pygame
import math
import os
import random

# Pomost (drewniany, przy statku): Reinforced Docks spowalnia wrogow 15%
# TYLKO w tym prostokacie (x, y, w, h). Poza nim predkosc normalna.
_PIER_RECT = (240, 600, 340, 120)

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
        self._docks_slow = False  # Reinforced Docks: 15% wolniej, tylko na pomoście
        # Punkty dobrane do namalowanej drogi: dolna droga w prawo,
        # zakret w gore, gorna droga z powrotem do bazy.
        self.path = [
                     (322, 658), (425, 630), (505, 591), (588, 581),
                     (696, 570), (792, 558), (890, 546), (953, 536),
                     (1034, 523), (1049, 497), (1021, 488), (944, 477),
                     (838, 467), (724, 450), (626, 438), (540, 426),
                     (448, 414), (359, 399), (264, 387), (250, 351)]
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
        # Statusy DoT (paczka 26): trucizna (kolce / strzaly Clyde'a)
        # i podpalenie (strzaly Bonnie). Tickowanie w game.py
        # (Game._tick_statuses) - tu tylko stan + grafika.
        self._poison_t = 0        # ticki pozostalej trucizny
        self._poison_dps = 0.0    # obrazenia na sekunde
        self._burn_t = 0          # ticki pozostalego podpalenia
        self._burn_dps = 0.0      # obrazenia na sekunde
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

    def apply_golden(self):
        """Golden Touch: zamienia sprite'y na zlote odmiany (TEN SAM rozmiar, bez skalowania).
        Wrog jest wtedy faktycznie widoczny jako zloto. Zloto za niego x2 (flaga _gold_marked)."""
        if getattr(self, '_gold_applied', False) or self.elite:
            return
        self._gold_applied = True
        # Kopie list (nie modyfikuj wspoldzielonych!)
        self.imgs = self.imgs[:]
        self.die_imgs = self.die_imgs[:]
        self.hurt_imgs = self.hurt_imgs[:]
        if self.attack_imgs:
            self.attack_imgs = self.attack_imgs[:]
        for lst in (self.imgs, self.die_imgs, self.hurt_imgs, self.attack_imgs):
            for i, img in enumerate(lst):
                lst[i] = self._apply_gold_filter(img)

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
            if self.attack_imgs:
                self.attack_imgs = self.attack_imgs[:]
            self._imgs_copied = True
            # Skalowanie 1.25x + zloty filtr NA STALE (pre-render, nie co klatke).
            # attack_imgs TEZ - bez tego elita przy ataku na budynek wracala
            # do zwyklych kolorow (klatki ataku nie mialy zlotego filtra).
            for lst in (self.imgs, self.die_imgs, self.hurt_imgs, self.attack_imgs):
                for i, img in enumerate(lst):
                    w, h = img.get_size()
                    scaled = pygame.transform.scale(img, (int(w * 1.25), int(h * 1.25)))
                    lst[i] = self._apply_gold_filter(scaled)

    def get_hitbox(self):
        """Prostokat kolizji na podstawie faktycznego rozmiaru sprite'a.
        Wieceksze sprite'y = wiekszy hitbox = latwiej trafic.
        Dopasowany do rysowania: blit(img, (x - w/2, y - h/2 - 35))."""
        img = self.img
        if img is None:
            w, h = 64, 64
        else:
            w = img.get_width()
            h = img.get_height()
        return pygame.Rect(self.x - w / 2, self.y - h / 2 - 35, w, h)

    def hitbox_in_radius(self, cx, cy, radius):
        """Czy hitbox sprite'a dotyka okregu o srodku (cx, cy) i promieniu radius."""
        hb = self.get_hitbox()
        nx = hb.left if cx < hb.left else (hb.right if cx > hb.right else cx)
        ny = hb.top if cy < hb.top else (hb.bottom if cy > hb.bottom else cy)
        dx, dy = cx - nx, cy - ny
        return dx * dx + dy * dy < radius * radius

    def draw(self, win):
        # Czyste rysowanie - bez zmiany stanu (stan zmienia update()).
        if self.img is None:
            return
        # Culling: nie rysuj poza ekranem (wydajnosc)
        if self.x < -80 or self.x > 1204 or self.y < -80 or self.y > 800:
            return
        # 6: elitarni maja juz zloty filtr nalozony w make_elite() (pre-render)
        # Golden Touch: sprite'y zamienione na zlote w apply_golden() (pre-render)
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
        # V2: wskaznik spowolnienia - usuniety na prosbe gracza
        _blit_x = self.x - img_to_draw.get_width()/2
        _blit_y = self.y - img_to_draw.get_height()/2 - 35
        win.blit(img_to_draw, (_blit_x, _blit_y))
        # Spowolnienie = wyrazna powloka lodu NA wrogu (polprzezroczysty
        # jasnoniebieski filtr w ksztalcie sylwetki + krysztalki lodu przy
        # stopach). Wrog zostaje w pelni widoczny i animowany - zadnego
        # "ducha" ani zamrozonej pozy. Cache per klatka animacji.
        if self.slow_timer > 0 and not self.dying and not self.dead and self.flash_timer <= 0:
            if not hasattr(self, '_ice_cache') or self._ice_cache.get('img') is not self.img:
                mask = pygame.mask.from_surface(self.img)
                ice_surf = mask.to_surface(setcolor=(165, 215, 255, 95),
                                           unsetcolor=(0, 0, 0, 0))
                self._ice_cache = {'img': self.img, 'surf': ice_surf}
            win.blit(self._ice_cache['surf'], (_blit_x, _blit_y))
            # Krysztalki lodu przy stopach (deterministyczne wg pozycji -
            # nie migocza losowo co klatke)
            _seed = int(self.x) // 7 + int(self.y) // 5
            for i in range(3):
                cx = int(self.x) - 14 + ((_seed * (i + 3)) % 28)
                cy = int(self.y) + 2 - ((_seed * (i + 1)) % 4)
                pygame.draw.line(win, (210, 240, 255), (cx, cy), (cx - 2, cy - 6), 2)
                pygame.draw.line(win, (210, 240, 255), (cx, cy), (cx + 2, cy - 6), 2)
        # Trucizna: zielona powloka na sylwetce + babelki unoszace sie
        # przy wrogu (deterministyczne wg pozycji i czasu gry - bez losowego
        # migotania; czas z licznika animacji wroga, rosnie co klatke update)
        if getattr(self, '_poison_t', 0) > 0 and not self.dying and not self.dead and self.flash_timer <= 0:
            if not hasattr(self, '_poison_cache') or self._poison_cache.get('img') is not self.img:
                mask = pygame.mask.from_surface(self.img)
                poison_surf = mask.to_surface(setcolor=(110, 230, 90, 85),
                                              unsetcolor=(0, 0, 0, 0))
                self._poison_cache = {'img': self.img, 'surf': poison_surf}
            win.blit(self._poison_cache['surf'], (_blit_x, _blit_y))
            _phase = int(getattr(self, 'dis', 0) * 2)
            for i in range(3):
                _bx = int(self.x) - 12 + ((int(self.x) // 5 + i * 11) % 24)
                _rise = (_phase * (1 + i) + i * 23) % 34
                _by = int(self.y) - 6 - _rise
                _br = 3 - _rise // 14
                if _br > 0:
                    pygame.draw.circle(win, (140, 255, 110), (_bx, _by), _br, 1)
        # Podpalenie: pomaranczowa powloka + migoczace plomienie przy stopach
        if getattr(self, '_burn_t', 0) > 0 and not self.dying and not self.dead and self.flash_timer <= 0:
            if not hasattr(self, '_burn_cache') or self._burn_cache.get('img') is not self.img:
                mask = pygame.mask.from_surface(self.img)
                burn_surf = mask.to_surface(setcolor=(255, 130, 40, 85),
                                            unsetcolor=(0, 0, 0, 0))
                self._burn_cache = {'img': self.img, 'surf': burn_surf}
            win.blit(self._burn_cache['surf'], (_blit_x, _blit_y))
            _phase = int(getattr(self, 'dis', 0) * 3)
            _seed = int(self.x) // 6 + int(self.y) // 4
            for i in range(3):
                _fx = int(self.x) - 13 + ((_seed * (i + 2) + _phase // 3) % 26)
                _fh = 7 + ((_phase // 2 + i * 5) % 6)
                pygame.draw.polygon(win, (255, 150, 50),
                                    [(_fx - 3, int(self.y) + 2), (_fx + 3, int(self.y) + 2),
                                     (_fx, int(self.y) + 2 - _fh)])
                pygame.draw.polygon(win, (255, 210, 110),
                                    [(_fx - 1, int(self.y) + 1), (_fx + 1, int(self.y) + 1),
                                     (_fx, int(self.y) + 1 - _fh // 2)])
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
        # Siatka bezpieczenstwa: HP <= 0 zawsze znaczy smierc, nawet gdy
        # obrazenia pominely hit() (bezposrednie odjecie HP) - inaczej taki
        # wrog chodzi w nieskonczonosc i nigdy nie placi zlota za zabojstwo.
        if self.health <= 0 and not self.dying and not self.dead:
            self.dying = True
            self.die_count = 0
        # Atak na baze - animacja ataku zamiast natychmiastowego znikniecia
        if self.attacking:
            # EASTER EGG (boss rewanzowy ze skoku na fale 10): zamiast jednego
            # uderzenia i znikniecia OBLEGA budynek - petla animacji ataku,
            # a co 100 tickow (1 s) stawia flage _building_hit, ktora Game
            # zamienia na -1 zycie. Zyje przy bramie, dopoki nie zginie -
            # wieze moga go normalnie celowac (nie ma reached_end).
            if getattr(self, "_building_attacker", False):
                self.attack_count += 1
                if self.attack_imgs:
                    idx = (self.attack_count // 4) % len(self.attack_imgs)
                    self.img = self.attack_imgs[idx]
                if self.attack_count % 100 == 0:
                    self._building_hit = True
                return
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
            # Animacja co 4 ticki (nie co klatke - wczesniej bylo za szybko).
            # Spowolniony wrog: krok animacji co 8 tickow - nogi ida w tempie
            # ruchu (polowa predkosci), zamiast slizgac sie jak bryla lodu.
            _step = 8 if self.slow_timer > 0 else 4
            self._anim_tick = getattr(self, '_anim_tick', 0) + 1
            if self._anim_tick >= _step:
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
       # Reinforced Docks: 15% wolniej, ale TYLKO na pomoście (x 240-580,
       # y 600-720 - drewniany pomost przy statku). Po zejsciu z pomostu
       # predkosc wraca do normalnej (flaga _docks_slow z gen_enemies).
       if getattr(self, "_docks_slow", False) and _PIER_RECT[0] <= self.x < _PIER_RECT[0] + _PIER_RECT[2] and _PIER_RECT[1] <= self.y < _PIER_RECT[1] + _PIER_RECT[3]:
           current_vel *= getattr(self, "_docks_factor", 0.85)  # Docks L1: 0.85, L2: 0.70
       # Deszcz / sztorm morski: brodzenie 10% wolniej (flaga _rain_slow
       # ustawiana co tick przez game.py; pogoda ma pomagac graczowi)
       if getattr(self, "_rain_slow", False):
           current_vel *= 0.9
       step_len = current_vel / 3.0
       dist_to_target = math.sqrt((x2 - self.x)**2 + (y2 - self.y)**2)
       step_len = min(step_len, dist_to_target)
       self.x += dirn[0] * step_len
       self.y += dirn[1] * step_len
       self.dis += step_len

       # Dotarl do punktu docelowego? Blisko punktu ALBO minal jego
       # plaszczyzne (projekcja na kierunek segmentu >= dlugosc segmentu).
       # Sam warunek odleglosci nie wystarczal: wrog z offsetem bocznym
       # (np. rozproszony spawn grupowy) idzie rownolegle do segmentu,
       # nigdy nie wchodzi w promien ~2px od punktu i w efekcie szedl
       # prosto przed siebie az za mape.
       _seg_len = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
       _proj = (self.x - x1) * dirn[0] + (self.y - y1) * dirn[1]
       if dist_to_target <= self.velocity / 3.0 + 1 or _proj >= _seg_len:
           if self.path_pos + 1 >= len(self.path):
               # Koniec sciezki - atak na baze (animacja), nie natychmiastowe znikniecie
               if not self.attacking and not self.reached_end:
                   self.attacking = True
                   self.attack_count = 0
           else:
               self.path_pos += 1
       
    def hit(self, damage, flash=True):
        if self.dying or self.dead:
            return False
        self.health -= damage
        if flash:
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
    