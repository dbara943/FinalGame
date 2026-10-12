import pygame
import os
# Najwyzsza jakosc skalowania GPU (ostrzejszy fullscreen)
os.environ.setdefault("SDL_HINT_RENDER_SCALE_QUALITY", "2")
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
                                _gold_tint,
                                sound_1 as tower_sound_1, sound_2 as tower_sound_2,
                                sound_3 as tower_sound_3, sound_4 as tower_sound_4,
                                sound_5 as tower_sound_5)
from ships.ship import Ship
from menu.menu import VerticalMenu
from effects.particles import ParticleSystem, FloatingCoin, Shockwave
import time
import random
pygame.font.init()
pygame.display.set_caption('Island Defenders')

lives_img = pygame.image.load(os.path.join("images", "heart.png"))
money_img = pygame.image.load(os.path.join("images", "money.png"))
side_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "side_menu.png")), (375, 475))
t1_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "t1.png")), (30, 30))
t2_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "t2.png")), (30, 30))
t3_img = _gold_tint(pygame.transform.scale(pygame.image.load(os.path.join("images", "t3.png")), (30, 30)))
t4_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "t4.png")), (30, 30))
t5_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "t5.png")), (30, 30))
wave_bg = pygame.transform.scale(pygame.image.load(os.path.join("images","wave.png")), (225, 75))

towers_names = ["woodenTower", "metalTower", "goldenTower", "fireTower", "blazeTower"]
# Mapowanie: nazwa klasy wiezy -> nazwa przycisku w sklepie (t1..t5).
# get_item_cost() szuka po nazwie przycisku, wiec bez tego zwracal -1.
tower_shop_names = {"woodenTower": "t1", "metalTower": "t2", "goldenTower": "t3",
                    "fireTower": "t4", "blazeTower": "t5"}
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
sound_win = pygame.mixer.Sound("sounds/win.wav")
sound_lose = pygame.mixer.Sound("sounds/lose.wav")
sound_roar = pygame.mixer.Sound("sounds/roar.wav")
sound_levelup = pygame.mixer.Sound("sounds/levelup.wav")
sound_horn = pygame.mixer.Sound("sounds/horn.wav")
sound_rain = pygame.mixer.Sound("sounds/rain.wav")
sound_rain.set_volume(0.35)  # deszcz wyraznie ciszej niz reszta
sound_gull = pygame.mixer.Sound("sounds/gull.wav")
sound_fanfare = pygame.mixer.Sound("sounds/fanfare.wav")
shoot_sounds = {
    "WoodenTower": pygame.mixer.Sound("sounds/shoot_wood.wav"),
    "MetalTower": pygame.mixer.Sound("sounds/shoot_metal.wav"),
    "GoldenTower": pygame.mixer.Sound("sounds/shoot_gold.wav"),
    "FireTower": pygame.mixer.Sound("sounds/shoot_fire.wav"),
    "BlazeTower": pygame.mixer.Sound("sounds/shoot_blaze.wav"),
}

