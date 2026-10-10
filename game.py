import pygame
import os
import math
from enemies.forkman import Forkman
from enemies.swordman import Swordman
from enemies.knight import Knight
from enemies.goblin import Goblin
from enemies.cyclop import Cyclop
from enemies.impostor import Impostor
from enemies.ogre import Ogre
from enemies.evilVillager import EvilVillager
from enemies.boss import Boss
from towers.woodenTower import (WoodenTower, MetalTower, GoldenTower, FireTower, BlazeTower,
                                sound_1 as tower_sound_1, sound_2 as tower_sound_2,
                                sound_3 as tower_sound_3, sound_4 as tower_sound_4,
                                sound_5 as tower_sound_5)
from ships.ship import Ship
from menu.menu import VerticalMenu
import time
import random
pygame.font.init()
pygame.display.set_caption('Island Defenders')

lives_img = pygame.image.load(os.path.join("images", "heart.png"))
money_img = pygame.image.load(os.path.join("images", "money.png"))
side_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "side_menu.png")), (375, 475))
t1_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "t1.png")), (30, 30))
t2_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "t2.png")), (30, 30))
t3_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "t3.png")), (30, 30))
t4_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "t4.png")), (30, 30))
t5_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "t5.png")), (30, 30))
wave_bg = pygame.transform.scale(pygame.image.load(os.path.join("images","wave.png")), (225, 75))

towers_names = ["woodenTower", "metalTower", "goldenTower", "fireTower", "blazeTower"]
waves = [
    [40,0,0,0,0,0,0,0],
    [30,10,0,0,0,0,0,0],
    [25,15,5,0,0,0,0,0],
    [15,15,10,5,0,0,0,0],
    [10,10,15,10,5,0,0,0],
    [5,5,15,10,10,5,0,0],
    [0,0,10,15,15,10,5,0],
    [0,0,0,10,15,15,10,5],
    [0,5,10,10,15,15,20,10],
    [0,0,0,0,0,0,0,0],  # Fala 10: sam boss
]
pygame.mixer.init()
music = pygame.mixer.music.load(os.path.join("sounds", "music.wav"))
sound_1 = pygame.mixer.Sound("sounds/1.wav")
sound_2 = pygame.mixer.Sound("sounds/2.wav")
sound_3 = pygame.mixer.Sound("sounds/3.wav")
sound_4 = pygame.mixer.Sound("sounds/4.wav")
sound_5 = pygame.mixer.Sound("sounds/5.wav")

class Game:
    def __init__(self, lives=20, money=200, sound=True):
        self.width = 1124
        self.height = 720
        self.win = pygame.display.set_mode((self.width, self.height), pygame.SCALED | pygame.FULLSCREEN)
        self.enemies = []
        self.towers = []
        self.projectiles = []
        self.lives = lives
        self.money = money
        self._start_lives = lives
        self._start_money = money
        self.sound = sound
        self.paused = False
        self.speed = 1  # 1x, 2x, 3x
        self.pause_btn_rect = pygame.Rect(self.width - 120, 10, 50, 44)
        self.speed_btn_rect = pygame.Rect(self.width - 60, 10, 50, 44)
        self._wave_start_lives = lives
        self.damage_numbers = []  # Latajace liczby obrazen [(x, y, tekst, timer)]
        if not sound:
            pygame.mixer.music.set_volume(0)
            for s in (sound_1, sound_2, sound_3, sound_4, sound_5,
                      tower_sound_1, tower_sound_2, tower_sound_3,
                      tower_sound_4, tower_sound_5):
                s.set_volume(0)
        self.bg = pygame.image.load(os.path.join("images", "bg_noship.png"))
        self.bg = pygame.transform.scale(self.bg, (self.width, self.height))
        self.ship = Ship(os.path.join("images", "ship.png"), dock_x=300, dock_y=665,
                         screen_w=self.width)
        self.ship.sail_in()
        self.last_wave_done = False
        self.timer = time.time()
        self.hud_font = pygame.font.SysFont("arial", 26, bold=True)
        self.selected_tower = None
        self.menu = VerticalMenu(self.width - side_img.get_width() + 350, 250, side_img)
        self.menu.add_btn(t1_img, "t1", 100)
        self.menu.add_btn(t2_img, "t2", 200)
        self.menu.add_btn(t3_img, "t3", 300)
        self.menu.add_btn(t4_img, "t4", 400)
        self.menu.add_btn(t5_img, "t5", 500)
        self.moving_object =  None
        self.wave = 0
        self.current_wave = waves[self.wave][:]
        self.won = False
        self.enemy_classes = [Forkman, Swordman, Knight, Goblin, Cyclop, Impostor, Ogre, EvilVillager]

    def gen_enemies(self):
        # Wrogowie desantuja sie tylko gdy statek jest w porcie.
        if self.won or self.ship.state != Ship.DOCKED:
            return
        if sum(self.current_wave) == 0:
            self.ship.sail_out()
            if self.wave + 1 >= len(waves):
                self.last_wave_done = True
            else:
                # Bonus za czysta fale (bez utraty zycia) + odsetki 5% od oszczednosci
                if hasattr(self, '_wave_start_lives') and self.lives == self._wave_start_lives:
                    bonus = 50 + self.wave * 10
                    self.money += bonus
                interest = int(self.money * 0.05)
                self.money += interest
                self.wave += 1
                self.money += self.wave * 100
                self.current_wave = waves[self.wave][:]
                self._wave_start_lives = self.lives
                # Boss na falach 4 i 8; fala 10 (ostatnia) to sam boss.
                if (self.wave + 1) % 4 == 0 and self.wave + 1 < 10:
                    self.enemies.append(Boss())
                elif self.wave + 1 == 10:
                    self.enemies.append(Boss())
        else:
            for i in range(len(self.current_wave)):
                if self.current_wave[i] != 0:
                    self.current_wave[i] -= 1
                    self.enemies.append(self.enemy_classes[i]())
                    break
    def run(self):
        if self.sound:
            pygame.mixer.music.play(loops=-1)
        run = True
        clock = pygame.time.Clock()
        while run:
            clock.tick(100)
            
            if time.time() - self.timer >= random.randrange(1, 5)/2:
                    self.timer = time.time()
                    self.gen_enemies()
            self.ship.update()
            if self.ship.state == Ship.AWAY and not self.won:
                if self.last_wave_done:
                    self.won = True
                else:
                    self.ship.sail_in()
            pos = pygame.mouse.get_pos()                 
            if self.moving_object:
                self.moving_object.move(pos[0], pos[1])
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                if event.type == pygame.KEYDOWN:
                    # T: zmiana priorytetu celowania wybranej wiezy
                    if event.key == pygame.K_t and self.selected_tower:
                        priorities = ["first", "strong", "weak", "last"]
                        idx = priorities.index(self.selected_tower.target_priority)
                        self.selected_tower.target_priority = priorities[(idx + 1) % 4]
                    # Q: aktywacja umiejetnosci wybranej wiezy
                    if event.key == pygame.K_q and self.selected_tower:
                        self.selected_tower.activate_ability(self.enemies, self.projectiles)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    # Przyciski pauzy i predkosci
                    if self.pause_btn_rect.collidepoint(pos):
                        self.paused = not self.paused
                        continue
                    if self.speed_btn_rect.collidepoint(pos):
                        self.speed = self.speed % 3 + 1  # 1->2->3->1
                        continue
                    if self.moving_object:
                        if self.moving_object.name in towers_names:
                            self.towers.append(self.moving_object)
                        self.moving_object.moving = False
                        self.moving_object = None      
                    else:
                        pass
                    side_menu_button = self.menu.get_clicked(pos[0], pos[1])
                    if side_menu_button:
                        cost = self.menu.get_item_cost(side_menu_button)
                        if self.money >= cost:
                            self.money -= cost
                            self.add_tower(side_menu_button)
                    
                    btn_clicked = None                    
                    if self.selected_tower:
                        btn_clicked = self.selected_tower.menu.get_clicked(pos[0], pos[1])
                        if btn_clicked:
                            if btn_clicked == "Upgrade":
                                cost = self.selected_tower.menu.get_item_cost()
                                if cost != "MAX" and self.money >= cost:
                                    self.money -= cost
                                    self.selected_tower.upgrade(cost)
                            elif btn_clicked == "Sell":
                                self.money += self.selected_tower.sell_value()
                                self.towers.remove(self.selected_tower)
                                self.selected_tower = None
                    if not (btn_clicked):    
                        for tw in self.towers:
                            if tw.click(pos[0], pos[1]):
                                tw.selected = True
                                self.selected_tower = tw
                            else:
                                tw.selected = False     
            # Logika gry (pauza pomija, predkosc powtarza)
            if not self.paused:
                for _ in range(self.speed):
                    self.update_game_logic()
                    if self.lives <= 0 or self.won:
                        break

            if self.lives <= 0:
                if self.show_end_screen(False):
                    self.reset_game()
                else:
                    run = False
            elif self.won:
                if self.show_end_screen(True):
                    self.reset_game()
                else:
                    run = False

            self.draw()
        pygame.quit()

    def reset_game(self):
        """Resetuje stan gry do poczatku (na potrzeby przycisku RESTART)."""
        self.enemies = []
        self.towers = []
        self.projectiles = []
        self.damage_numbers = []
        self.lives = self._start_lives
        self.money = self._start_money
        self.wave = 0
        self.current_wave = waves[self.wave][:]
        self.won = False
        self.last_wave_done = False
        self.paused = False
        self.speed = 1
        self.selected_tower = None
        self.moving_object = None
        self.timer = time.time()
        self._wave_start_lives = self._start_lives
        self.ship = Ship(os.path.join("images", "ship.png"), dock_x=300, dock_y=665,
                         screen_w=self.width)
        self.ship.sail_in()

    def update_game_logic(self):
        """Jedna iteracja logiki gry (ruch wrogow, ataki, pociski)."""
        # Aktualizacja cooldownow umiejetnosci
        for tw in self.towers:
            if tw.ability_cooldown > 0:
                tw.ability_cooldown -= 1
            if tw.ability_active > 0:
                tw.ability_active -= 1
                if tw.ability_active == 0:
                    tw._rapid_fire = False
                    tw._gold_rush = False
        to_del = []
        for en in self.enemies:
            if en.reached_end:
                to_del.append(en)
            elif en.dead:
                to_del.append(en)

        for d in to_del:
            if d.reached_end:
                sound_1.play()
                self.lives -= 1
            else:
                # Wrog zabity pociskiem - kasa za niego.
                # Golden Touch: podwojna kasa
                reward = d.money
                for tw in self.towers:
                    if getattr(tw, '_gold_rush', False) and tw.ability_active > 0:
                        reward = d.money * 2
                        break
                self.money += reward
            self.enemies.remove(d)

        for tw in self.towers:
            tw.attack(self.enemies, self.projectiles)

        # Pociski leca do celow; trafienie zadaje obrazenia.
        for proj in self.projectiles[:]:
            hit_enemy = proj.move()
            if hit_enemy is not None:
                # Splash damage: obrazenia obszarowe dla Fire/Blaze.
                if proj.splash_radius > 0:
                    for en in self.enemies:
                        if en.dying or en.dead or en.reached_end:
                            continue
                        dist = math.sqrt((en.x - hit_enemy.x)**2 + (en.y - hit_enemy.y)**2)
                        if dist < proj.splash_radius:
                            if en.hit(proj.damage):
                                tower_sound_3.play()
                            self.damage_numbers.append([en.x, en.y - 40, str(proj.damage), 30])
                else:
                    if hit_enemy.hit(proj.damage):
                        tower_sound_3.play()
                    self.damage_numbers.append([hit_enemy.x, hit_enemy.y - 40, str(proj.damage), 30])
                # Slow: MetalTower spowalnia trafionych.
                if proj.slow_on_hit:
                    hit_enemy.apply_slow(90)  # 1.5 sekundy przy 60 FPS
            if proj.done:
                self.projectiles.remove(proj)
        # Aktualizacja latajacych liczb obrazen
        for dn in self.damage_numbers[:]:
            dn[1] -= 1  # w gore
            dn[3] -= 1  # timer
            if dn[3] <= 0:
                self.damage_numbers.remove(dn)

    def show_end_screen(self, won):
        """Ekran koncowy. Zwraca True jesli gracz chce zrestartowac, False jesli wyjsc."""
        big_font = pygame.font.SysFont("arial", 70)
        small_font = pygame.font.SysFont("arial", 30)
        title = "YOU WIN! The island is saved!" if won else "YOU LOSE! The monsters broke through!"
        color = (60, 200, 90) if won else (220, 60, 60)
        # Przyciski
        restart_rect = pygame.Rect(self.width//2 - 220, self.height//2 + 60, 200, 60)
        quit_rect = pygame.Rect(self.width//2 + 20, self.height//2 + 60, 200, 60)
        # Statyczna klatka tla (bez migotania - rysujemy raz)
        self.win.blit(self.bg, (0, 0))
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.win.blit(overlay, (0, 0))
        text = big_font.render(title, 1, color)
        self.win.blit(text, (self.width // 2 - text.get_width() // 2, self.height // 2 - 60))
        sub = small_font.render("Wave reached: " + str(self.wave + 1) + " / " + str(len(waves)), 1, (255, 255, 255))
        self.win.blit(sub, (self.width // 2 - sub.get_width() // 2, self.height // 2 + 20))
        pygame.display.update()
        # Petla czeka na klikniecie przycisku (bez przerysowywania tla - brak migotania)
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    if restart_rect.collidepoint(pos):
                        return True
                    if quit_rect.collidepoint(pos):
                        return False
            # Rysuj przyciski (tylko przyciski sie odswiezaja)
            for rect, label_text, btn_color in [
                (restart_rect, "RESTART", (60, 180, 80)),
                (quit_rect, "QUIT", (180, 60, 60)),
            ]:
                pygame.draw.rect(self.win, btn_color, rect, border_radius=10)
                pygame.draw.rect(self.win, (255, 255, 255), rect, 2, border_radius=10)
                label = small_font.render(label_text, True, (255, 255, 255))
                self.win.blit(label, (rect.x + rect.width//2 - label.get_width()//2,
                                      rect.y + rect.height//2 - label.get_height()//2))
            pygame.display.update()
        return False
        
    def draw(self):
        self.win.blit(self.bg, (0,0))
        self.ship.draw(self.win)
        for tw in self.towers:
            tw.draw(self.win)
        if self.moving_object:
            self.moving_object.draw(self.win)
        for en in self.enemies:
            en.draw(self.win)
        for proj in self.projectiles:
            proj.draw(self.win)
        # Latajace liczby obrazen
        font_dmg = pygame.font.SysFont("arial", 18, bold=True)
        for x, y, text, timer in self.damage_numbers:
            alpha = min(255, timer * 8)
            label = font_dmg.render(text, True, (255, 100, 100))
            self.win.blit(label, (x - label.get_width()//2, y))
        
        self.menu.draw(self.win)
        self.draw_hud()

        pygame.display.update()

    def draw_hud(self):
        # Rzad spojnych "pigulek": fala, zycia, kasa
        pill_h = 44
        y = 10
        items = [
            (10, 180, None, "Wave #" + str(self.wave + 1)),
            (200, 130, lives_img, str(self.lives)),
            (340, 150, money_img, str(self.money)),
        ]
        for x, w, icon, text in items:
            s = pygame.Surface((w, pill_h), pygame.SRCALPHA)
            pygame.draw.rect(s, (8, 18, 38, 190), s.get_rect(), border_radius=pill_h // 2)
            pygame.draw.rect(s, (255, 255, 255, 70), s.get_rect(), 2, border_radius=pill_h // 2)
            self.win.blit(s, (x, y))
            label = self.hud_font.render(text, True, (255, 255, 255))
            cy = y + pill_h // 2 - label.get_height() // 2
            if icon is None:
                self.win.blit(label, (x + w // 2 - label.get_width() // 2, cy))
            else:
                ic = pygame.transform.scale(icon, (28, 28))
                group_w = ic.get_width() + 8 + label.get_width()
                gx = x + w // 2 - group_w // 2
                self.win.blit(ic, (gx, y + pill_h // 2 - ic.get_height() // 2))
                self.win.blit(label, (gx + ic.get_width() + 8, cy))
        # Przyciski pauzy i predkosci (prawy gorny rog)
        for rect, text in [(self.pause_btn_rect, "II" if not self.paused else "▶"),
                           (self.speed_btn_rect, f"{self.speed}x")]:
            s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, (8, 18, 38, 190), s.get_rect(), border_radius=10)
            pygame.draw.rect(s, (255, 255, 255, 70), s.get_rect(), 2, border_radius=10)
            self.win.blit(s, rect)
            label = self.hud_font.render(text, True, (255, 255, 255))
            self.win.blit(label, (rect.x + rect.width//2 - label.get_width()//2,
                                  rect.y + rect.height//2 - label.get_height()//2))
        # Podglad nastepnej fali (ikony wrogow)
        if self.wave + 1 < len(waves):
            next_wave = waves[self.wave + 1]
            preview_x = 10
            preview_y = 65
            # Tlo podgladu
            s = pygame.Surface((300, 50), pygame.SRCALPHA)
            pygame.draw.rect(s, (8, 18, 38, 150), s.get_rect(), border_radius=10)
            self.win.blit(s, (preview_x, preview_y))
            font_small = pygame.font.SysFont("arial", 16)
            label = font_small.render("Next:", True, (255, 255, 255))
            self.win.blit(label, (preview_x + 8, preview_y + 15))
            # Ikony wrogow (po jednej na typ, z liczba)
            x_off = preview_x + 60
            for i, count in enumerate(next_wave):
                if count > 0 and x_off < preview_x + 280:
                    # Uzyj pierwszej klatki animacji jako ikony
                    try:
                        enemy_cls = self.enemy_classes[i]
                        temp = enemy_cls()
                        icon = pygame.transform.scale(temp.imgs[0], (30, 30))
                        self.win.blit(icon, (x_off, preview_y + 10))
                        cnt_label = font_small.render(str(count), True, (255, 255, 0))
                        self.win.blit(cnt_label, (x_off + 32, preview_y + 15))
                        x_off += 60
                    except:
                        pass
            # Boss w nastepnej fali?
            if (self.wave + 2) % 4 == 0:
                boss_label = font_small.render("BOSS!", True, (255, 50, 50))
                self.win.blit(boss_label, (x_off, preview_y + 15))
        # Priorytet celowania wybranej wiezy
        if self.selected_tower:
            font_small = pygame.font.SysFont("arial", 16)
            prio_text = f"Target: {self.selected_tower.target_priority} (T)"
            label = font_small.render(prio_text, True, (255, 255, 0))
            self.win.blit(label, (10, 125))
            # Umiejetnosc aktywna
            tw = self.selected_tower
            if hasattr(tw, 'ability_name'):
                if tw.ability_cooldown > 0:
                    cd_sec = tw.ability_cooldown // 60
                    ab_text = f"{tw.ability_name}: {cd_sec}s (Q)"
                    color = (150, 150, 150)
                else:
                    ab_text = f"{tw.ability_name}: GOTOWE (Q)"
                    color = (100, 255, 100)
                label = font_small.render(ab_text, True, color)
                self.win.blit(label, (10, 145))
    def add_tower(self, name):
        x, y = pygame.mouse.get_pos()
        name_list = ["t1", "t2", "t3", "t4", "t5"]
        object_list = [WoodenTower(x,y), MetalTower(x,y), GoldenTower(x,y), FireTower(x,y), BlazeTower(x,y)]
        
        try:
            obj = object_list[name_list.index(name)]
            self.moving_object = obj
            obj.moving = True
        except Exception as e:
            print(str(e) + "NOT VALID NAME")

    
if __name__ == "__main__":
    from menu.start_menu import StartMenu
    start_menu = StartMenu(1124, 720, pygame.image.load(os.path.join("images", "bg.png")))
    settings = start_menu.run()
    if settings is not None:
        g = Game(lives=settings["lives"], money=settings["money"], sound=settings["sound"])
        g.run()
    pygame.quit()