class Game:
    def __init__(self, lives=20, money=200, sound=True):
        self.width = 1124
        self.height = 720
        self.win = pygame.display.set_mode((self.width, self.height), pygame.SCALED | pygame.FULLSCREEN)
        # Konwersja formatu obrazkow po inicjalizacji display (szybszy blit)
        global lives_img, money_img, side_img, t1_img, t2_img, t3_img, t4_img, t5_img
        lives_img = lives_img.convert_alpha()
        money_img = money_img.convert_alpha()
        side_img = side_img.convert_alpha()
        t1_img = t1_img.convert_alpha()
        t2_img = t2_img.convert_alpha()
        t3_img = t3_img.convert_alpha()
        t4_img = t4_img.convert_alpha()
        t5_img = t5_img.convert_alpha()
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
        # Statystyki koncowe
        self.stats_kills = 0
        self.stats_gold = 0
        self.stats_damage = 0
        self.endless = False  # Tryb endless po wygranej
        self.endless_wave = 0
        self.wave_banner_text = ""  # V3: banner fali
        self.wave_banner_timer = 0
        self.muzzle_flashes = []  # V4: blyski przy strzale [(x, y, timer)]
        self.waiting_for_clear = False  # Czekamy na wyczyszczenie planszy przed nastepna fala
        self.gold_notifications = []  # Widoczne powiadomienia o zlocie [(tekst, timer)]
        self.corpses = []  # Trupy wrogow: [img, x, y, timer]
        self.early_wave_rect = None  # R2: prostokat przycisku "Nastepna fala"
        self.wave_modifier = None  # U8: modyfikator fali (swift/rich/swarm)
        self.show_all_ranges = False  # U10: pokaz wszystkie zasiegi
        self.pending_boss = None  # Boss czeka na zadokowanie statku
        self.raining = False  # 7: deszcz
        self.raindrops = []  # krople deszczu [(x, y, speed)]
        self.wave_report = None  # 9: raport po fali (tekst, timer)
        self._wave_kills_start = 0
        self._wave_gold_start = 0
        self.last_placed = None  # Q7: ostatnio postawiona wieza (Ctrl+Z)
        self.last_upgrade = None  # Q13: ostatni upgrade (Ctrl+Z)
        # Efekty wizualne
        self.particles = ParticleSystem()
        self.coins = []  # Latajace monety
        self.chests = []  # 21: skrzynie skarbow [x, y, timer]
        self.kill_streak = []  # 37: znaczniki zabojstw
        self.announcements = []  # 37: ogloszenia [tekst, timer]
        self.gull_timer = 900  # 39: krakanie mew
        # Ambient wizualny 11-25
        self.fishes = []  # 12: skaczace rybki [x, y, vx, vy, t, kolor]
        self.fish_timer = 200
        self.balloon = None  # 14: balon [x, y]
        self.balloon_timer = 1800
        self.whale_timer = 2400  # 15: wieloryb
        self.whale = None  # [x, t]
        self.crabs = [[250 + i * 60, 660, random.random() * 6, 1] for i in range(3)]  # 17: [x, y, faza, kier]
        self.octo_timer = 3000  # 18: osmiornica
        self.octo = None  # [x, t]
        self.chameleon_hue = 0  # 25: kameleon
        self.shockwaves = []  # Kregi uderzeniowe
        self.screen_shake = 0  # Wstrzas ekranu
        self.scorch_marks = []  # Spalenizna [(x, y, timer)]
        self.clouds = [(random.randint(0, 1124), random.randint(20, 200), random.randint(20, 40)) for _ in range(3)]
        self.leaves = [(random.randint(0, 1124), random.randint(0, 720)) for _ in range(15)]
        self.seagulls = [(random.randint(200, 900), random.randint(50, 150), random.random()*6) for _ in range(2)]
        self.game_time = 0  # Q17: zegar sesji (ticki)
        self.muted = False  # Q16
        self.build_queue = []  # Q14: kolejka budowy
        self.tower_filter = None  # Q15: filtr wiez
        self.display_money = 200  # Niespodzianka 4: animowany licznik zlota
        # Wizualne: fale, odbicia, niebo
        self.wave_phase = 0  # faza fal wody
        self.shooting_stars = []  # spadajace gwiazdy
        self.fireflies = [(random.randint(100, 1000), random.randint(300, 600)) for _ in range(12)]
        self.butterflies = [(random.randint(200, 900), random.randint(350, 550), random.random()*6) for _ in range(5)]
        self.bird_flocks = []  # klucze ptakow
        self.flowers = [(random.randint(150, 950), random.randint(380, 620), random.choice([(255,150,180),(255,255,150),(200,150,255)])) for _ in range(15)]
        self.boss_footprints = []  # slady stop bossa
        self.lightning_timer = 0  # blyskawica
        self.morning_fog = 0  # mgla poranna
        if not sound:
            pygame.mixer.music.pause()
            for s in (sound_1, sound_2, sound_3, sound_4, sound_5,
                      tower_sound_1, tower_sound_2, tower_sound_3,
                      tower_sound_4, tower_sound_5, sound_win, sound_lose, sound_roar,
                      sound_levelup, sound_horn, sound_rain, sound_gull, sound_fanfare,
                      *shoot_sounds.values()):
                s.set_volume(0)
        self.bg = pygame.image.load(os.path.join("images", "bg_noship.png"))
        self.bg = pygame.transform.scale(self.bg, (self.width, self.height))
        self.ship = Ship(os.path.join("images", "ship.png"), dock_x=300, dock_y=665,
                         screen_w=self.width)
        self.ship.sail_in()
        self.last_wave_done = False
        self.timer = time.time()
        self.hud_font = pygame.font.SysFont("segoe ui, calibri, arial", 26, bold=True)
        # Cache fontow - tworzone raz w __init__, nie co klatke (wydajnosc)
        _fn = "segoe ui, calibri, arial"
        self.font_big70 = pygame.font.SysFont(_fn, 70)
        self.font_small30 = pygame.font.SysFont(_fn, 30)
        self.font_stats24 = pygame.font.SysFont(_fn, 24)
        self.font_dmg18 = pygame.font.SysFont(_fn, 18, bold=True)
        self.font_crit22 = pygame.font.SysFont(_fn, 22, bold=True)
        self.font_banner64 = pygame.font.SysFont(_fn, 64, bold=True)
        self.font_gold28 = pygame.font.SysFont(_fn, 28, bold=True)
        self.font_boss16 = pygame.font.SysFont(_fn, 16, bold=True)
        self.font_btn18 = pygame.font.SysFont(_fn, 18, bold=True)
        self.font_c13 = pygame.font.SysFont(_fn, 13, bold=True)
        self.font_r16 = pygame.font.SysFont(_fn, 16)
        self.font_q14 = pygame.font.SysFont(_fn, 14)
        self.font_p36 = pygame.font.SysFont(_fn, 36, bold=True)
        self.font_s16 = pygame.font.SysFont(_fn, 16)
        self.font_e14 = pygame.font.SysFont(_fn, 14, bold=True)
        self.font_ann34 = pygame.font.SysFont(_fn, 34, bold=True)
        self.font_f13 = pygame.font.SysFont(_fn, 13, bold=True)
        self.font_f11 = pygame.font.SysFont(_fn, 11)
        self.font_small16 = pygame.font.SysFont(_fn, 16)
        # Prerender pigulek HUD (tla statyczne, nie tworzone co klatke)
        self._pill_h = 44
        self._pills = []
        for _w in (180, 130, 150):
            _s = pygame.Surface((_w, self._pill_h), pygame.SRCALPHA)
            pygame.draw.rect(_s, (8, 18, 38, 190), _s.get_rect(), border_radius=self._pill_h // 2)
            pygame.draw.rect(_s, (255, 255, 255, 70), _s.get_rect(), 2, border_radius=self._pill_h // 2)
            self._pills.append(_s)
        self._lives_icon = pygame.transform.scale(lives_img, (28, 28))
        self._money_icon = pygame.transform.scale(money_img, (28, 28))
        # Prerender statycznych napisow (wydajnosc)
        self._txt_paused = self.font_p36.render("PAUSED", True, (255, 255, 255))
        self._txt_paused_sub = self.font_s16.render("you can build and upgrade towers", True, (200, 200, 200))
        self._txt_ready = self.font_f11.render("READY - click", True, (255, 255, 200))
        self._txt_no_tower = self.font_f11.render("no tower", True, (120, 120, 120))
        self._txt_next = self.font_small16.render("Next:", True, (255, 255, 255))
        self._txt_boss = self.font_small16.render("BOSS!", True, (255, 50, 50))
        # Licznik klatek i cache czasu animacji ambient (wydajnosc)
        self._frame = 0
        self._ambient_t = 0.0
        self._hover_enemy = None
        self._now = 0
        self._now_s = 0.0
        # Prerender nakladek dnia/nocy (fullscreen Surface raz, nie co klatke)
        self._overlay_sunset = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._overlay_sunset.fill((255, 150, 50, 40))
        self._overlay_night = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._overlay_night.fill((10, 10, 40, 100))
        self._overlay_dawn = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._overlay_dawn.fill((255, 200, 150, 30))
        self.selected_tower = None
        self.menu = VerticalMenu(self.width - 100, 250, side_img)
        self.menu.add_btn(t1_img, "t1", 100, damage=1)
        self.menu.add_btn(t2_img, "t2", 200, damage=3)
        self.menu.add_btn(t3_img, "t3", 300, damage=5)
        self.menu.add_btn(t4_img, "t4", 400, damage=8)
        self.menu.add_btn(t5_img, "t5", 500, damage=10)
        self.moving_object =  None
        self.menu_dragging = False  # przeciganie sklepu myszka
        self.menu_drag_dx = 0
        self.menu_drag_dy = 0
        self.wave = 0
        self.current_wave = waves[self.wave][:]
        self.won = False
        self.enemy_classes = [Forkman, Swordman, Knight, Goblin, Cyclop, Impostor, Ogre, EvilVillager]

    def gen_enemies(self):
        # Wrogowie desantuja sie tylko gdy statek jest w porcie.
        if self.won or self.ship.state != Ship.DOCKED:
            return
        # Boss czeka na zadokowanie - spawnuj gdy statek w porcie
        if self.pending_boss:
            self.enemies.append(self.pending_boss)
            # A10: intro bossa
            self.wave_banner_text = "⚠ BOSS ⚠"
            self.wave_banner_timer = 150
            self.screen_shake = 10
            sound_roar.play()
            self.pending_boss = None
        if sum(self.current_wave) == 0:
            # Rozladunek zakonczony - statek wyplywa, czekamy na wyczyszczenie planszy.
            # Nastepna fala zacznie sie dopiero gdy nie bedzie wrogow na mapie.
            if not self.waiting_for_clear:
                self.waiting_for_clear = True
                self.ship.sail_out()
        else:
            for i in range(len(self.current_wave)):
                if self.current_wave[i] != 0:
                    self.current_wave[i] -= 1
                    en = self.enemy_classes[i]()
                    # U8: SWIFT - +30% predkosci
                    if self.wave_modifier == "swift":
                        en.velocity *= 1.3
                    # 6: 8% szansy na elitarnego (nie boss)
                    if not isinstance(en, Boss) and random.random() < 0.08:
                        en.make_elite()
                    self.enemies.append(en)
                    break

    def advance_wave(self):
        """Przechodzi do nastepnej fali: zloto, bonusy, powiadomienie. Wywolywane
        gdy plansza jest wyczyszczona i statek ma wrocic."""
        # 9: raport po fali
        if self.wave > 0 or self.endless_wave > 0:
            kills = self.stats_kills - self._wave_kills_start
            gold = self.stats_gold - self._wave_gold_start
            lives_lost = self._wave_start_lives - self.lives
            # MVP: wieza z najwieksza liczba zabojstw
            mvp = max(self.towers, key=lambda t: t.kills, default=None)
            mvp_text = f"{mvp.name} ({mvp.kills})" if mvp else "-"
            report = f"Wave {self.wave + 1}: {kills} kills, -{lives_lost} lives, +{gold}$ | MVP: {mvp_text}"
            self.wave_report = [report, 240]
        self._wave_kills_start = self.stats_kills
        self._wave_gold_start = self.stats_gold
        sound_fanfare.play()  # 40: fanfara fali
        if self.endless:
            # Tryb endless: generuj fale proceduralnie z rosnacym HP
            self.endless_wave += 1
            self.wave += 1
            scale = 1 + self.endless_wave * 0.15
            self.current_wave = [
                int(20 * scale), int(15 * scale), int(12 * scale), int(10 * scale),
                int(8 * scale), int(6 * scale), int(5 * scale), int(3 * scale),
            ]
            gold = 200
            self.money += gold
            self.gold_notifications.append([f"+{gold} gold (endless wave)", 150])
            if self.endless_wave % 4 == 0:
                self.pending_boss = Boss()
        elif self.wave + 1 >= len(waves):
            self.last_wave_done = True
        else:
            # Zloto za fale: baza + bonus za czysta fale (bez odsetek)
            base_gold = (self.wave + 1) * 100
            bonus = 0
            if hasattr(self, '_wave_start_lives') and self.lives == self._wave_start_lives:
                bonus = 50 + self.wave * 10
            total = base_gold + bonus
            self.money += total
            # Widoczne powiadomienie o zlocie
            parts = [f"+{base_gold} for wave"]
            if bonus > 0:
                parts.append(f"+{bonus} clean wave")
            self.gold_notifications.append([" | ".join(parts), 180])
            self.wave += 1
            self.current_wave = waves[self.wave][:]
            self._wave_start_lives = self.lives
            self.wave_banner_text = f"WAVE {self.wave + 1}"  # V3
            self.wave_banner_timer = 120  # 2 sekundy
            # U8: modyfikator co 3 fale (nie na bossach)
            self.wave_modifier = None
            wave_num = self.wave + 1
            if wave_num % 3 == 0 and wave_num % 4 != 0 and wave_num != 10:
                mod = random.choice(["swift", "rich", "swarm"])
                self.wave_modifier = mod
                if mod == "swift":
                    self.wave_banner_text += " [SWIFT!]"
                elif mod == "rich":
                    self.wave_banner_text += " [RICH!]"
                elif mod == "swarm":
                    self.current_wave = [int(c * 1.5) for c in self.current_wave]
                    self.wave_banner_text += " [SWARM!]"
            # 7: deszcz na losowych falach (20% szansy, nie na bossach)
            was_raining = self.raining
            self.raining = False
            if wave_num % 4 != 0 and wave_num != 10 and random.random() < 0.2:
                self.raining = True
                self.wave_banner_text += " [RAIN]"
                self.raindrops = [(random.randint(0, self.width), random.randint(0, self.height),
                                   random.randint(8, 14)) for _ in range(100)]
                sound_rain.play(loops=-1)  # 38: szum deszczu
            elif was_raining:
                sound_rain.stop()
                # B4: tecza po deszczu
                self._rainbow_timer = 600  # 10s
            # Boss na falach 4 i 8; fala 10 (ostatnia) to sam boss FINALNY.
            # Boss spawnuje sie dopiero gdy statek zadokuje (pending_boss).
            if (self.wave + 1) % 4 == 0 and self.wave + 1 < 10:
                self.pending_boss = Boss()
                self.wave_banner_text = f"WAVE {self.wave + 1} - BOSS!"
            elif self.wave + 1 == 10:
                self.pending_boss = Boss(final=True)
                self.wave_banner_text = "FINALNA FALA - BOSS!"
        self.waiting_for_clear = False
    def run(self):
        if self.sound:
            pygame.mixer.music.play(loops=-1)
        run = True
        clock = pygame.time.Clock()
        # Fixed timestep: logika 100Hz, render 60 FPS (wydajnosc bez zmiany balansu)
        LOGIC_HZ = 100.0
        RENDER_FPS = 60
        logic_acc = 0.0
        ship_acc = 0.0
        while run:
            clock.tick_busy_loop(RENDER_FPS)
            
            if time.time() - self.timer >= random.randrange(1, 5)/2:
                    self.timer = time.time()
                    self.gen_enemies()
            # Statek w tempie logiki 100Hz (akumulator, z capem)
            ship_acc = min(ship_acc + LOGIC_HZ / RENDER_FPS, 5.0)
            while ship_acc >= 1.0:
                self.ship.update()
                ship_acc -= 1.0
            if self.ship.state == Ship.AWAY and not self.won:
                if self.last_wave_done:
                    self.won = True
                elif self.waiting_for_clear:
                    # Statek odplynal po rozladunku - czekamy na wyczyszczenie planszy.
                    # Nastepna fala dopiero gdy nie ma wrogow.
                    if len(self.enemies) == 0:
                        self.advance_wave()
                        if not self.last_wave_done:
                            # Statek wraca losowo z lewej lub prawej (sail_in losuje strone)
                            self.ship.sail_in()
                else:
                    self.ship.sail_in()
            pos = pygame.mouse.get_pos()                 
            if self.moving_object:
                self.moving_object.move(pos[0], pos[1])
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                # Przeciganie sklepu
                if event.type == pygame.MOUSEMOTION and self.menu_dragging:
                    self.menu.x = max(100, min(self.width - 100, event.pos[0] + self.menu_drag_dx))
                    self.menu.y = max(190, min(self.height - 190, event.pos[1] + self.menu_drag_dy))
                if event.type == pygame.MOUSEBUTTONUP:
                    self.menu_dragging = False
                if event.type == pygame.KEYDOWN:
                    # Q: aktywacja umiejetnosci wybranej wiezy
                    if event.key == pygame.K_q and self.selected_tower:
                        self.selected_tower.activate_ability(self.enemies, self.projectiles)
                    # F11: przelacz fullscreen / okno 1:1 (ostrzejsze piksele)
                    if event.key == pygame.K_F11:
                        self._fullscreen = not getattr(self, '_fullscreen', True)
                        if self._fullscreen:
                            self.win = pygame.display.set_mode(
                                (self.width, self.height), pygame.SCALED | pygame.FULLSCREEN)
                        else:
                            self.win = pygame.display.set_mode((self.width, self.height))
                    # Spacja: pauza
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    # 1-5: wybor wiezy ze sklepu
                    if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                        idx = event.key - pygame.K_1
                        tower_names = ["t1", "t2", "t3", "t4", "t5"]
                        if idx < len(tower_names):
                            cost = self.menu.get_item_cost(tower_names[idx])
                            if self.money >= cost:
                                self.money -= cost
                                self.add_tower(tower_names[idx])
                    # U: upgrade wybranej wiezy, S: sprzedaz
                    if event.key == pygame.K_u and self.selected_tower:
                        cost = self.selected_tower.menu.get_item_cost()
                        if cost != "MAX" and self.money >= cost:
                            self.money -= cost
                            self.selected_tower.upgrade(cost)
                            # Q13: zapamietaj do Ctrl+Z
                            self.last_upgrade = (self.selected_tower, cost)
                    # U10: R - pokaz/ukryj wszystkie zasiegi
                    if event.key == pygame.K_r:
                        self.show_all_ranges = not self.show_all_ranges
                    # Q7: Ctrl+Z - cofnij postawienie wiezy / upgrade
                    if event.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        if self.last_upgrade:
                            tw, cost = self.last_upgrade
                            if tw.level > 1:
                                tw.level -= 1
                                tw.damage -= 2
                                tw.range -= 12
                                tw.total_spent -= cost
                                self.money += cost
                            self.last_upgrade = None
                        elif self.last_placed:
                            tw, cost = self.last_placed
                            if tw in self.towers:
                                self.towers.remove(tw)
                                self._recalc_synergy()
                                self.money += cost
                                if self.selected_tower is tw:
                                    self.selected_tower = None
                            self.last_placed = None
                    # Q10: F - przelacz 1x/3x
                    if event.key == pygame.K_f:
                        self.speed = 3 if self.speed == 1 else 1
                    # Q16: M - wyciszenie (pauza muzyki, nie restart)
                    if event.key == pygame.K_m:
                        self.muted = not self.muted
                        if self.muted:
                            pygame.mixer.music.pause()
                            sound_rain.stop()
                        else:
                            pygame.mixer.music.unpause()
                            if self.raining:
                                sound_rain.play(loops=-1)
                        vol = 0 if self.muted else 1
                        for s in (sound_1, sound_2, sound_3, sound_4, sound_5, sound_win, sound_lose, sound_roar,
                                  sound_levelup, sound_horn, sound_rain, sound_gull, sound_fanfare,
                                  *shoot_sounds.values()):
                            s.set_volume(vol)
                        if not self.muted:
                            sound_rain.set_volume(0.35)  # deszcz zawsze ciszej
                    # Q11: F5 - zapis, F9 - wczytaj
                    if event.key == pygame.K_F5:
                        self.save_game()
                    if event.key == pygame.K_F9:
                        self.load_game()
                    # Q15: C - filtr wiez (cykl po typach)
                    if event.key == pygame.K_c:
                        types = [None, "Wooden", "Metal", "Golden", "Fire", "Blaze"]
                        idx = types.index(self.tower_filter) if self.tower_filter in types else 0
                        self.tower_filter = types[(idx + 1) % len(types)]
                    if event.key == pygame.K_s and self.selected_tower:
                        self.money += self.selected_tower.sell_value()
                        self.towers.remove(self.selected_tower)
                        self._recalc_synergy()
                        self.selected_tower = None
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    # Przeciganie sklepu: klik na panel (poza przyciskami) = drag
                    if self.menu.get_rect().collidepoint(pos):
                        if not self.menu.get_clicked(pos[0], pos[1]):
                            self.menu_dragging = True
                            self.menu_drag_dx = self.menu.x - pos[0]
                            self.menu_drag_dy = self.menu.y - pos[1]
                            continue
                    # Q3: Shift+klik = szybka sprzedaz wiezy
                    keys = pygame.key.get_mods()
                    if keys & pygame.KMOD_SHIFT and self.selected_tower:
                        self.money += self.selected_tower.sell_value()
                        self.towers.remove(self.selected_tower)
                        self._recalc_synergy()
                        self.selected_tower = None
                        continue
                    # Ability dock - klikniecie aktywuje umiejetnosc
                    if hasattr(self, 'ability_slots'):
                        for rect, tname in self.ability_slots:
                            if rect.collidepoint(pos):
                                for tw in self.towers:
                                    if type(tw).__name__.startswith(tname) and tw.ability_cooldown <= 0:
                                        tw.activate_ability(self.enemies, self.projectiles)
                                        break
                                continue
                    # R2: przycisk wczesniejszej fali
                    if self.early_wave_rect and self.early_wave_rect.collidepoint(pos):
                        bonus = len(self.enemies) * 5
                        self.money += bonus
                        self.gold_notifications.append([f"+{bonus}$ rush bonus!", 150])
                        self.advance_wave()
                        if not self.last_wave_done and not self.won:
                            self.ship.sail_in()
                        continue
                    # Przyciski pauzy i predkosci
                    if self.pause_btn_rect.collidepoint(pos):
                        self.paused = not self.paused
                        continue
                    if self.speed_btn_rect.collidepoint(pos):
                        self.speed = self.speed % 3 + 1  # 1->2->3->1
                        continue
                    if self.moving_object:
                        if self.moving_object.name in towers_names:
                            # R4: tylko na poprawnym miejscu
                            gx = round(self.moving_object.x / 40) * 40
                            gy = round(self.moving_object.y / 40) * 40
                            if self.is_valid_placement(gx, gy):
                                self.moving_object.x, self.moving_object.y = gx, gy
                                self.moving_object.menu.x, self.moving_object.menu.y = gx, gy
                                self.moving_object.menu.update()
                                # Q14: Shift = kolejka budowy
                                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                                    self.build_queue.append((self.moving_object.name, gx, gy))
                                    self.money += self.shop_price(self.moving_object.name)  # zwrot, pobierze przy budowie
                                else:
                                    self.towers.append(self.moving_object)
                                    self._recalc_synergy()
                                # Q7: zapamietaj do Ctrl+Z
                                self.last_placed = (self.moving_object, self.shop_price(self.moving_object.name))
                            # else: niepoprawne - wieza znika (pieniadze przepadaja? nie - zwroc)
                            else:
                                # Zwroc pieniadze za wieze
                                cost = self.shop_price(self.moving_object.name)
                                self.money += cost
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
                                self._recalc_synergy()
                                self.selected_tower = None
                    if not (btn_clicked):    
                        for tw in self.towers:
                            if tw.click(pos[0], pos[1]):
                                tw.selected = True
                                self.selected_tower = tw
                            else:
                                tw.selected = False     
            # Logika gry w tempie 100Hz (akumulator) - pauza pomija, predkosc mnozy
            # Cap 5 tickow/klatke: zapobiega spirali smierci i skokom po stallu
            if not self.paused:
                logic_acc = min(logic_acc + (LOGIC_HZ / RENDER_FPS) * self.speed, 5.0)
                while logic_acc >= 1.0:
                    self.update_game_logic()
                    logic_acc -= 1.0
                    if self.lives <= 0 or self.won:
                        logic_acc = 0
                        break

            if self.lives <= 0:
                sound_lose.play()
                result = self.show_end_screen(False)
                if result == "restart":
                    self.reset_game()
                else:
                    run = False
            elif self.won:
                sound_win.play()
                result = self.show_end_screen(True)
                if result == "restart":
                    self.reset_game()
                elif result == "continue":
                    # Tryb endless: kontynuuj z proceduralnymi falami
                    self.endless = True
                    self.won = False
                    self.last_wave_done = False
                    self.ship.sail_in()
                else:
                    run = False

            try:
                self.draw()
            except pygame.error:
                # Utrata kontekstu graficznego (alt-tab) - nie crashuj
                pass
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
        self.endless = False
        self.endless_wave = 0
        self.paused = False
        self.speed = 1
        self.selected_tower = None
        self.moving_object = None
        self.timer = time.time()
        self._wave_start_lives = self._start_lives
        self.stats_kills = 0
        self.stats_gold = 0
        self.stats_damage = 0
        self.ship = Ship(os.path.join("images", "ship.png"), dock_x=300, dock_y=665,
                         screen_w=self.width)
        self.ship.sail_in()

    def _recalc_synergy(self):
        """5: przelicza bonus synergii - tylko gdy wieze sie zmienia, nie co tick."""
        for tw in self.towers:
            tw._synergy = tw.get_synergy_bonus(self.towers)

    def update_game_logic(self):
        """Jedna iteracja logiki gry (ruch wrogow, ataki, pociski)."""
        # V3: banner fali
        if self.wave_banner_timer > 0:
            self.wave_banner_timer -= 1
        # Powiadomienia o zlocie
        for gn in self.gold_notifications[:]:
            gn[1] -= 1
            if gn[1] <= 0:
                self.gold_notifications.remove(gn)
        # Trupy - znikaja po 4 sekundach
        for c in self.corpses[:]:
            c[3] -= 1
            if c[3] <= 0:
                self.corpses.remove(c)
        # 9: raport po fali
        if self.wave_report:
            self.wave_report[1] -= 1
            if self.wave_report[1] <= 0:
                self.wave_report = None
        # Efekty: czasteczki, monety, fale uderzeniowe
        self.particles.update()
        for c in self.coins[:]:
            if c.update():
                self.coins.remove(c)
        for s in self.shockwaves[:]:
            if s.update():
                self.shockwaves.remove(s)
        if self.screen_shake > 0:
            self.screen_shake -= 1
        for sc in self.scorch_marks[:]:
            sc[2] -= 1
            if sc[2] <= 0:
                self.scorch_marks.remove(sc)
        self.game_time += 1
        # 39: losowe krakanie mew
        self.gull_timer -= 1
        if self.gull_timer <= 0:
            self.gull_timer = random.randint(1200, 2400)
            if not self.muted:
                sound_gull.play()
        # Q14: kolejka budowy - stawiaj po kolei
        if self.build_queue and not self.moving_object:
            name, gx, gy = self.build_queue[0]
            cost = self.shop_price(name)
            if self.money >= cost and self.is_valid_placement(gx, gy):
                self.money -= cost
                tower_map = {"t1": WoodenTower, "t2": MetalTower, "t3": GoldenTower,
                             "t4": FireTower, "t5": BlazeTower}
                tw = tower_map[name](gx, gy)
                self.towers.append(tw)
                self._recalc_synergy()
                self.build_queue.pop(0)
            else:
                self.build_queue.pop(0)  # nie da sie - usun z kolejki
        # Niespodzianka 4: animowany licznik zlota (dogania prawdziwa wartosc)
        if self.display_money < self.money:
            self.display_money = min(self.money, self.display_money + max(1, (self.money - self.display_money) // 10))
        elif self.display_money > self.money:
            self.display_money = self.money
        # V4: muzzle flashes
        for mf in self.muzzle_flashes[:]:
            mf[2] -= 1
            if mf[2] <= 0:
                self.muzzle_flashes.remove(mf)
        # Aktualizacja cooldownow umiejetnosci
        for tw in self.towers:
            if tw.ability_cooldown > 0:
                tw.ability_cooldown -= 1
            # Cooldown ataku wiezy (tick-based, zeby speed dzialal)
            if tw.attack_cooldown > 0:
                tw.attack_cooldown -= 1
        # Update wrogow (animacje, ruch, timery) - TU, nie w draw()!
        for en in self.enemies:
            en.update()
            # A7: kurz
            if getattr(en, '_dust', False):
                en._dust = False
                self.particles.burst(en.x, en.y + 15, (180, 160, 140), count=2, speed=1, life=20, size=3, gravity=-0.05)
            # Slad lodu za spowolnionymi
            if en.slow_timer > 0 and random.random() < 0.15:
                self.particles.burst(en.x, en.y + 10, (180, 220, 255), count=1, speed=0.5, life=20, size=2, gravity=0)
            # Slady stop bossa
            if isinstance(en, Boss) and random.random() < 0.15:
                self.boss_footprints.append([en.x, en.y + 10, 300])
                if len(self.boss_footprints) > 20:
                    self.boss_footprints.pop(0)
            # Boss finalny: ryk przy enrage
            if isinstance(en, Boss) and en.get_roar_request():
                sound_roar.play()
                self.wave_banner_text = "BOSS ENRAGED!"
                self.wave_banner_timer = 90
            # Boss finalny przywoluje miniony
            if isinstance(en, Boss) and en.get_summon_request():
                for _ in range(2):
                    m = Forkman()
                    m.x, m.y = en.x - 30, en.y + 20
                    m.path_pos = en.path_pos
                    self.enemies.append(m)
                self.gold_notifications.append(["Boss przywoluje posilki!", 120])
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
                # Q6: auto-pauza przy 3 zyciach
                if self.lives == 3 and not self.paused:
                    self.paused = True
                    self.gold_notifications.append(["WARNING: 3 lives! Paused.", 180])
            else:
                # Wrog zabity pociskiem - kasa za niego.
                # Golden Touch: podwojna kasa (oznaczeni lub globalny buff)
                reward = d.money
                if getattr(d, '_gold_marked', False):
                    reward *= 2
                # U8: RICH - +50% zlota
                if self.wave_modifier == "rich":
                    reward = int(reward * 1.5)
                # 7: deszcz +15% zlota
                if self.raining:
                    reward = int(reward * 1.15)
                self.money += reward
                # Trup zostaje na ziemi (ostatnia klatka animacji smierci)
                if d.die_imgs:
                    corpse_img = d.die_imgs[-1]
                    self.corpses.append([corpse_img, d.x, d.y, 240])  # 4 sekundy
                # A1: eksplozja czasteczek
                self.particles.burst(d.x, d.y - 30, (200, 200, 200), count=10, speed=3)
                if isinstance(d, Boss):
                    self.particles.burst(d.x, d.y - 30, (255, 100, 100), count=30, speed=5, size=6)
                    self.shockwaves.append(Shockwave(d.x, d.y - 30, max_r=120))
                    self.screen_shake = 15  # A6: wstrzas przy bossie
                # A2: latajaca moneta
                self.coins.append(FloatingCoin(d.x, d.y - 40, 415, 32, reward))
                # R5: licznik zabojstw wiezy
                if d.last_hit_by:
                    d.last_hit_by.kills += 1
                self.stats_kills += 1
                self.stats_gold += reward
                # 21: skrzynia skarbow po bossie
                if isinstance(d, Boss):
                    self.chests.append([d.x, d.y, 0])
                # 37: spiker serii zabojstw
                now = self._now
                self.kill_streak = [t for t in getattr(self, 'kill_streak', []) if now - t < 3000]
                self.kill_streak.append(now)
                n = len(self.kill_streak)
                if n == 2: self.announce("DOUBLE KILL!")
                elif n == 3: self.announce("TRIPLE KILL!")
                elif n == 5: self.announce("RAMPAGE!")
                elif n == 8: self.announce("UNSTOPPABLE!")
            self.enemies.remove(d)

        # Siatka przestrzenna dla namierzania (wydajnosc)
        _cell = 120
        _grid = {}
        for en in self.enemies:
            if en.dying or en.dead or en.reached_end:
                continue
            _key = (int(en.x // _cell), int(en.y // _cell))
            _grid.setdefault(_key, []).append(en)
        for tw in self.towers:
            # 5: synergia - przeliczana tylko gdy wieze sie zmienia (flaga), nie co tick
            # 7: deszcz -10% zasiegu
            tw._rain_mod = 0.9 if self.raining else 1.0
            # Wizualne: czasteczki idle wiez
            if random.random() < 0.05:
                tname = type(tw).__name__
                if tname == "FireTower":
                    self.particles.burst(tw.x, tw.y - 40, (255, 120, 40), count=1, speed=1, life=25, size=3, gravity=-0.1)
                elif tname == "GoldenTower":
                    self.particles.burst(tw.x, tw.y - 40, (255, 215, 0), count=1, speed=0.8, life=30, size=2, gravity=-0.05)
                elif tname == "MetalTower":
                    self.particles.burst(tw.x, tw.y - 40, (180, 220, 255), count=1, speed=0.8, life=25, size=2, gravity=-0.05)
                elif tname == "BlazeTower":
                    self.particles.burst(tw.x, tw.y - 40, (200, 100, 255), count=1, speed=1, life=25, size=3, gravity=-0.1)
            # A5: efekt ulepszenia
            if getattr(tw, '_upgrade_fx', False):
                tw._upgrade_fx = False
                self.particles.burst(tw.x, tw.y - 40, (255, 215, 0), count=20, speed=4, size=5)
                self.shockwaves.append(Shockwave(tw.x, tw.y - 20, max_r=60, color=(255, 215, 0)))
                sound_levelup.play()  # Niespodzianka 2: dzwiek level up
            if tw.attack(self.enemies, self.projectiles, _grid, _cell):
                # V4: muzzle flash przy strzale
                self.muzzle_flashes.append([tw.x, tw.y - 30, 6])
                # Dym z lufy
                self.particles.burst(tw.x, tw.y - 35, (150, 150, 150), count=2, speed=1, life=20, size=3, gravity=-0.08)

        # Pociski leca do celow; trafienie zadaje obrazenia.
        for proj in self.projectiles[:]:
            hit_enemy = proj.move()
            if hit_enemy is not None:
                # R5: zapamietaj wieze
                if proj.source_tower:
                    hit_enemy.last_hit_by = proj.source_tower
                # U6: Critical hit - 15% szansy na 2x obrazen
                is_crit = random.random() < 0.15
                crit_mult = 2.0 if is_crit else 1.0
                # Efekty specjalne pociskow umiejetnosci
                if proj.special == "frost_nova":
                    # Frost Nova: spowolnienie wszystkich w duzym promieniu
                    for en in self.enemies:
                        if en.dying or en.dead or en.reached_end:
                            continue
                        dist = math.sqrt((en.x - hit_enemy.x)**2 + (en.y - hit_enemy.y)**2)
                        if dist < 150:
                            en.apply_slow(240)
                            en.hit(5)
                    self.damage_numbers.append([hit_enemy.x, hit_enemy.y - 50, "FROST NOVA!", 40, (150, 220, 255)])
                elif proj.special == "meteor":
                    # Meteor: 3x obrazen, duzy splash
                    for en in self.enemies:
                        if en.dying or en.dead or en.reached_end:
                            continue
                        dist = math.sqrt((en.x - hit_enemy.x)**2 + (en.y - hit_enemy.y)**2)
                        if dist < 120:
                            dmg = proj.damage * 3 * en.get_damage_mult("fire")
                            if en.hit(dmg):
                                tower_sound_3.play()
                            self.damage_numbers.append([en.x, en.y - 40, str(int(dmg)), 30])
                    self.damage_numbers.append([hit_enemy.x, hit_enemy.y - 60, "METEOR!", 40, (255, 150, 50)])
                    self.scorch_marks.append([hit_enemy.x, hit_enemy.y, 600])
                    self.shockwaves.append(Shockwave(hit_enemy.x, hit_enemy.y, max_r=100, color=(255, 150, 50)))
                    self.screen_shake = 8
                elif proj.special == "armageddon":
                    # Armageddon: obrazenia dla wszystkich
                    for en in self.enemies:
                        if not en.dying and not en.dead and not en.reached_end:
                            en.hit(30)
                    self.damage_numbers.append([hit_enemy.x, hit_enemy.y - 60, "ARMAGEDDON!", 50, (220, 100, 255)])
                    self.shockwaves.append(Shockwave(hit_enemy.x, hit_enemy.y, max_r=150, color=(200, 100, 255)))
                    self.screen_shake = 12
                elif proj.special == "golden":
                    # Golden: oznaczenie podwojnej kasy
                    hit_enemy._gold_marked = True
                    dmg = proj.damage * hit_enemy.get_damage_mult(proj.damage_type)
                    hit_enemy.hit(dmg)
                    self.damage_numbers.append([hit_enemy.x, hit_enemy.y - 40, str(int(dmg)), 30, (255, 215, 0)])
                # Splash damage: obrazenia obszarowe dla Fire/Blaze.
                elif proj.splash_radius > 0:
                    for en in self.enemies:
                        if en.dying or en.dead or en.reached_end:
                            continue
                        dist = math.sqrt((en.x - hit_enemy.x)**2 + (en.y - hit_enemy.y)**2)
                        if dist < proj.splash_radius:
                            dmg = proj.damage * crit_mult * en.get_damage_mult(proj.damage_type)
                            if en.hit(dmg):
                                tower_sound_3.play()
                            dmg_text = str(int(dmg)) + ("!" if is_crit else "")
                            dmg_color = (255, 220, 50) if is_crit else None
                            self.damage_numbers.append([en.x, en.y - 40, dmg_text, 30, dmg_color])
                            self.stats_damage += int(dmg)
                else:
                    dmg = proj.damage * crit_mult * hit_enemy.get_damage_mult(proj.damage_type)
                    if hit_enemy.hit(dmg):
                        tower_sound_3.play()
                    dmg_text = str(int(dmg)) + ("!" if is_crit else "")
                    dmg_color = (255, 220, 50) if is_crit else None
                    self.damage_numbers.append([hit_enemy.x, hit_enemy.y - 40, dmg_text, 30, dmg_color])
                    self.stats_damage += int(dmg)
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
        """Ekran koncowy. Zwraca 'restart', 'continue' (endless), lub 'quit'."""
        big_font = self.font_big70
        small_font = self.font_small30
        title = "YOU WIN! The island is saved!" if won else "YOU LOSE! The monsters broke through!"
        color = (60, 200, 90) if won else (220, 60, 60)
        # Przyciski
        if won:
            restart_rect = pygame.Rect(self.width//2 - 330, self.height//2 + 160, 200, 60)
            continue_rect = pygame.Rect(self.width//2 - 100, self.height//2 + 160, 200, 60)
            quit_rect = pygame.Rect(self.width//2 + 130, self.height//2 + 160, 200, 60)
        else:
            restart_rect = pygame.Rect(self.width//2 - 220, self.height//2 + 160, 200, 60)
            quit_rect = pygame.Rect(self.width//2 + 20, self.height//2 + 160, 200, 60)
            continue_rect = None
        # Statyczna klatka tla (bez migotania - rysujemy raz)
        self.win.blit(self.bg, (0, 0))
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.win.blit(overlay, (0, 0))
        text = big_font.render(title, 1, color)
        self.win.blit(text, (self.width // 2 - text.get_width() // 2, self.height // 2 - 60))
        sub = small_font.render("Wave reached: " + str(self.wave + 1) + " / " + str(len(waves)), 1, (255, 255, 255))
        self.win.blit(sub, (self.width // 2 - sub.get_width() // 2, self.height // 2 + 20))
        # Statystyki koncowe (R12)
        stats_font = self.font_stats24
        stats = [
            f"Kills: {self.stats_kills}",
            f"Gold earned: {self.stats_gold}",
            f"Damage dealt: {self.stats_damage}",
        ]
        for i, s in enumerate(stats):
            label = stats_font.render(s, True, (200, 200, 200))
            self.win.blit(label, (self.width // 2 - label.get_width() // 2, self.height // 2 + 55 + i * 30))
        pygame.display.update()
        # Petla czeka na klikniecie przycisku (bez przerysowywania tla - brak migotania)
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    if restart_rect.collidepoint(pos):
                        return "restart"
                    if quit_rect.collidepoint(pos):
                        return "quit"
                    if continue_rect and continue_rect.collidepoint(pos):
                        return "continue"
            # Rysuj przyciski (tylko przyciski sie odswiezaja)
            buttons = [
                (restart_rect, "RESTART", (60, 180, 80)),
                (quit_rect, "QUIT", (180, 60, 60)),
            ]
            if continue_rect:
                buttons.insert(1, (continue_rect, "CONTINUE", (60, 120, 220)))
            for rect, label_text, btn_color in buttons:
                pygame.draw.rect(self.win, btn_color, rect, border_radius=10)
                pygame.draw.rect(self.win, (255, 255, 255), rect, 2, border_radius=10)
                label = small_font.render(label_text, True, (255, 255, 255))
                self.win.blit(label, (rect.x + rect.width//2 - label.get_width()//2,
                                      rect.y + rect.height//2 - label.get_height()//2))
            pygame.display.update()
        return "quit"
        
    def draw(self):
        self._frame += 1
        # Jeden odczyt czasu na klatke (wydajnosc) - uzywany w calej klatce
        self._now = pygame.time.get_ticks()
        self._now_s = self._now / 1000.0
        # A6: wstrzas ekranu
        ox, oy = 0, 0
        if self.screen_shake > 0:
            ox = random.randint(-4, 4)
            oy = random.randint(-4, 4)
        self.win.blit(self.bg, (ox, oy))
        # Wizualne: niebo i woda
        self.draw_sky_effects()
        self.draw_water_effects()
        self.draw_ambient_life()
        # B1: cykl dnia/nocy - przyciemnienie
        self.draw_day_night()
        self.ship.draw(self.win)
        # Iskry z komina statku (gdy plynie)
        if self.ship.state in (self.ship.IN, self.ship.OUT) and self._frame % 5 == 0:
            self.particles.burst(self.ship.x, self.ship.y - 30, (255, 150, 50),
                               count=2, speed=1.5, life=25, size=3, gravity=-0.15)
        # 5: linia synergii miedzy wiezami tego samego typu
        drawn_links = set()
        for tw in self.towers:
            # Q15: filtr - przyciemnij niepasujace
            if self.tower_filter and not type(tw).__name__.startswith(self.tower_filter):
                continue
            if tw._synergy > 1.0:
                for tw2 in self.towers:
                    if tw2 is not tw and type(tw2).__name__ == type(tw).__name__:
                        _dx, _dy = tw2.x - tw.x, tw2.y - tw.y
                        if _dx*_dx + _dy*_dy < 10000:
                            key = tuple(sorted([id(tw), id(tw2)]))
                            if key not in drawn_links:
                                drawn_links.add(key)
                                pygame.draw.line(self.win, (255, 215, 0, 120),
                                               (tw.x, tw.y - 20), (tw2.x, tw2.y - 20), 2)
        for tw in self.towers:
            tw.draw(self.win)  # draw() rysuje tez okrag zasiegu (bez duplikatu)
        # Q15: przyciemnij odfiltrowane
        if self.tower_filter:
            dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 100))
            self.win.blit(dim, (0, 0))
            for tw in self.towers:
                if type(tw).__name__.startswith(self.tower_filter):
                    tw.draw(self.win)
        if self.moving_object:
            self.moving_object.draw(self.win)
            self.moving_object.draw_radius(self.win)
        # Trupy pod wrogami (znikaja stopniowo)
        for img, x, y, timer in self.corpses:
            alpha = min(255, timer * 2)
            corpse = img.copy()
            corpse.set_alpha(alpha)
            self.win.blit(corpse, (x - corpse.get_width()/2, y - corpse.get_height()/2 - 35))
        # 1: Uszkodzenia zamku (baza na koncu sciezki)
        self.draw_castle_damage()
        # 10: podglad trasy wroga na hover (co 3. klatke - wydajnosc)
        if self._frame % 3 == 0:
            self._hover_enemy = None
            mx, my = pygame.mouse.get_pos()
            for en in self.enemies:
                if en.dying or en.dead or en.reached_end:
                    continue
                _dx, _dy = mx - en.x, my - (en.y - 35)
                if _dx*_dx + _dy*_dy < 1225:
                    self._hover_enemy = en
                    break
        if self._hover_enemy is not None:
            en = self._hover_enemy
            hlabel = self.font_e14.render(f"HP: {int(en.health)}/{en.max_health}", True, (255, 180, 180))
            self.win.blit(hlabel, (en.x - hlabel.get_width()//2, en.y - 95))
        # Q9: podswietl wrogow w zasiegu wybranej wiezy
        if self.selected_tower:
            st = self.selected_tower
            for en in self.enemies:
                if en.dying or en.dead or en.reached_end:
                    continue
                _dx, _dy = en.x - st.x, en.y - st.y
                if _dx*_dx + _dy*_dy < st.range * st.range:
                    pygame.draw.circle(self.win, (255, 255, 100, 100),
                                     (int(en.x), int(en.y - 35)), 30, 2)
        # 7: deszcz
        if self.raining and not self.paused:
            for i, (x, y, speed) in enumerate(self.raindrops):
                y += speed
                if y > self.height:
                    y = -10
                    x = random.randint(0, self.width)
                self.raindrops[i] = (x, y, speed)
                pygame.draw.line(self.win, (150, 180, 220, 120), (x, y), (x - 3, y + 12), 2)
        elif self.raining:
            for x, y, speed in self.raindrops:
                pygame.draw.line(self.win, (150, 180, 220, 120), (x, y), (x - 3, y + 12), 2)
        for en in self.enemies:
            en.draw(self.win)
        for proj in self.projectiles:
            proj.draw(self.win)
        # Latajace liczby obrazen
        font_dmg = self.font_dmg18
        font_crit = self.font_crit22
        for item in self.damage_numbers:
            # Obsluga starego formatu (4 elementy) i nowego (5 z kolorem)
            if len(item) == 5:
                x, y, text, timer, color = item
            else:
                x, y, text, timer = item
                color = None
            if color:
                label = font_crit.render(text, True, color)
            else:
                label = font_dmg.render(text, True, (255, 100, 100))
            self.win.blit(label, (x - label.get_width()//2, y))
        # V3: banner fali
        if self.wave_banner_timer > 0:
            alpha = min(255, self.wave_banner_timer * 3)
            banner_font = self.font_banner64
            label = banner_font.render(self.wave_banner_text, True, (255, 255, 255))
            # Cien pod napisem
            shadow = banner_font.render(self.wave_banner_text, True, (0, 0, 0))
            cx = self.width // 2
            cy = self.height // 3
            self.win.blit(shadow, (cx - label.get_width()//2 + 3, cy + 3))
            self.win.blit(label, (cx - label.get_width()//2, cy))
        # V4: muzzle flashes
        for x, y, timer in self.muzzle_flashes:
            if timer > 0:
                radius = 12 + (6 - timer) * 2
                flash = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                pygame.draw.circle(flash, (255, 220, 100, timer * 40), (radius, radius), radius)
                self.win.blit(flash, (x - radius, y - radius))
        # Powiadomienia o zlocie za fale (widoczne, pod HUDem)
        gold_font = self.font_gold28
        for i, (text, timer) in enumerate(self.gold_notifications):
            alpha = min(255, timer * 2)
            # Tlo powiadomienia
            label = gold_font.render(text, True, (255, 215, 0))
            bg_w = label.get_width() + 30
            bg = pygame.Surface((bg_w, 44), pygame.SRCALPHA)
            pygame.draw.rect(bg, (8, 18, 38, 190), bg.get_rect(), border_radius=22)
            pygame.draw.rect(bg, (255, 215, 0, 150), bg.get_rect(), 2, border_radius=22)
            bx = self.width // 2 - bg_w // 2
            by = 70 + i * 50
            self.win.blit(bg, (bx, by))
            self.win.blit(label, (bx + 15, by + 22 - label.get_height() // 2))
        # R1: Pasek HP bossa - wyrazisty, nie zlewa sie z UI
        for en in self.enemies:
            if isinstance(en, Boss) and not en.dying and not en.dead:
                bar_w, bar_h = 500, 22
                bx = self.width // 2 - bar_w // 2
                by = 8
                ratio = max(0.0, min(1.0, en.health / en.max_health))
                # Tlo - ciemne z czerwona obwiednia
                bg = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
                pygame.draw.rect(bg, (15, 5, 5, 240), bg.get_rect(), border_radius=11)
                pygame.draw.rect(bg, (200, 50, 50, 255), bg.get_rect(), 3, border_radius=11)
                self.win.blit(bg, (bx, by))
                # Wypelnienie z gradientem
                fill_w = int((bar_w - 6) * ratio)
                if fill_w > 0:
                    fg = pygame.Surface((fill_w, bar_h - 6), pygame.SRCALPHA)
                    # Gradient: jasna czerwien u gory
                    for i in range(bar_h - 6):
                        t = i / (bar_h - 6)
                        r = int(230 - t * 40)
                        g = int(70 - t * 30)
                        pygame.draw.line(fg, (r, g, 50), (0, i), (fill_w, i))
                    # Zaokraglenie przez maske
                    mask = pygame.Surface((fill_w, bar_h - 6), pygame.SRCALPHA)
                    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=8)
                    fg.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    self.win.blit(fg, (bx + 3, by + 3))
                # Czaszka + nazwa
                boss_font = self.font_boss16
                skull = "☠ BOSS" if not getattr(en, 'final', False) else "☠ FINAL BOSS"
                if getattr(en, 'enraged', False):
                    skull += " (ENRAGED!)"
                    scol = (255, 100, 100)
                else:
                    scol = (255, 220, 220)
                blabel = boss_font.render(skull, True, scol)
                # Cien pod tekstem
                shadow = boss_font.render(skull, True, (0, 0, 0))
                tx = bx + bar_w // 2 - blabel.get_width() // 2
                ty = by + bar_h // 2 - blabel.get_height() // 2
                self.win.blit(shadow, (tx + 1, ty + 1))
                self.win.blit(blabel, (tx, ty))
                break
        
        # R2: Przycisk "Nastepna fala" - wczesniejsze przywolanie za bonus
        # (gdy statek odplynal ale wrogowie jeszcze sa na mapie)
        if self.waiting_for_clear and len(self.enemies) > 0 and not self.won and not self.last_wave_done:
            btn_w, btn_h = 220, 44
            bx = self.width - btn_w - 20
            by = 70
            self.early_wave_rect = pygame.Rect(bx, by, btn_w, btn_h)
            # Bonus zalezy od liczby pozostalych wrogow
            bonus = len(self.enemies) * 5
            btn_bg = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
            pygame.draw.rect(btn_bg, (30, 90, 50, 230), btn_bg.get_rect(), border_radius=12)
            pygame.draw.rect(btn_bg, (100, 255, 150, 180), btn_bg.get_rect(), 2, border_radius=12)
            self.win.blit(btn_bg, (bx, by))
            btn_font = self.font_btn18
            label = btn_font.render(f"NEXT WAVE +{bonus}$", True, (200, 255, 210))
            self.win.blit(label, (bx + btn_w//2 - label.get_width()//2, by + btn_h//2 - label.get_height()//2))
        else:
            self.early_wave_rect = None
        
        # Ability dock - pasek umiejetnosci na dole
        self.draw_ability_dock()
        
        # U9: podglad zasiegu wiezy ze sklepu (hover)
        # Q12: porownanie DPS
        if not self.moving_object:
            pos = pygame.mouse.get_pos()
            hovered = self.menu.get_hovered(pos[0], pos[1])
            if hovered:
                tmp = {"t1": WoodenTower, "t2": MetalTower, "t3": GoldenTower,
                       "t4": FireTower, "t5": BlazeTower}.get(hovered)
                if tmp:
                    tw = tmp(pos[0], pos[1])
                    tw.draw_radius(self.win)
                    # Q12: DPS vs srednia
                    avg = sum(t.damage for t in self.towers) / max(1, len(self.towers))
                    diff = tw.damage - avg
                    cfont = self.font_c13
                    ctxt = f"DPS {tw.damage} ({'+' if diff >= 0 else ''}{diff:.0f} vs avg)"
                    ccol = (100, 255, 100) if diff >= 0 else (255, 150, 150)
                    clabel = cfont.render(ctxt, True, ccol)
                    self.win.blit(clabel, (pos[0] + 15, pos[1] - 25))
        # U10: pokaz wszystkie zasiegi (R)
        if self.show_all_ranges:
            for tw in self.towers:
                tw.draw_radius(self.win)
        
        # R4: siatka stawiania z walidacja (gdy przecigasz wieze)
        if self.moving_object:
            self.draw_placement_grid(self.win, self.moving_object.x, self.moving_object.y)
        
        # 9: raport po fali
        if self.wave_report:
            text, timer = self.wave_report
            rfont = self.font_r16
            label = rfont.render(text, True, (220, 230, 240))
            bg_w = label.get_width() + 30
            bg = pygame.Surface((bg_w, 36), pygame.SRCALPHA)
            pygame.draw.rect(bg, (15, 25, 40, 220), bg.get_rect(), border_radius=18)
            pygame.draw.rect(bg, (100, 150, 200, 120), bg.get_rect(), 1, border_radius=18)
            bx = self.width // 2 - bg_w // 2
            by = self.height - 120
            self.win.blit(bg, (bx, by))
            self.win.blit(label, (bx + 15, by + 18 - label.get_height() // 2))
        
        # Spalenizna
        for x, y, timer in self.scorch_marks:
            s = pygame.Surface((50, 30), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (30, 30, 30, min(150, timer)), s.get_rect())
            self.win.blit(s, (x - 25, y - 15))
        # Czasteczki i efekty
        self.particles.draw(self.win)
        for s in self.shockwaves:
            s.draw(self.win)
        for c in self.coins:
            c.draw(self.win)
        # A4: chmury (wolno, pozycja bazowa + przesuniecie czasowe)
        t = self._now_s
        for i, (base_x, cy, size) in enumerate(self.clouds):
            cx = (base_x + t * 8) % (self.width + 200) - 100
            for ox in [-20, 0, 20]:
                pygame.draw.circle(self.win, (255, 255, 255, 90), (int(cx + ox), int(cy)), size // 2)
        # A9: mewy
        for i, (base_x, gy, phase) in enumerate(self.seagulls):
            gx = (base_x + t * 12) % (self.width + 100) - 50
            wing = math.sin(t * 6 + phase) * 8
            pygame.draw.line(self.win, (80, 80, 80), (gx - 12, gy + wing), (gx, gy), 2)
            pygame.draw.line(self.win, (80, 80, 80), (gx, gy), (gx + 12, gy + wing), 2)
        # B5: liscie
        for i, (base_x, ly) in enumerate(self.leaves):
            lx = (base_x + t * 6) % (self.width + 40) - 20
            ly = ly + math.sin(t * 2 + i) * 10
            pygame.draw.circle(self.win, (120, 180, 80, 150), (int(lx), int(ly)), 3)
        # A9: dym z namiotu (pozycja przyblizona)
        for i in range(2):
            sx = 850 + i * 10
            sy = 550 - ((t * 20 + i * 30) % 60)
            alpha = int(80 * (1 - ((t * 20 + i * 30) % 60) / 60))
            pygame.draw.circle(self.win, (150, 150, 150, alpha), (int(sx), int(sy)), 8)
        # Pochodnie przy zamku (migoczacy ogien)
        for tx, ty in [(240, 330), (320, 330)]:
            flame_h = 12 + 4 * math.sin(t * 10 + tx)
            pygame.draw.polygon(self.win, (255, 120, 20),
                              [(tx-6, ty), (tx, ty-flame_h), (tx+6, ty)])
            pygame.draw.polygon(self.win, (255, 220, 100),
                              [(tx-3, ty), (tx, ty-flame_h*0.6), (tx+3, ty)])
            pygame.draw.circle(self.win, (255, 200, 120, 60), (tx, ty-8), 18)

        # Motyle (dzien)
        phase = (self.wave // 2) % 4
        if phase in (0, 1):
            for i, (bx, by, ph) in enumerate(self.butterflies):
                bx = (bx + t * 10) % 900 + 100
                by = by + 15 * math.sin(t * 2 + ph)
                wing = 5 + 3 * math.sin(t * 12 + ph)
                pygame.draw.ellipse(self.win, (255, 180, 220), (bx-wing, by-3, wing*2, 6))
        # Kwiaty
        for fx, fy, col in self.flowers:
            pygame.draw.circle(self.win, col, (fx, fy), 4)
            pygame.draw.circle(self.win, (255, 255, 200), (fx, fy), 2)
        # Klucz ptakow (losowo)
        if self._frame % 500 == 0 and len(self.bird_flocks) < 2:
            self.bird_flocks.append([0, random.randint(80, 180), 0])
        for flock in self.bird_flocks[:]:
            flock[0] += 3; flock[2] += 1
            for i in range(5):
                bx = flock[0] - i * 25
                by = flock[1] + abs(i - 2) * 12
                wing = 6 * math.sin(t * 8 + i)
                pygame.draw.line(self.win, (60, 60, 60), (bx-8, by+wing), (bx, by), 2)
                pygame.draw.line(self.win, (60, 60, 60), (bx, by), (bx+8, by+wing), 2)
            if flock[0] > self.width + 100:
                self.bird_flocks.remove(flock)
        # Slady stop bossa
        for fp in self.boss_footprints[:]:
            fp[2] -= 1
            if fp[2] <= 0:
                self.boss_footprints.remove(fp)
            else:
                alpha = int(100 * fp[2] / 300)
                pygame.draw.ellipse(self.win, (60, 50, 40, alpha),
                                  (fp[0]-15, fp[1]-8, 30, 16))
        # Ognisko z tanczacymi
        self.draw_campfire()
        self.draw_chests()
        self.draw_announcements()
        # Q17: zegar sesji
        mins = self.game_time // 3600
        secs = (self.game_time // 60) % 60
        qfont = self.font_q14
        tlabel = qfont.render(f"{mins:02d}:{secs:02d}", True, (200, 200, 200))
        self.win.blit(tlabel, (self.width - 70, self.height - 30))
        
        # 8: wskaznik pauzy z informacja o budowaniu
        if self.paused:
            pfont = self.font_p36
            plabel = self._txt_paused
            sfont = self.font_s16
            slabel = self._txt_paused_sub
            px = self.width // 2 - plabel.get_width() // 2
            py = 60
            # Polprzezroczyste tlo
            bg = pygame.Surface((plabel.get_width() + 40, 70), pygame.SRCALPHA)
            pygame.draw.rect(bg, (0, 0, 0, 150), bg.get_rect(), border_radius=12)
            self.win.blit(bg, (px - 20, py - 10))
            self.win.blit(plabel, (px, py))
            self.win.blit(slabel, (self.width//2 - slabel.get_width()//2, py + 42))
        
        # Q1: pasek postepu fali
        total_to_spawn = sum(self.current_wave)
        spawned = getattr(self, '_wave_total', total_to_spawn + len(self.enemies))
        if not hasattr(self, '_wave_total') or total_to_spawn == 0 and len(self.enemies) == 0:
            # Reset przy nowej fali
            pass
        remaining = total_to_spawn + len(self.enemies)
        # Q2: ostrzezenie o bossie
        next_is_boss = (self.wave + 2) % 4 == 0 or self.wave + 2 == 10
        if next_is_boss and self.waiting_for_clear and not hasattr(self, '_boss_warned'):
            self._boss_warned = True
            self.wave_banner_text = "WARNING: BOSS INCOMING!"
            self.wave_banner_timer = 150
            sound_horn.play()  # Niespodzianka 5: rog ostrzegawczy
        if not self.waiting_for_clear:
            self._boss_warned = False
        
        self.menu.draw(self.win)
        self.draw_hud()

        pygame.display.update()

    def draw_castle_damage(self):
        """1: Wizualne uszkodzenia zamku zaleza od liczby zyc."""
        cx, cy = 300, 375  # koniec sciezki (baza)
        t = self._now_s
        if self.lives <= 15:
            # Pekniecia
            for x1, y1, x2, y2 in [(cx-20, cy-30, cx-5, cy-10), (cx+15, cy-35, cx+5, cy-15),
                                    (cx-10, cy+10, cx-25, cy+30)]:
                pygame.draw.line(self.win, (40, 40, 40), (x1, y1), (x2, y2), 3)
        if self.lives <= 10:
            # Dym (3 smugi)
            for i in range(3):
                sx = cx - 20 + i * 20
                sy = cy - 50 - ((t * 30 + i * 20) % 40)
                alpha = int(120 * (1 - ((t * 30 + i * 20) % 40) / 40))
                s = pygame.Surface((24, 24), pygame.SRCALPHA)
                pygame.draw.circle(s, (100, 100, 100, alpha), (12, 12), 10)
                self.win.blit(s, (sx - 12, sy - 12))
        if self.lives <= 5:
            # Ogien (plomienie)
            for i in range(4):
                fx = cx - 30 + i * 20
                fy = cy - 20
                h = 18 + 8 * math.sin(t * 8 + i * 1.5)
                pts = [(fx - 8, fy), (fx, fy - h), (fx + 8, fy)]
                pygame.draw.polygon(self.win, (255, 120, 20), pts)
                pts2 = [(fx - 4, fy), (fx, fy - h * 0.6), (fx + 4, fy)]
                pygame.draw.polygon(self.win, (255, 220, 80), pts2)

    def announce(self, text):
        """37: ogloszenie spikera - jak w LoL: jedno naraz, nowe zastepuje stare."""
        self.announcements = [[text, 150]]

    def draw_chests(self):
        """21: skrzynie skarbow po bossie (otwieranie + monety)."""
        for ch in self.chests[:]:
            ch[2] += 1
            t = ch[2]
            x, y = ch[0], ch[1]
            # Skrzynia
            pygame.draw.rect(self.win, (101, 67, 33), (x - 22, y - 16, 44, 28), border_radius=4)
            pygame.draw.rect(self.win, (70, 45, 20), (x - 22, y - 16, 44, 28), 2, border_radius=4)
            # Wieko otwiera sie
            lid_open = min(1.0, t / 60)
            lid_y = y - 16 - int(18 * lid_open)
            pygame.draw.rect(self.win, (130, 90, 45), (x - 22, lid_y, 44, 12), border_radius=4)
            # Blask zlota
            if t > 40:
                glow = int(120 + 60 * math.sin(t * 0.2))
                s = pygame.Surface((70, 50), pygame.SRCALPHA)
                pygame.draw.ellipse(s, (255, 215, 0, glow), s.get_rect())
                self.win.blit(s, (x - 35, y - 45))
                if t == 60:
                    self.particles.burst(x, y - 20, (255, 215, 0), count=25, speed=4, size=4)
            if t > 300:
                self.chests.remove(ch)

    def draw_announcements(self):
        """37: jedno ogloszenie naraz (styl LoL) - maly, na gorze, z ciemnym tlem."""
        if not self.announcements:
            return
        a = self.announcements[0]
        a[1] -= 1
        if a[1] <= 0:
            self.announcements.remove(a)
            return
        alpha = min(255, a[1] * 4)
        f = self.font_ann34
        outline = f.render(a[0], True, (20, 20, 20))
        label = f.render(a[0], True, (255, 210, 60))
        pad_x, pad_y = 18, 8
        bg_w = label.get_width() + pad_x * 2
        bg_h = label.get_height() + pad_y * 2
        s = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 170), s.get_rect(), border_radius=16)
        for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            s.blit(outline, (pad_x + ox, pad_y + oy))
        s.blit(label, (pad_x, pad_y))
        s.set_alpha(alpha)
        self.win.blit(s, (self.width // 2 - bg_w // 2, 95))

    def draw_ambient_life(self):
        """11-20, 22-25: zycie na wyspie (animacje 30Hz - pozycje co 2. klatke)."""
        if self._frame % 2 == 0:
            self._ambient_t = self._now_s
        t = self._ambient_t
        phase = (self.wave // 2) % 4
        night = (phase == 2)

        # 11: wodospad na skale
        wx, wy = 1085, 250
        pygame.draw.rect(self.win, (110, 110, 120), (wx - 14, wy - 60, 28, 70), border_radius=6)
        for i in range(6):
            fy = wy - 55 + ((t * 120 + i * 22) % 65)
            pygame.draw.line(self.win, (180, 220, 255, 160), (wx - 8 + i * 3, fy), (wx - 8 + i * 3, fy + 14), 2)
        # Piana u dolu
        for i in range(4):
            px = wx - 12 + i * 8 + 3 * math.sin(t * 3 + i)
            pygame.draw.circle(self.win, (255, 255, 255, 140), (int(px), wy + 12), 4)

        # 13: usuniety wulkan na horyzoncie (na prosbe gracza)

        # 14: balon
        self.balloon_timer -= 1
        if self.balloon_timer <= 0 and self.balloon is None:
            self.balloon = [-80, random.randint(60, 160)]
            self.balloon_timer = random.randint(3000, 5000)
        if self.balloon:
            self.balloon[0] += 0.7
            bx, by = self.balloon
            # Powłoka w paski
            for i, col in enumerate([(220, 60, 60), (255, 220, 80), (60, 140, 220)]):
                pygame.draw.arc(self.win, col, (bx - 26, by - 30, 52, 44), math.pi / 2 + i * 0.5, math.pi / 2 + (i + 1) * 0.5, 9)
            pygame.draw.circle(self.win, (220, 60, 60), (int(bx), int(by - 8)), 24, 0)
            pygame.draw.rect(self.win, (101, 67, 33), (bx - 8, by + 16, 16, 12), border_radius=3)
            pygame.draw.line(self.win, (80, 60, 40), (bx - 14, by + 8), (bx - 8, by + 16), 2)
            pygame.draw.line(self.win, (80, 60, 40), (bx + 14, by + 8), (bx + 8, by + 16), 2)
            if bx > self.width + 80:
                self.balloon = None

        # 12: teczowe rybki
        self.fish_timer -= 1
        if self.fish_timer <= 0:
            self.fish_timer = random.randint(150, 400)
            self.fishes.append([random.randint(150, 950), 655, random.uniform(-2, 2), -7,
                                0, random.choice([(255, 120, 150), (120, 200, 255), (255, 220, 100), (150, 255, 180)])])
        for f in self.fishes[:]:
            f[4] += 1
            f[0] += f[2]; f[1] += f[3]; f[3] += 0.35
            pygame.draw.ellipse(self.win, f[5], (f[0] - 8, f[1] - 4, 16, 8))
            if f[1] > 670:
                self.fishes.remove(f)

        # 15: wieloryb
        self.whale_timer -= 1
        if self.whale_timer <= 0 and self.whale is None:
            self.whale = [random.randint(200, 900), 0]
            self.whale_timer = random.randint(2800, 4500)
        if self.whale:
            self.whale[1] += 1
            wt = self.whale[1]
            x = self.whale[0]
            # Wynurzenie: 0-60 w gore, 60-140 na gorze, 140-200 w dol
            if wt < 200:
                depth = -30 * math.sin(math.pi * min(1.0, wt / 200))
                y = 660 + depth
                pygame.draw.ellipse(self.win, (70, 90, 120), (x - 45, y - 14, 90, 28))
                pygame.draw.polygon(self.win, (70, 90, 120), [(x + 35, y), (x + 55, y - 18), (x + 42, y)])
                if 60 < wt < 140 and wt % 20 == 0:
                    self.particles.burst(x - 10, y - 20, (200, 230, 255), count=4, speed=2, life=25, size=3, gravity=-0.1)
            else:
                self.whale = None

        # 16: papugi na palmach
        for px, py, col in [(205, 400, (220, 60, 60)), (215, 408, (60, 180, 80))]:
            flap = 6 * math.sin(t * 10 + px)
            pygame.draw.ellipse(self.win, col, (px - 7, py - 5, 14, 10))
            pygame.draw.circle(self.win, col, (int(px + 8), int(py - 4)), 5)
            pygame.draw.polygon(self.win, (255, 200, 60), [(px + 12, py - 4), (px + 17, py - 2), (px + 12, py)])
            # Skrzydlo
            pygame.draw.ellipse(self.win, (min(255, col[0]+40), min(255, col[1]+40), col[2]), (px - 9, py - 8 + flap * 0.3, 12, 6))

        # 17: kraby na plazy
        for cr in self.crabs:
            cr[2] += 0.05 * cr[3]
            cr[0] += 0.6 * cr[3]
            if cr[0] > 1050: cr[3] = -1
            if cr[0] < 80: cr[3] = 1
            wob = 3 * math.sin(cr[2] * 8)
            pygame.draw.ellipse(self.win, (200, 80, 60), (cr[0] - 9, cr[1] - 6 + wob * 0.3, 18, 12))
            # Szczypce
            pygame.draw.circle(self.win, (220, 100, 70), (int(cr[0] + 10 * cr[3]), int(cr[1] - 8)), 4)
            # Nogi
            for li in range(3):
                pygame.draw.line(self.win, (170, 60, 45), (cr[0] - 6 + li * 6, cr[1] + 5), (cr[0] - 8 + li * 6, cr[1] + 11), 2)

        # 18: macka osmiornicy
        self.octo_timer -= 1
        if self.octo_timer <= 0 and self.octo is None:
            self.octo = [random.randint(150, 950), 0]
            self.octo_timer = random.randint(3500, 5500)
        if self.octo:
            self.octo[1] += 1
            ot = self.octo[1]
            h = 70 * math.sin(math.pi * min(1.0, ot / 180)) if ot < 180 else 0
            if h > 2:
                x = self.octo[0]
                sway = 12 * math.sin(t * 2)
                pts = [(x, 665)]
                for s in range(1, 6):
                    pts.append((x + sway * s / 5, 665 - h * s / 5))
                pygame.draw.lines(self.win, (150, 60, 120), False, pts, 9)
                if ot >= 180:
                    self.octo = None

        # 19: latarnia morska - usunieta na prosbe gracza

        # 20: wrak statku - usuniety na prosbe gracza

        # 22: dmiace ruiny
        ux, uy = 950, 360
        for i, (cxo, h) in enumerate([(-18, 46), (0, 60), (18, 38)]):
            pygame.draw.rect(self.win, (140, 135, 125), (ux + cxo - 7, uy - h, 14, h), border_radius=3)
            pygame.draw.rect(self.win, (110, 105, 95), (ux + cxo - 10, uy - h - 8, 20, 8), border_radius=2)
        for i in range(2):
            sx = ux + i * 14 - 7 + 6 * math.sin(t + i * 2)
            sy = uy - 66 - ((t * 14 + i * 40) % 50)
            alpha = int(70 * (1 - ((t * 14 + i * 40) % 50) / 50))
            pygame.draw.circle(self.win, (150, 150, 150, alpha), (int(sx), int(sy)), 7)

        # 23: swiecace grzyby (noc)
        if night:
            for gx, gy in [(350, 555), (365, 560), (950, 470)]:
                glow = 90 + 50 * math.sin(t * 3 + gx)
                pygame.draw.circle(self.win, (120, 220, 255, int(glow)), (gx, gy - 6), 10)
                pygame.draw.ellipse(self.win, (200, 120, 140), (gx - 6, gy - 10, 12, 10))
                pygame.draw.rect(self.win, (230, 220, 200), (gx - 2, gy - 2, 4, 8))

        # 24: pajeczyna z pajakiem - usunieta na prosbe gracza

        # 25: kameleon na lisciu
        self.chameleon_hue = (self.chameleon_hue + 0.4) % 360
        h = self.chameleon_hue
        # Prosta konwersja HSV->RGB
        c1 = abs((h / 60) % 2 - 1)
        r_ = int(255 * (1 - c1 * 0.6)); g_ = int(200 + 55 * math.sin(math.radians(h))); b_ = int(150 + 80 * math.cos(math.radians(h * 1.3)))
        kx, ky = 300, 480
        pygame.draw.ellipse(self.win, (60, 140, 70), (kx - 26, ky - 6, 52, 16))
        pygame.draw.ellipse(self.win, (r_, max(0,g_), max(0,b_)), (kx - 12, ky - 14, 24, 14))
        pygame.draw.circle(self.win, (r_, max(0,g_), max(0,b_)), (kx + 14, ky - 12), 7)
        pygame.draw.circle(self.win, (255, 255, 255), (kx + 16, ky - 13), 3)
        pygame.draw.circle(self.win, (20, 20, 20), (kx + 17, ky - 13), 1.5)
        # Ogon zwiniety
        pygame.draw.arc(self.win, (r_, max(0,g_), max(0,b_)), (kx - 30, ky - 16, 18, 18), 0, math.pi * 1.5, 4)

    def draw_campfire(self):
        t = self._now_s
        cx, cy = 830, 385  # na trawie przed wejsciem do namiotu (poziom ziemi)
        for i in range(8):
            ang = i * math.pi / 4
            pygame.draw.circle(self.win, (120, 120, 120),
                             (int(cx + 18 * math.cos(ang)), int(cy + 10 * math.sin(ang))), 6)
        pygame.draw.line(self.win, (101, 67, 33), (cx - 12, cy), (cx + 12, cy - 8), 4)
        for i, (col, h) in enumerate([((255, 80, 20), 28), ((255, 160, 40), 20), ((255, 230, 120), 12)]):
            fh = h + 6 * math.sin(t * 12 + i * 2)
            pygame.draw.polygon(self.win, col, [(cx - 10 + i*2, cy), (cx, cy - fh), (cx + 10 - i*2, cy)])
        if random.random() < 0.3:
            self.particles.burst(cx, cy - 20, (255, 180, 80), count=1, speed=1, life=20, size=2, gravity=-0.12)
        mx = cx - 45 + 8 * math.sin(t * 3)
        my = cy + 5 - abs(10 * math.sin(t * 6))
        pygame.draw.circle(self.win, (255, 200, 170), (int(mx), int(my - 28)), 8)
        pygame.draw.line(self.win, (70, 50, 120), (mx, my - 20), (mx, my), 4)
        ls = 8 * math.sin(t * 6)
        pygame.draw.line(self.win, (50, 50, 80), (mx, my), (mx - 8 + ls, my + 14), 3)
        pygame.draw.line(self.win, (50, 50, 80), (mx, my), (mx + 8 - ls, my + 14), 3)
        sa = -0.5 + 0.4 * math.sin(t * 6)
        sx2, sy2 = mx + 25 * math.cos(sa), (my - 20) + 25 * math.sin(sa)
        pygame.draw.line(self.win, (101, 67, 33), (mx + 5, my - 15), (sx2, sy2), 3)
        pygame.draw.polygon(self.win, (180, 180, 180), [(sx2, sy2), (sx2 - 8, sy2 + 4), (sx2 - 4, sy2 - 6)])
        wx = cx + 45 + 8 * math.cos(t * 2.5)
        wy = cy + 5
        spin = t * 4
        pygame.draw.polygon(self.win, (220, 100, 150), [(wx, wy - 20), (wx - 12, wy + 8), (wx + 12, wy + 8)])
        pygame.draw.circle(self.win, (255, 210, 180), (int(wx), int(wy - 28)), 7)
        pygame.draw.circle(self.win, (150, 80, 40),
                         (int(wx + 10 * math.cos(spin)), int(wy - 30 + 6 * math.sin(spin))), 4)
        panx, pany = wx + 20 * math.cos(spin + 1), (wy - 15) + 12 * math.sin(spin + 1)
        pygame.draw.line(self.win, (255, 210, 180), (wx, wy - 18), (panx, pany), 3)
        pygame.draw.circle(self.win, (80, 80, 80), (int(panx), int(pany)), 7)

    def draw_day_night(self):
        """B1: Cykl dnia/nocy - przyciemnienie co 2 fale (nakladki prerenderowane)."""
        phase = (self.wave // 2) % 4  # 0=dzien, 1=zachod, 2=noc, 3=swit
        t = self._now_s
        if phase == 0:
            # Dzien - brak nakladki (oszczednosc), tylko cienie chmur
            self.morning_fog = 0
            for i, (base_x, cy, size) in enumerate(self.clouds):
                cx = (base_x + t * 8) % (self.width + 200) - 100
                shadow = pygame.Surface((size * 3, size), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow, (0, 0, 0, 40), shadow.get_rect())
                self.win.blit(shadow, (cx - size * 1.5 + 30, 450))
            return
        if phase == 1:
            self.win.blit(self._overlay_sunset, (0, 0))
        elif phase == 2:
            self.win.blit(self._overlay_night, (0, 0))
            # B10: latarnie w nocy
            for x, y in [(400, 500), (600, 480), (800, 460), (500, 420)]:
                pygame.draw.circle(self.win, (255, 220, 120, 80), (x, y), 25)
                pygame.draw.circle(self.win, (255, 240, 180), (x, y), 6)
        elif phase == 3:
            self.win.blit(self._overlay_dawn, (0, 0))
            # Mgla poranna (15s)
            if self.morning_fog < 900:
                self.morning_fog += 1
                fog = pygame.Surface((self.width, 200), pygame.SRCALPHA)
                fog.fill((220, 230, 240, int(60 * (1 - self.morning_fog / 900))))
                self.win.blit(fog, (0, 520))
        # B4: tecza po deszczu (10s po koncu deszczu)
        if hasattr(self, '_rainbow_timer') and self._rainbow_timer > 0:
            self._rainbow_timer -= 1
            colors = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255)]
            for i, c in enumerate(colors):
                pygame.draw.arc(self.win, (*c, 100), 
                              (self.width//2 - 200, 100, 400, 200), 
                              math.pi, 2 * math.pi, 8 - i)
        # B6: blyskawice w deszczu
        if self.raining:
            if random.random() < 0.005:
                self.lightning_timer = 8
            if self.lightning_timer > 0:
                self.lightning_timer -= 1
                flash = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                flash.fill((255, 255, 255, int(80 * self.lightning_timer / 8)))
                self.win.blit(flash, (0, 0))
                # Blyskawica
                lx = random.randint(200, 900)
                pts = [(lx, 0)]
                for j in range(8):
                    pts.append((lx + random.randint(-30, 30), (j+1) * 60))
                pygame.draw.lines(self.win, (255, 255, 200), False, pts, 3)

    def save_game(self):
        """Q11: Zapis gry do pliku."""
        import pickle
        data = {
            'wave': self.wave, 'money': self.money, 'lives': self.lives,
            'towers': [(type(t).__name__, t.x, t.y, t.level) for t in self.towers],
            'stats_kills': self.stats_kills, 'stats_gold': self.stats_gold,
        }
        with open('savegame.dat', 'wb') as f:
            pickle.dump(data, f)
        self.gold_notifications.append(["Game saved (F5)", 120])

    def load_game(self):
        """Q11: Wczytaj gre z pliku."""
        import pickle, os
        if not os.path.exists('savegame.dat'):
            return
        with open('savegame.dat', 'rb') as f:
            data = pickle.load(f)
        self.wave = data['wave']
        self.money = data['money']
        self.lives = data['lives']
        self.stats_kills = data['stats_kills']
        self.stats_gold = data['stats_gold']
        self.towers = []
        tower_map = {"WoodenTower": WoodenTower, "MetalTower": MetalTower,
                     "GoldenTower": GoldenTower, "FireTower": FireTower,
                     "BlazeTower": BlazeTower}
        for name, x, y, level in data['towers']:
            tw = tower_map[name](x, y)
            for _ in range(level - 1):
                tw.upgrade(0)
            self.towers.append(tw)
            self._recalc_synergy()
        self.enemies = []
        self.current_wave = waves[self.wave][:]
        self.gold_notifications.append(["Game loaded (F9)", 120])

    def draw_sky_effects(self):
        """Wizualne: niebo (slonce, ksiezyc, gwiazdy, zorza, spadajace gwiazdy)."""
        t = self._now_s
        phase = (self.wave // 2) % 4
        # Slonce w dzien / ksiezyc w nocy
        if phase in (0, 1, 3):
            sun_x = 900 - (self.wave % 2) * 200
            sun_y = 80
            pygame.draw.circle(self.win, (255, 240, 150, 200), (sun_x, sun_y), 35)
            pygame.draw.circle(self.win, (255, 250, 200), (sun_x, sun_y), 25)
        if phase == 2:
            # Ksiezyc
            pygame.draw.circle(self.win, (220, 220, 240), (850, 70), 28)
            pygame.draw.circle(self.win, (15, 15, 35), (842, 64), 24)  # krater
            # Migoczace gwiazdy
            for i in range(30):
                sx = (i * 173) % self.width
                sy = (i * 97) % 180
                tw = 100 + 80 * math.sin(t * 3 + i)
                pygame.draw.circle(self.win, (255, 255, 255, int(tw)), (sx, sy), 2)
            # Spadajace gwiazdy (losowo)
            if random.random() < 0.01 and len(self.shooting_stars) < 3:
                self.shooting_stars.append([random.randint(0, self.width), 0, random.randint(-8, -4)])
            for s in self.shooting_stars[:]:
                s[0] += 6; s[1] -= s[2]
                pygame.draw.line(self.win, (255, 255, 255, 200), (s[0], s[1]), (s[0]-20, s[1]+10), 2)
                if s[1] < -20:
                    self.shooting_stars.remove(s)
            # Zorza polarna
            for i in range(5):
                ax = 200 + i * 150
                ay = 60 + 20 * math.sin(t * 0.8 + i)
                alpha = int(60 + 40 * math.sin(t * 1.2 + i * 2))
                s = pygame.Surface((100, 80), pygame.SRCALPHA)
                pygame.draw.ellipse(s, (100, 255, 180, alpha), s.get_rect())
                self.win.blit(s, (ax - 50, ay - 40))
            # Swietliki
            for fx, fy in self.fireflies:
                glow = 100 + 80 * math.sin(t * 4 + fx)
                pygame.draw.circle(self.win, (255, 255, 150, int(glow)), (fx, fy), 3)

    def draw_water_effects(self):
        """Wizualne: woda (fale, odbicia, kilwater, pecherzyki)."""
        t = self._now_s
        # Fale (3 warstwy)
        for layer in range(3):
            for i in range(20):
                wx = (i * 60 + t * (10 + layer * 5)) % (self.width + 60) - 30
                wy = 640 + layer * 25 + 8 * math.sin(t * 1.5 + i + layer)
                alpha = 80 - layer * 20
                pygame.draw.arc(self.win, (255, 255, 255, alpha),
                              (wx - 25, wy - 8, 50, 16), math.pi, 2 * math.pi, 2)
        # Kilwater statku
        if self.ship.state in (self.ship.IN, self.ship.OUT):
            for i in range(8):
                wx = self.ship.x - i * 15
                wy = self.ship.y + 10 + random.randint(-5, 5)
                alpha = int(120 * (1 - i / 8))
                pygame.draw.circle(self.win, (255, 255, 255, alpha), (int(wx), int(wy)), 6 - i // 2)
        # Odbicie ksiezyca w nocy
        phase = (self.wave // 2) % 4
        if phase == 2:
            for i in range(10):
                mx = 850 + random.randint(-20, 20)
                my = 650 + i * 8
                pygame.draw.line(self.win, (220, 220, 240, 100), (mx - 15, my), (mx + 15, my), 2)
        # Pecherzyki przy brzegu
        for i in range(8):
            bx = (i * 140 + t * 20) % self.width
            by = 630 + 5 * math.sin(t * 2 + i)
            pygame.draw.circle(self.win, (200, 230, 255, 120), (int(bx), int(by)), 3)
        # Fale o skaly (splash)
        if random.random() < 0.1:
            self.particles.burst(150, 620, (255, 255, 255), count=3, speed=2, life=20, size=3)

    def draw_ability_dock(self):
        """Pasek 5 umiejetnosci (po jednej na typ wiezy). Kliknij aby aktywowac."""
        tower_types = [
            ("Wooden", "Rapid Fire", (139, 90, 43)),
            ("Metal", "Frost Nova", (120, 130, 140)),
            ("Golden", "Golden Touch", (212, 175, 55)),
            ("Fire", "Meteor", (220, 80, 40)),
            ("Blaze", "Armageddon", (180, 40, 180)),
        ]
        slot_w, slot_h = 110, 64
        gap = 8
        total_w = 5 * slot_w + 4 * gap
        start_x = self.width // 2 - total_w // 2
        y = self.height - slot_h - 10
        self.ability_slots = []
        
        for i, (tname, aname, color) in enumerate(tower_types):
            x = start_x + i * (slot_w + gap)
            rect = pygame.Rect(x, y, slot_w, slot_h)
            self.ability_slots.append((rect, tname))
            ready_tower = None
            cooling = None
            for tw in self.towers:
                if type(tw).__name__.startswith(tname):
                    if tw.ability_cooldown <= 0:
                        ready_tower = tw
                        break
                    elif cooling is None:
                        cooling = tw
            bg = pygame.Surface((slot_w, slot_h), pygame.SRCALPHA)
            if ready_tower:
                pygame.draw.rect(bg, (*color, 230), bg.get_rect(), border_radius=10)
                pygame.draw.rect(bg, (255, 255, 255, 200), bg.get_rect(), 2, border_radius=10)
            elif cooling:
                pygame.draw.rect(bg, (40, 50, 65, 230), bg.get_rect(), border_radius=10)
                cd_ratio = cooling.ability_cooldown / cooling.ability_max_cooldown
                overlay_h = int(slot_h * cd_ratio)
                pygame.draw.rect(bg, (0, 0, 0, 150), (0, 0, slot_w, overlay_h), border_radius=10)
            else:
                pygame.draw.rect(bg, (30, 35, 45, 180), bg.get_rect(), border_radius=10)
            self.win.blit(bg, (x, y))
            f1 = self.font_f13
            f2 = self.font_f11
            t1 = f1.render(aname, True, (255, 255, 255))
            self.win.blit(t1, (x + slot_w//2 - t1.get_width()//2, y + 6))
            if ready_tower:
                t2 = self._txt_ready
            elif cooling:
                secs = cooling.ability_cooldown // 60
                t2 = f2.render(f"{secs}s", True, (180, 180, 180))
            else:
                t2 = self._txt_no_tower
            self.win.blit(t2, (x + slot_w//2 - t2.get_width()//2, y + 28))
            t3 = f2.render(tname, True, (200, 200, 200))
            self.win.blit(t3, (x + slot_w//2 - t3.get_width()//2, y + 44))

    def draw_placement_grid(self, win, mx, my):
        """R4: Siatka + podswietlenie poprawnosci miejsca."""
        grid = 40
        # Siatka
        for x in range(0, self.width, grid):
            pygame.draw.line(win, (255, 255, 255, 25), (x, 0), (x, self.height), 1)
        for y in range(0, self.height, grid):
            pygame.draw.line(win, (255, 255, 255, 25), (0, y), (self.width, y), 1)
        # Przyciagnij do siatki
        gx = round(mx / grid) * grid
        gy = round(my / grid) * grid
        valid = self.is_valid_placement(gx, gy)
        color = (80, 220, 100, 120) if valid else (220, 80, 80, 120)
        hl = pygame.Surface((grid, grid), pygame.SRCALPHA)
        pygame.draw.rect(hl, color, hl.get_rect(), border_radius=6)
        win.blit(hl, (gx - grid//2, gy - grid//2))
        # Okrag zasiegu w miejscu stawiania
        if hasattr(self.moving_object, 'range'):
            r = self.moving_object.range
            surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (150, 220, 255, 60), (r, r), r, 2)
            win.blit(surf, (gx - r, gy - r))

    def shop_price(self, tower_name):
        """Cena wiezy w sklepie. Mapuje nazwe klasy (woodenTower) na przycisk (t1)."""
        return self.menu.get_item_cost(tower_shop_names.get(tower_name, tower_name))

    def _is_grass(self, x, y):
        """Czy punkt (x, y) to jasna trawa - probka koloru z tla."""
        if 0 <= x < self.width and 0 <= y < self.height:
            r, g, b, _a = self.bg.get_at((int(x), int(y)))
            # Jasna, zoltawo-zielona trawa (nie morski odcien wzgorz)
            return g > 110 and g > r + 15 and b < 80
        return False

    def is_valid_placement(self, x, y):
        """R4: Czy mozna postawic wieze w (x, y)."""
        # Poza mapa / na menu bocznym
        if x < 40 or x > self.width - 200 or y < 40 or y > self.height - 40:
            return False
        # Tylko na trawie
        if not self._is_grass(x, y):
            return False
        # Na drodze (punkty sciezki wroga)
        path = [(480, 590), (600, 560), (750, 530), (900, 495),
                (980, 460), (1020, 430), (980, 385),
                (800, 375), (600, 370), (400, 365), (280, 355)]
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            # Odleglosc punktu od odcinka
            dx, dy = x2 - x1, y2 - y1
            l2 = dx*dx + dy*dy
            if l2 == 0:
                dist = math.hypot(x - x1, y - y1)
            else:
                t = max(0, min(1, ((x - x1)*dx + (y - y1)*dy) / l2))
                px, py = x1 + t*dx, y1 + t*dy
                dist = math.hypot(x - px, y - py)
            if dist < 50:
                return False
        # Na innej wiezy
        for tw in self.towers:
            if math.hypot(x - tw.x, y - tw.y) < 60:
                return False
        return True

    def draw_hud(self):
        # Rzad spojnych "pigulek": fala, zycia, kasa (tla prerenderowane)
        pill_h = self._pill_h
        y = 10
        items = [
            (10, 0, None, "Wave #" + str(self.wave + 1)),
            (200, 1, self._lives_icon, str(self.lives)),
            (340, 2, self._money_icon, str(int(self.display_money))),
        ]
        for x, pi, icon, text in items:
            self.win.blit(self._pills[pi], (x, y))
            w = self._pills[pi].get_width()
            label = self.hud_font.render(text, True, (255, 255, 255))
            cy = y + pill_h // 2 - label.get_height() // 2
            if icon is None:
                self.win.blit(label, (x + w // 2 - label.get_width() // 2, cy))
            else:
                group_w = icon.get_width() + 8 + label.get_width()
                gx = x + w // 2 - group_w // 2
                self.win.blit(icon, (gx, y + pill_h // 2 - icon.get_height() // 2))
                self.win.blit(label, (gx + icon.get_width() + 8, cy))
        # Q1: pasek postepu fali - usuniety na prosbe gracza
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
            font_small = self.font_small16
            label = self._txt_next
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
                boss_label = self._txt_boss
                self.win.blit(boss_label, (x_off, preview_y + 15))
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