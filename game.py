import pygame
import os
import sys
import i18n
from i18n import t as tr
# PyInstaller: gdy uruchomione jako .exe, pliki sa w sys._MEIPASS
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)
# Najwyzsza jakosc skalowania GPU (ostrzejszy fullscreen)
os.environ.setdefault("SDL_HINT_RENDER_SCALE_QUALITY", "2")
pygame.font.init()
pygame.display.set_caption('Island Defenders')
# Ekran ladowania (zanim ciezkie assety) - fullscreen zeby nie bylo czarnego paska
try:
    _info = pygame.display.Info()
    _lw, _lh = _info.current_w, _info.current_h
    _load_win = pygame.display.set_mode((_lw, _lh), pygame.FULLSCREEN)
    _load_win.fill((20, 25, 35))
    _lf = pygame.font.SysFont("arial", 36)
    _lt = _lf.render(i18n.t("loading"), True, (255, 255, 255))
    _load_win.blit(_lt, (_lw//2 - _lt.get_width()//2, _lh//2 - 20))
    pygame.display.flip()
except Exception:
    pass
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
from enemies.enemy import _PIER_RECT  # pomost: kraby i fale go omijaja (jest NAD woda)
from towers.woodenTower import (WoodenTower, MetalTower, GoldenTower, FireTower, BlazeTower,
                                _gold_tint,
                                sound_1 as tower_sound_1, sound_2 as tower_sound_2,
                                sound_3 as tower_sound_3, sound_4 as tower_sound_4,
                                sound_5 as tower_sound_5)
from ships.ship import Ship
from ships.ally_ship import AllyShip
from menu.menu import VerticalMenu, Menu
from towers.tower import menu_bg as _tower_menu_bg, upgrade_btn as _upgrade_btn, sell_btn as _sell_btn
from effects.particles import ParticleSystem, FloatingCoin, Shockwave
import time
import random

lives_img = pygame.image.load(os.path.join("images", "heart.png"))
money_img = pygame.image.load(os.path.join("images", "coin.png"))
side_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "side_menu.png")), (375, 475))
t1_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "t2.png")), (30, 30))
t2_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "t1.png")), (30, 30))
t3_img = _gold_tint(pygame.transform.scale(pygame.image.load(os.path.join("images", "t3.png")), (30, 30)))
t4_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "t4.png")), (30, 30))
t5_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "t5.png")), (30, 30))
wave_bg = pygame.transform.scale(pygame.image.load(os.path.join("images","wave.png")), (225, 75))

towers_names = ["woodenTower", "metalTower", "goldenTower", "fireTower", "blazeTower"]
# Mapowanie: nazwa klasy wiezy -> nazwa przycisku w sklepie (t1..t5).
# get_item_cost() szuka po nazwie przycisku, wiec bez tego zwracal -1.
tower_shop_names = {"woodenTower": "t1", "metalTower": "t2", "goldenTower": "t3",
                    "fireTower": "t4", "blazeTower": "t5"}
# Upgrady klikalnego budynku (jednorazowe na run)
BUILDING_UPGRADES = [
    {"id": "treasury", "name": "War Treasury", "cost": 1200,
     "desc": "+25% gold from all kills, permanently."},
    {"id": "bounty", "name": "Bounty Board", "cost": 1500,
     "desc": "Bosses and elite enemies give +50% gold."},
    {"id": "lucky", "name": "Lucky Charm", "cost": 2000,
     "desc": "Towers have 10% chance to deal 2x critical damage."},
    {"id": "docks", "name": "Reinforced Docks", "cost": 2500,
     "desc": "Enemies move 15% slower on the pier."},
    {"id": "storm", "name": "Storm Caller", "cost": 3000,
     "desc": "Storms last longer and give +25% gold (instead of +15%)."},
    {"id": "walls", "name": "Reinforced Walls", "cost": 3500,
     "desc": "+5 max lives for the building."},
    {"id": "ammo", "name": "Ammunition Depot", "cost": 4000,
     "desc": "All towers shoot 15% faster."},
    {"id": "drones", "name": "Repair Drones", "cost": 5000,
     "desc": "+1 max life right away, then heals +1 life every 2 waves (up to max). A drone orbits the building."},
    {"id": "tesla", "name": "Tesla Coil", "cost": 6500,
     "desc": "Zaps the nearest enemy every few seconds. Attracts storms; huge range in storms."},
    {"id": "facility", "name": "Drone Launch Facility", "cost": 8000,
     "desc": "Launches a combat drone: minigun strafes enemies, then kamikazes with a huge splash. Rearms in 3 min.",
     "requires": "drones"},
    {"id": "cavalry", "name": "Call the Cavalry", "cost": 10000,
     "desc": "An allied ship cripples the pirate ship, then bombards enemies.",
     "endless_only": True},
]
# Upgrady klikalnego namiotu (jednorazowe na run)
TENT_UPGRADES = [
    {"id": "scout", "name": "Scout Reports", "cost": 2000,
     "desc": "Ambush: +25% damage to enemies in first 4s after spawning."},
    {"id": "supply", "name": "Supply Lines", "cost": 2500,
     "desc": "Towers cost 15% less (buy and upgrade)."},
    {"id": "drums", "name": "War Drums", "cost": 3000,
     "desc": "Tower abilities recharge 30% faster."},
    {"id": "medic", "name": "Field Medic", "cost": 1500,
     "desc": "Bombardment destroys towers half as often (50% -> 25%)."},
    {"id": "signal", "name": "Signal Fire", "cost": 3500,
     "desc": "Campfire grows 2x. All Fire towers shoot 12% faster. Dancers guard the building with bows."},
    {"id": "guerrilla", "name": "Guerrilla Training", "cost": 4000,
     "desc": "+35% damage against slowed enemies."},
    {"id": "banner", "name": "Honor Banner", "cost": 4000,
     "desc": "All towers deal +10% damage."},
    {"id": "spikes", "name": "Spike Barricade", "cost": 4500,
     "desc": "Spikes on the road wound passing enemies."},
    {"id": "balloon", "name": "Recon Balloon", "cost": 5500,
     "desc": "Scout balloon drifts overhead, dropping bombs on enemies."},
    {"id": "sabotage", "name": "Sabotage", "cost": 6000,
     "desc": "Saboteurs poison enemy supplies. All enemies spawn with -15% HP."},
]
# Balans trudnosci: EASY ma byc naprawde latwy, NORMAL bazowy, HARD naprawde trudny.
# price_mult: ceny WSZYSTKIEGO (sklep, ulepszenia wiez, upgrady budynku/namiotu).
# enemy_hp_mult / enemy_speed_mult: zwykli wrogowie (bossowie maja wlasne HP w _boss_hp).
# gold_mult: zloto za zabojstwa. spawn_mult: odstep miedzy spawnami (wiekszy = wolniej).
# ability_cd_mult: czasy odnowienia umiejetnosci wiez. storm_chance: bazowa szansa na burze.
# sell_mult: zwrot przy sprzedazy wiezy (zakup + ulepszenia).
DIFFICULTY_CONFIG = {
    "EASY": {"price_mult": 0.8, "enemy_hp_mult": 0.8, "enemy_speed_mult": 1.0,
             "gold_mult": 1.25, "spawn_mult": 1.3, "ability_cd_mult": 0.85, "storm_chance": 0.2,
             "sell_mult": 0.8},
    "NORMAL": {"price_mult": 1.0, "enemy_hp_mult": 1.0, "enemy_speed_mult": 1.0,
               "gold_mult": 1.0, "spawn_mult": 1.0, "ability_cd_mult": 1.0, "storm_chance": 0.15,
               "sell_mult": 0.7},
    "HARD": {"price_mult": 1.25, "enemy_hp_mult": 1.3, "enemy_speed_mult": 1.15,
             "gold_mult": 0.85, "spawn_mult": 0.7, "ability_cd_mult": 1.25, "storm_chance": 0.10,
             "sell_mult": 0.6},
}
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
sound_glass = pygame.mixer.Sound("sounds/glass_shatter.wav")
sound_ab_rapid = pygame.mixer.Sound("sounds/ability_rapidfire.wav")
sound_ab_frost = pygame.mixer.Sound("sounds/ability_frostnova.wav")
sound_ab_gold = pygame.mixer.Sound("sounds/ability_goldentouch.wav")
sound_ab_meteor = pygame.mixer.Sound("sounds/ability_meteor.wav")
sound_ab_arma = pygame.mixer.Sound("sounds/ability_armageddon.wav")
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
sound_minigun = pygame.mixer.Sound("sounds/minigun.wav")
sound_minigun.set_volume(0.35)  # szybkie serie: ciszej, zeby nie zagluszaly
sound_rocket = pygame.mixer.Sound("sounds/rocket_launch.wav")
sound_rocket.set_volume(0.5)
sound_rocket_boom = pygame.mixer.Sound("sounds/rocket_boom.wav")
sound_rocket_boom.set_volume(0.6)
shoot_sounds = {
    "WoodenTower": pygame.mixer.Sound("sounds/shoot_wood.wav"),
    "MetalTower": pygame.mixer.Sound("sounds/shoot_metal.wav"),
    "GoldenTower": pygame.mixer.Sound("sounds/shoot_gold.wav"),
    "FireTower": pygame.mixer.Sound("sounds/shoot_fire.wav"),
    "BlazeTower": pygame.mixer.Sound("sounds/shoot_blaze.wav"),
}

class SpikeCluster:
    """Kolce na drodze (Spike Barricade): klikalne jak wieze, upgrade o 2 poziomy,
    sprzedaz. Obrazenia wg poziomu (8/14/22 dps), ceny upgradu skalowane
    trudnoscia (price_mult). 1 klaster = 1/3 ceny Spike Barricade
    (4500/3 = 1500, x price_mult) - tyle liczy sie przy sprzedazy."""
    UPGRADE_COSTS = [600, 1200]  # bazowe (poziom 1->2, 2->3)
    DAMAGES = [8.0, 14.0, 22.0]  # dps na poziomach 1/2/3
    BASE_SHARE = 1500  # 4500 / 3 klastry

    def __init__(self, x, y, price_mult=1.0):
        self.x = x
        self.y = y
        self.level = 1
        self.max_level = 3
        self.damage = self.DAMAGES[0]
        self.range = 40  # promien razenia
        self.kills = 0
        self.name = "spikes"
        self.display_name = "Spike Barricade"
        self.total_spent = int(self.BASE_SHARE * price_mult)
        costs = [int(c * price_mult) for c in self.UPGRADE_COSTS] + ["MAX"]
        self.menu = Menu(self, x, y, _tower_menu_bg, costs)
        self.menu.add_btn(_upgrade_btn, "Upgrade", dx=-65, dy=-45)
        self.menu.add_btn(_sell_btn, "Sell", dx=15, dy=-45)

    def sell_value(self, rate=0.7):
        return int(self.total_spent * rate)

    def upgrade(self, cost=0):
        if self.level < self.max_level:
            self.total_spent += cost
            self.level += 1
            self.damage = self.DAMAGES[self.level - 1]

    def click(self, X, Y):
        return abs(X - self.x) <= 30 and abs(Y - self.y) <= 25

class Game:
    def __init__(self, lives=20, money=200, sound=True, difficulty="NORMAL"):
        self.width = 1124
        self.height = 720
        self.difficulty = difficulty  # EASY / NORMAL / HARD (do HP bossa)
        # Natywna rozdzielczosc ekranu (opcja C: render w pelnej rozdzielczosci)
        if not pygame.display.get_init():
            pygame.display.init()
        _info = pygame.display.Info()
        self._native_w, self._native_h = _info.current_w, _info.current_h
        # Display w natywnej rozdzielczosci (bez SCALED - reczne smoothscale)
        # Fallback jesli FULLSCREEN nie dziala
        try:
            self._screen = pygame.display.set_mode((self._native_w, self._native_h), pygame.FULLSCREEN)
        except pygame.error:
            self._screen = pygame.display.set_mode((self._native_w, self._native_h))
        # Uzyj RZECZYWISTEGO rozmiaru (Windows moze zwrocic inny niz zadany)
        self._native_w, self._native_h = self._screen.get_size()
        # Bufor gry 1124x720 - cala logika bez zmian
        self.win = pygame.Surface((self.width, self.height))
        self._fullscreen = True
        self.show_menu = False  # menu ESC
        self._show_help = False  # pod-ekran "How to Play"
        self._forfeit = False  # rezygnacja z gry (ESC -> Forfeit Run)
        self._menu_buttons = []  # [rect, action] - budowane w draw_menu
        # Skok do fali endless z menu pauzy: pole tekstowe + przycisk
        self._pause_wave_txt = ""
        self._pause_wave_focus = False
        self._pause_jump_input = None
        self._pause_jump_btn = None
        # Strefy stawiania wiez (narysowane przez gracza)
        self._placement_zones = [
            [(96, 369), (2, 387), (0, 441), (143, 483), (314, 489), (428, 505), (465, 529), (487, 547), (494, 556), (970, 496), (118, 369), (101, 370), (101, 369)],
            [(465, 370), (455, 379), (420, 383), (903, 432), (1070, 474), (1080, 478), (1095, 474), (1119, 484), (1119, 369), (1029, 362), (1022, 375), (994, 385), (953, 385), (924, 383), (892, 382), (864, 373), (852, 365), (469, 370), (458, 378)],
            [(1076, 511), (1062, 522), (1055, 530), (918, 550), (791, 566), (685, 578), (574, 585), (557, 594), (606, 607), (682, 615), (765, 623), (813, 630), (857, 629), (944, 624), (989, 622), (1042, 612), (1093, 594), (1116, 586), (1116, 523), (1095, 523), (1077, 513)],
        ]
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
        self.cannonballs = []  # Pociski armatnie statku
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
        self.stats_kills_by_type = {}
        self.stats_towers_built = 0
        self.stats_towers_lost = 0
        self.stats_abilities_used = 0
        self.stats_gold_spent = 0
        # Upgrady budynku (klikany szklany budynek)
        self.building_upgrades = set()  # id kupionych upgradow
        self._building_menu_open = False
        self._building_menu_buttons = []  # (rect, upgrade_id)
        self._building_rect = pygame.Rect(110, 158, 353, 231)  # bbox of drawn highlight polygon
        self._building_icons = {}
        for uid in ("walls", "drones", "tesla", "treasury", "bounty",
                    "ammo", "lucky", "storm", "docks", "cavalry"):
            try:
                img = pygame.image.load(os.path.join("images", "upgrades", uid + ".webp"))
                self._building_icons[uid] = pygame.transform.smoothscale(img, (56, 56))
            except:
                self._building_icons[uid] = None
        # Facility uses the same icon as Repair Drones (same icon, second tier)
        self._building_icons["facility"] = self._building_icons.get("drones")
        self._building_desc_font = pygame.font.SysFont("arial", 16)
        # Upgrady namiotu (klikany namiot tipi)
        self.tent_upgrades = set()  # id kupionych upgradow
        self._tent_menu_open = False
        self._tent_menu_buttons = []
        self._tent_rect = pygame.Rect(861, 244, 170, 144)  # bbox of drawn highlight polygon
        # Highlight polygons drawn by Daniel in the draw tool (2026-10-14)
        self._building_highlight_pts = [(114, 386), (110, 280), (140, 214), (200, 165), (276, 158), (340, 200), (389, 189), (463, 254), (457, 383), (304, 387), (139, 389)]
        self._tent_highlight_pts = [(861, 366), (948, 244), (1031, 376), (946, 388), (879, 380)]
        self._tent_icons = {}
        _tent_icon_files = {"scout": "scout", "drums": "drums", "supply": "supply",
                            "medic": "medic", "guerrilla": "guerrilla",
                            "banner": "veteran", "signal": "signal",
                            "spikes": "spikes", "balloon": "balloon",
                            "sabotage": "sabotage"}
        for uid, fname in _tent_icon_files.items():
            try:
                img = pygame.image.load(os.path.join("images", "upgrades", "tent_" + fname + ".webp"))
                self._tent_icons[uid] = pygame.transform.smoothscale(img, (56, 56))
            except:
                self._tent_icons[uid] = None
        # Wizualne efekty namiotu (init)
        self._balloon_x = -100
        self._balloon_bomb_cd = 0
        self._balloon_bombs = []
        self._spikes = []  # klastry kolcow (SpikeCluster, klikalne)
        self.selected_spike = None  # wybrany klaster kolcow (menu jak wieza)
        self._dancers = [
            {"x": 377, "y": 352, "home_x": 377, "home_y": 352, "alive": True, "sex": "m", "name": "Clyde", "kills": 0, "cd": 0, "mode": "guard", "target": None, "duel_t": 0, "swing": 0},
            {"x": 183, "y": 357, "home_x": 183, "home_y": 357, "alive": True, "sex": "f", "name": "Bonnie", "kills": 0, "cd": 0, "mode": "guard", "target": None, "duel_t": 0, "swing": 0},
        ]
        self._guard_arrows = []
        self._tombstones = []  # R.I.P. stones for fallen guards (reset each run)
        # Achievements
        from achievements import AchievementManager
        self.ach_mgr = AchievementManager()
        _ach_defaults = {
            "kills": 0, "boss_kills": 0, "elite_kills": 0,
            "max_wave": 0, "wins": 0, "flawless_waves": 0,
            "perfect_wins": 0, "comeback_wins": 0,
            "endless_entered": 0, "max_endless_wave": 0,
            "gold_earned": 0, "max_gold_held": 0, "gold_spent": 0,
            "towers_built": 0, "max_level_towers": 0, "max_level_at_once": 0,
            "fire_towers": 0, "golden_towers": 0, "abilities_used": 0,
            "building_upgrades": 0, "tent_upgrades": 0,
            "cavalry_bought": 0, "sabotage_bought": 0, "balloon_bought": 0,
            "drums_bought": 0, "medic_bought": 0,
            "storm_fights": 0, "crits": 0, "pirate_crippled": 0,
            "dancers_sacrificed": 0, "tesla_kills": 0,
            "full_lives_wave8": 0, "dancer_kills": 0,
        }
        # Skumulowane statystyki z poprzednich runow (achievements.json) - nie zeruj
        _saved = dict(getattr(self.ach_mgr, "stats", {}) or {})
        self._ach_stats = dict(_ach_defaults)
        for _k, _v in _saved.items():
            if _k in self._ach_stats:
                try:
                    self._ach_stats[_k] = int(_v)
                except:
                    pass
        # Liczniki per-run (Fire/Golden "in one game" - max per-run, nie suma)
        self._run_fire_towers = 0
        self._run_golden_towers = 0
        self._win_recorded = False  # unikaj podwojnego liczenia wygranej
        self._ach_popup = None  # (name, desc, icon, timer)
        self._ach_popup_timer = 0
        self._spikes = []  # klastry kolcow na drodze (SpikeCluster)
        # Tancerze-straznicy (Signal Fire)
        self._dancers = [
            {"x": 377, "y": 352, "home_x": 377, "home_y": 352, "alive": True, "sex": "m", "name": "Clyde", "kills": 0, "cd": 0, "mode": "guard", "target": None, "duel_t": 0, "swing": 0},  # mezczyzna z toporem
            {"x": 183, "y": 357, "home_x": 183, "home_y": 357, "alive": True, "sex": "f", "name": "Bonnie", "kills": 0, "cd": 0, "mode": "guard", "target": None, "duel_t": 0, "swing": 0},  # kobieta z patelnia
        ]
        self._guard_arrows = []  # widoczne strzaly z lukow straznikow
        self._tombstones = []  # R.I.P. stones for fallen guards (reset each run)
        # Dron naprawczy (wizualny)
        self._drone_angle = 0.0
        # Tesla Coil
        self._tesla_cooldown = 0
        # Combat drone (Drone Launch Facility) - 100Hz logic ticks
        self._combat_drone = None
        self._facility_rearm = 0
        self._coil_strikes = []  # pioruny walace w cewke Tesli (burza)
        self._facility_tracers = []
        self._facility_blasts = []
        self._facility_rockets = []  # lecace rakiety drona bojowego
        # Statek sojuszniczy (Call the Cavalry)
        self.pirate_crippled = False
        self.ally_ship = None
        self._ally_strike_at = None  # po ilu rozladowanych wrogach wplynie
        self._ally_shots_left = 0
        self._ally_fire_timer = 0
        self.mortar_shots = []  # pociski mozdzierzowe
        self._storm_extra = False  # Storm Caller: burza trwa 2 fale
        self.endless = False  # Tryb endless po wygranej
        self.endless_wave = 0
        self.wave_banner_text = ""  # V3: banner fali
        self.wave_banner_timer = 0
        self.muzzle_flashes = []  # V4: blyski przy strzale [(x, y, timer)]
        self.waiting_for_clear = False  # Czekamy na wyczyszczenie planszy przed nastepna fala
        self._clear_timer = 0  # Zabezpieczenie przed zawieszeniem fali
        self.gold_notifications = []  # Widoczne powiadomienia o zlocie [(tekst, timer)]
        self.corpses = []  # Trupy wrogow: [img, x, y, timer]
        self.early_wave_rect = None  # R2: prostokat przycisku "Nastepna fala"
        self.wave_modifier = None  # U8: modyfikator fali (swift/rich/swarm)
        # Bombardowanie cinematic
        self.bombard_active = False  # czy cinematic trwa
        self.bombard_phase = 0  # faza cinematic
        self.bombard_timer = 0  # timer fazy
        self.bombard_targets = []  # wieze do ostrzelania
        self.bombard_index = 0  # ktora wieza aktualnie
        self.bombard_zoom = 0  # 0=brak, 1=zoom in, 2=zoom out
        self.bombard_zoom_tower = None  # wieza na ktora zoomujemy
        self.show_all_ranges = False  # U10: pokaz wszystkie zasiegi
        self.pending_bosses = []  # Bossowie czekajacy na zadokowanie statku (co 10 fal: kilku naraz)
        self._tesla_guaranteed_storm = 0  # Tesla Coil: gwarantowana burza w nastepnej rundzie
        self._endless_rain_left = 0  # pozostale fale deszczu w endless (gwarantowana burza)
        self._clear_snap = None  # snapshot wrogow dla failsafe'a czyszczenia planszy
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
        self.boss_intro_dark = 0  # Przyciemnienie przy wejsciu bossa
        self.scorch_marks = []  # Spalenizna [(x, y, timer)]
        self.clouds = [(random.randint(0, 1124), random.randint(20, 200), random.randint(20, 40)) for _ in range(3)]
        self.leaves = [(random.randint(0, 1124), random.randint(0, 720)) for _ in range(15)]
        self.seagulls = [(random.randint(200, 900), random.randint(50, 150), random.random()*6) for _ in range(2)]
        self.game_time = 0  # Q17: zegar sesji (ticki)
        self.music_muted = not sound  # jesli sound=False z menu, muzyka wyciszona
        self.sfx_muted = not sound  # dzwieki tez wyciszone
        self._music_intense = False  # intensywna (boss) vs zwykla sciezka
        self.build_queue = []  # Q14: kolejka budowy
        self.tower_filter = None  # Q15: filtr wiez
        self.display_money = 200  # Niespodzianka 4: animowany licznik zlota
        self.display_lives = 20  # Animowany licznik zyc
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
            for s in (sound_1, sound_2, sound_3, sound_4, sound_5, sound_glass,
                      sound_ab_rapid, sound_ab_frost, sound_ab_gold, sound_ab_meteor, sound_ab_arma,
                      tower_sound_1, tower_sound_2, tower_sound_3,
                      tower_sound_4, tower_sound_5, sound_win, sound_lose, sound_roar,
                      sound_levelup, sound_horn, sound_rain, sound_gull, sound_fanfare,
                      sound_minigun, sound_rocket, sound_rocket_boom,
                      *shoot_sounds.values()):
                s.set_volume(0)
        self.bg = pygame.image.load(os.path.join("images", "bg_noship.png"))
        self.bg = pygame.transform.scale(self.bg, (self.width, self.height))
        # Recon Balloon sprite: same model as upgrades-tab icon (white balloon, transparent bg)
        try:
            self._balloon_img = pygame.image.load(os.path.join("images", "balloon_recon.png")).convert_alpha()
        except Exception:
            self._balloon_img = None
        self.ship = Ship(os.path.join("images", "ship.png"), dock_x=278, dock_y=669,
                         screen_w=self.width)
        self.ship.sail_in()
        self.last_wave_done = False
        self._logic_tick = 0  # licznik tickow logiki 100Hz (spawn, Scout - skaluje sie z predkoscia)
        self._spawn_cd = 0  # odstep do nastepnego spawnu (ticki logiki)
        self.hud_font = pygame.font.SysFont("segoe ui, calibri, arial", 26, bold=True)
        # Cache fontow - tworzone raz w __init__, nie co klatke (wydajnosc)
        _fn = "segoe ui, calibri, arial"
        self.font_big70 = pygame.font.SysFont(_fn, 70)
        self.font_small30 = pygame.font.SysFont(_fn, 30)
        self.font_small26 = pygame.font.SysFont(_fn, 26)
        self.font_small22 = pygame.font.SysFont(_fn, 22)
        self.font_small18 = pygame.font.SysFont(_fn, 18)
        self.font_stats24 = pygame.font.SysFont(_fn, 24)
        self.font_dmg18 = pygame.font.SysFont(_fn, 18, bold=True)
        self.font_crit22 = pygame.font.SysFont(_fn, 22, bold=True)
        self.font_banner64 = pygame.font.SysFont(_fn, 64, bold=True)
        self.font_gold28 = pygame.font.SysFont(_fn, 28, bold=True)
        self.font_boss16 = pygame.font.SysFont(_fn, 16, bold=True)
        self.font_btn18 = pygame.font.SysFont(_fn, 18, bold=True)
        self.font_c13 = pygame.font.SysFont(_fn, 13, bold=True)
        self._tomb_fonts = {s: pygame.font.SysFont(_fn, s, bold=True) for s in (13, 12, 11, 10, 9, 8, 7, 6, 5)}  # tombstone text, shrink-to-fit
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
        self._coin_icon15 = pygame.transform.scale(money_img, (15, 15))
        # Prerender statycznych napisow (wydajnosc)
        self._txt_paused = self.font_p36.render(tr("hud.paused"), True, (255, 255, 255))
        self._txt_paused_sub = self.font_s16.render(tr("hud.paused_sub"), True, (200, 200, 200))
        self._txt_ready = self.font_f11.render(tr("hud.ready"), True, (255, 255, 200))
        self._txt_no_tower = self.font_f11.render(tr("hud.no_tower"), True, (120, 120, 120))
        self._txt_next = self.font_small16.render(tr("hud.next"), True, (255, 255, 255))
        self._txt_boss = self.font_small16.render(tr("hud.boss_next"), True, (255, 50, 50))
        # Licznik klatek i cache czasu animacji ambient (wydajnosc)
        self._frame = 0
        self._ambient_t = 0.0
        self._hover_enemy = None
        self._now = 0
        self._now_s = 0.0
        # Zegar ANIMACJI: posuwa sie tylko gdy gra nie jest zapauzowana.
        # Wszystkie animacje rysowane (chmury, woda, tancerze, ognisko,
        # kolysanie statkow, puls Tesli...) czytaja _anim_s zamiast
        # _now_s/time.time() - pauza zamraza caly obraz, nie tylko logike.
        self._anim_s = 0.0
        self._anim_last = None
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
        self.menu.add_btn(t2_img, "t2", 500, damage=3)
        self.menu.add_btn(t3_img, "t3", 750, damage=5)
        self.menu.add_btn(t4_img, "t4", 1000, damage=8)
        self.menu.add_btn(t5_img, "t5", 2000, damage=10)
        # Trudnosc: ceny sklepu (wyswietlane + pobierane) - skalowane raz przy starcie.
        # EASY -20%, HARD +25%. Supply Lines liczy sie OD tych cen (shop_price).
        for _btn in self.menu.buttons:
            _btn.cost = int(round(_btn.cost * self._diff("price_mult")))
        self.moving_object =  None
        self.menu_dragging = False  # przeciganie sklepu myszka
        self.menu_drag_dx = 0
        self.menu_drag_dy = 0
        self.wave = 0
        self.current_wave = waves[self.wave][:]
        # DEBUG LOG - start gry
        try:
            with open("wave_debug.log", "a") as f:
                f.write(f"GAME START: wave={self.wave}, current_wave={self.current_wave}, waves[0]={waves[0]}\n")
        except:
            pass
        self.won = False
        self.enemy_classes = [Forkman, Swordman, Knight, Goblin, Cyclop, Impostor, Ogre, EvilVillager]

    def _diff(self, key):
        """Wartosc balansu dla biezacej trudnosci (DIFFICULTY_CONFIG)."""
        return DIFFICULTY_CONFIG.get(self.difficulty, DIFFICULTY_CONFIG["NORMAL"]).get(key, 1.0)

    def _price(self, base):
        """Cena z mnoznikiem trudnosci (upgrady budynku/namiotu)."""
        return int(round(base * self._diff("price_mult")))

    def gen_enemies(self):
        # Wrogowie desantuja sie tylko gdy statek jest w porcie.
        if self.won or self.ship.state != Ship.DOCKED:
            return
        # Bossowie czekaja na zadokowanie - spawnuja gdy statek w porcie
        if self.pending_bosses:
            for _b in self.pending_bosses:
                # Sabotage: boss tez z -15% HP (widoczne na pasku)
                if "sabotage" in self.tent_upgrades:
                    _b.health = int(_b.health * 0.85)
                _b._spawn_tick = self._logic_tick
                self.enemies.append(_b)
            # A10: intro bossa - dramatyczne wejscie (raz na cala paczke)
            self.wave_banner_text = tr("banner.boss")
            self.wave_banner_timer = 150
            self.screen_shake = 10
            self.boss_intro_dark = 180  # przyciemnienie ekranu na 3s
            sound_roar.play()
            self.pending_bosses = []
        if sum(self.current_wave) == 0:
            # Rozladunek zakonczony - sprawdz bombardowanie lub wyplywamy
            if not self.waiting_for_clear:
                self.waiting_for_clear = True
                self._clear_timer = 0
                # Bombardowanie: fala 4 (index 3) przy max zyciach, fala 8 (index 7) przy >polowy zyc
                # Endless: CO FALE w 2 losowe wieze, bez warunkow zyciowych
                wave_num = self.wave + 1
                should_bombard = False
                bombard_targets = 3
                if self.endless:
                    should_bombard = True
                    bombard_targets = 2
                elif wave_num == 4 and self.lives >= self._start_lives:
                    should_bombard = True
                elif wave_num == 8 and self.lives > self._start_lives // 2:
                    should_bombard = True
                if should_bombard and not self.bombard_active:
                    self._start_bombardment(num_targets=bombard_targets)
                else:
                    self.ship.sail_out()
        else:
            # Spawn grupowy: rzut na liczbe wrogow w jednym desancie -
            # 64% x1, 20% x2, 10% x3, 5% x4, 1% x5 (typy losowe z puli fali)
            _r = random.random()
            _n = 5 if _r < 0.01 else 4 if _r < 0.06 else 3 if _r < 0.16 else 2 if _r < 0.36 else 1
            for _k in range(_n):
                if sum(self.current_wave) == 0:
                    break
                _en = self._spawn_one_from_pool()
                # Grupa nie moze stac w JEDNYM punkcie: kolejni czlonkowie
                # grupy startuja cofnieci wzdluz pierwszego odcinka trasy
                # (rozlozeni na pokladzie/pomoscie, ~26 px odstepu) + lekki
                # rozrzut boczny - inaczej sprite'y nakladaja sie 1:1 i po
                # zabiciu jednego "wyskakuje" nastepny z tego samego miejsca.
                if _en is not None and _k > 0:
                    _d = _en._path_dirs[0] if _en._path_dirs else (1, 0)
                    _back = _k * 26
                    _en.x -= _d[0] * _back
                    _en.y -= _d[1] * _back
                    _en.x += -_d[1] * random.randint(-7, 7)
                    _en.y += _d[0] * random.randint(-7, 7)

    def _spawn_one_from_pool(self):
        """Jeden wrog z puli biezacej fali (losowy typ) - dawne cialo gen_enemies."""
        # Losowa kolejnosc spawnu (nie od najslabszego) - mniej przewidywalnie
        available = [i for i, c in enumerate(self.current_wave) if c > 0]
        if available:
            i = random.choice(available)
            self.current_wave[i] -= 1
            en = self.enemy_classes[i]()
            # U8: SWIFT - +30% predkosci
            if self.wave_modifier == "swift":
                en.velocity *= 1.3
            # 6: 8% szansy na elitarnego (nie boss)
            # Endless: szansa na elitarnego rosnie z fala (8% -> maks. 18%)
            _elite_ch = 0.08 + (min(0.10, self.endless_wave * 0.01) if self.endless else 0.0)
            if not isinstance(en, Boss) and random.random() < _elite_ch:
                en.make_elite()
            # Endless: 5x HP bazowo + 5% co fale (compound), minimum +1 HP na fale
            # Reinforced Docks: wrogowie 15% wolniejsi, ale TYLKO na pomoście
            # (flaga _docks_slow; predkosc liczona w Enemy.move() wg pozycji).
            # Sabotage: wrogowie spawnuja sie z -15% HP
            if self.endless:
                scaled = self._endless_hp(en.max_health, self.endless_wave)
                en.max_health = scaled
                en.health = scaled
            # Trudnosc: HP i predkosc zwyklych wrogow (EASY slabsze/wolniejsze, HARD mocniejsze/szybsze)
            _hp_mult = self._diff("enemy_hp_mult")
            if _hp_mult != 1.0:
                en.max_health = int(en.max_health * _hp_mult)
                en.health = int(en.health * _hp_mult)
            en.velocity *= self._diff("enemy_speed_mult")
            if "sabotage" in self.tent_upgrades:
                # Tylko aktualne HP (widoczne na pasku), max zostaje
                en.health = int(en.health * 0.85)
            if "docks" in self.building_upgrades:
                en._docks_slow = True
            en._spawn_tick = self._logic_tick  # Scout Reports: ambush (ticki logiki, nie czas rzeczywisty)
            self.enemies.append(en)
            # Call the Cavalry: licz rozladowanych, sojusznik wplywa w 1. polowie fali
            if self._ally_strike_at is not None:
                self._ally_unloaded = getattr(self, "_ally_unloaded", 0) + 1
                if (self._ally_unloaded >= self._ally_strike_at
                        and (not self.ally_ship or self.ally_ship.state == AllyShip.AWAY)):
                    self._ally_strike_at = None  # tylko raz na fale
                    self.ally_ship = AllyShip(os.path.join("images", "ship_ally.png"),
                                              screen_w=self.width)
                    # Baraz z miejsca pirata (867, 603), nie z portu
                    self.ally_ship.sail_in("strike", fire_x=867)
                    self.ally_ship.y = 603
                    self.wave_banner_text = tr("banner.ally")
                    self.wave_banner_timer = 150
            return en
        return None

    def setup_endless_jump(self, n):
        """Teleport z menu glownego: start gry od wybranej fali endless.
        Ta sama logika co skok w trakcie gry (jump_to_wave), tylko bez
        resetu statku - gra dopiero powstala, statek juz wplywa."""
        self.jump_to_wave(n, reset_ship=False)

    def jump_to_wave(self, n, reset_ship=True):
        """Skok do fali endless z ZACHOWANIEM stanu gry: wieze, pieniadze,
        zycia i ulepszenia zostaja. Plansza jest czyszczona (wrogowie,
        bossowie w kolejce, pociski, mozdzierze), statek wplywa od nowa
        i fala czeka na start - jak przed rozpoczeciem fali. Skoczona
        fala NIE placi bonusu startowego (tylko ten jeden raz); po jej
        ukonczeniu nastepna fala placi juz normalnie.
        n >= 11: sklad/HP jak przy naturalnym dojsciu do tej fali.
        n == 10: EASTER EGG - rewanz z bossem finalnym z 100x HP;
        po jego fali gra przechodzi w endless od fali 11."""
        # Anuluj stawianie wiezy ze zwrotem (jak ESC)
        if getattr(self, "moving_object", None) is not None:
            try:
                self.money += self.shop_price(self.moving_object.name)
            except Exception:
                pass
            try:
                self.moving_object.moving = False
            except Exception:
                pass
            self.moving_object = None
        # Czyszczenie planszy i stanow bojowych
        self.enemies = []
        self.pending_bosses = []
        self.projectiles = []
        self.mortar_shots = []
        self._facility_rockets = []
        if self._combat_drone is not None:
            self._combat_drone["target"] = None
            if self._combat_drone["state"] == "engage":
                self._combat_drone["state"] = "wander"
        self.bombard_active = False
        self.bombard_phase = 0
        self.waiting_for_clear = False
        self.last_wave_done = False
        self._spawn_cd = 0
        if self.selected_tower is not None:
            try:
                self.selected_tower.selected = False
            except Exception:
                pass
        self.selected_tower = None
        self.selected_spike = None
        self._building_menu_open = False
        self._tent_menu_open = False
        if reset_ship:
            # Statek od nowa: wplywa jak na poczatku gry i desantuje fale
            self.ship = Ship(os.path.join("images", "ship.png"),
                             dock_x=278, dock_y=669, screen_w=self.width)
            self.ship.sail_in()
        if n <= 10:
            self.endless = True
            self.endless_wave = 0
            self.wave = 9
            self.current_wave = waves[9][:]
            self._wave_start_lives = self.lives
            self.pending_bosses.append(Boss(final=True,
                hp=int(950 * self._diff("enemy_hp_mult") * 100)))
            self.wave_banner_text = tr("banner.final_boss")
            self.wave_banner_timer = 150
        else:
            self.endless = True
            self.endless_wave = n - 11
            self.wave = n - 2
            self._setup_endless_wave(grant_gold=False)
            self._wave_start_lives = self.lives

    def _do_pause_jump(self):
        """SKOCZ z menu pauzy: skok do wpisanej fali i powrot do gry."""
        try:
            n = int(self._pause_wave_txt)
        except ValueError:
            return
        n = max(10, min(999, n))
        self.jump_to_wave(n)
        self._pause_wave_txt = ""
        self._pause_wave_focus = False
        self.show_menu = False
        self.paused = False

    def _setup_endless_wave(self, grant_gold=True):
        """Generuje kolejna fale endless (proceduralnie, rosnace HP).
        grant_gold=False przy skoku do fali (menu glowne / menu pauzy):
        skocznia fala nie placi bonusu startowego - tylko ten jeden raz,
        kolejne fale znowu placa normalnie."""
        self.endless_wave += 1
        self.wave += 1
        self._ach_stats['max_wave'] = max(self._ach_stats.get('max_wave', 0), self.wave + 1)
        self._ach_stats['max_endless_wave'] = max(self._ach_stats.get('max_endless_wave', 0), self.endless_wave)
        # Sklad endless: laczna liczba rosnie jak dawniej (79 x (1+0.15w)),
        # ale udzialy przesuwaja sie ku SILNIEJSZYM typom wraz z fala -
        # waga klasy i skaluje sie geometrycznie (1 + 0.06w)^i: na fali 11
        # sklad jest zblizony do dawnego, a od ~fali 20 dominuja Ogre
        # i EvilVillager, Forkman zostaje tylko dodatkiem (Daniel: za duzo
        # sprite'ow padajacych na jeden strzal, endless ma byc trudniejszy).
        _base = [20, 15, 12, 10, 8, 6, 5, 3]
        _w = self.endless_wave
        _total = int(sum(_base) * (1 + _w * 0.15))
        _weights = [b * (1 + 0.06 * _w) ** i for i, b in enumerate(_base)]
        _wsum = sum(_weights)
        self.current_wave = [max(1, int(_total * wt / _wsum)) for wt in _weights]
        # Bonus: numer fali x 100 (fala 11 = 1100). Przy SKOKU do fali
        # (grant_gold=False) bonus nie jest wyplacany - tylko ten jeden raz.
        gold = self.wave * 100
        if grant_gold:
            self.money += gold
            self._ach_stats["gold_earned"] = self._ach_stats.get("gold_earned", 0) + gold
            self.gold_notifications.append([tr("notif.gold_wave", gold=gold, wave=self.wave), 150])
        # Deszcz w endless: brak losowych burz, ale gwarantowana burza
        # z Tesla Coil dziala (1 runda, 2 ze Storm Caller). Deszcz
        # przeniesiony z kampanii gasnie po 1 fali endless (wczesniej
        # wisial w nieskonczonosc, bo endless nie mial logiki deszczu).
        if getattr(self, "_tesla_guaranteed_storm", 0) > 0:
            self._tesla_guaranteed_storm -= 1
            self.raining = True
            self._endless_rain_left = 2 if "storm" in self.building_upgrades else 1
            self.raindrops = [(random.randint(0, self.width), random.randint(0, self.height),
                               random.randint(8, 14)) for _ in range(100)]
            sound_rain.play(loops=-1)
        elif self.raining:
            if getattr(self, "_endless_rain_left", 0) > 0:
                self._endless_rain_left -= 1
            if self._endless_rain_left <= 0:
                self.raining = False
                sound_rain.stop()
                self._rainbow_timer = 600
        else:
            # Losowe burze w endless - te same szanse co w kampanii
            # (EASY 20%, NORMAL 15%, HARD 10%; Storm Caller podwaja).
            # Tesla Coil NIE zwieksza szansy - daje tylko gwarantowana
            # burze przy zakupie. Jak w kampanii: nie na falach z bossami.
            if "storm" in self.building_upgrades:
                _chance = self._diff("storm_chance") * 2
            else:
                _chance = self._diff("storm_chance")
            _dnum = self.wave + 1  # wyswietlany numer fali (self.wave juz zwiekszone)
            if _dnum % 10 != 0 and self.endless_wave % 4 != 0 and random.random() < _chance:
                self.raining = True
                # Storm Caller: burza trwaja 2 fale (jak w kampanii)
                self._endless_rain_left = 2 if "storm" in self.building_upgrades else 1
                self.raindrops = [(random.randint(0, self.width), random.randint(0, self.height),
                                   random.randint(8, 14)) for _ in range(100)]
                sound_rain.play(loops=-1)
        # Co 10 fal: ekstra bossowie (fala 20 -> 2, fala 30 -> 3, fala 40 -> 4...).
        # Na falach co 10 zastepuje zwyklego bossa z co-4-falowego cyklu
        # (fala 30 ma 3 bossow, nie 3+1).
        _wave_num = self.wave + 1  # self.wave juz zwiekszone wyzej
        if _wave_num % 10 == 0:
            for _ in range(_wave_num // 10):
                self.pending_bosses.append(
                    Boss(hp=int(self._endless_hp(350, self.endless_wave) * self._diff("enemy_hp_mult"))))
        elif self.endless_wave % 4 == 0:
            # Endless boss: 5x HP + 5% co fale (jak zwykli wrogowie)
            self.pending_bosses.append(
                Boss(hp=int(self._endless_hp(350, self.endless_wave) * self._diff("enemy_hp_mult"))))
        # Call the Cavalry: 50% szans na uderzenie w tej fali (po okaleczeniu pirata)
        self._ally_strike_at = None
        if ("cavalry" in self.building_upgrades and self.pirate_crippled
                and random.random() < 0.5):
            total = sum(self.current_wave)
            # Losowy moment w pierwszej polowie fali (po rozladowanych wrogach)
            self._ally_strike_at = random.randint(1, max(1, total // 2))
            self._ally_unloaded = 0

    def _endless_hp(self, base, endless_wave):
        """HP w endless: 5x bazowo od fali 11, potem +5% co fale (compound).
        Jesli 5% nie daje ani 1 HP, to +1."""
        hp = int(base * 5)
        for _ in range(1, endless_wave):
            bonus = int(hp * 0.05)
            hp += bonus if bonus >= 1 else 1
        return hp

    def _boss_hp(self, wave_num):
        """HP bossa wg fali i trudnosci (po obnizce o 50: bossowie byli za silni).
        Fala 4: EASY 150, NORMAL 200, HARD 250.
        Fala 8: EASY 350, NORMAL 450, HARD 550."""
        if wave_num == 8:
            return {"EASY": 350, "NORMAL": 450, "HARD": 550}.get(self.difficulty, 450)
        return {"EASY": 150, "NORMAL": 200, "HARD": 250}.get(self.difficulty, 200)

    def advance_wave(self):
        """Przechodzi do nastepnej fali: zloto, bonusy, powiadomienie. Wywolywane
        gdy plansza jest wyczyszczona i statek ma wrocic."""
        # Przerwane bombardowanie/przechwycenie (np. SKIP w trakcie poscigu
        # kawalerii): reset stanu, zeby zaden stary timeout nie wyrwal statku
        # z doku w trakcie desantu nowej fali. Bez tego statek wyplywal poza
        # mape zanim zdazyl rozpakowac wrogow.
        if self.bombard_active:
            self.bombard_active = False
            self.bombard_phase = 0
            self.bombard_timer = 0
            self.bombard_index = 0
            self.bombard_targets = []
            self.bombard_zoom = 0
            self.bombard_zoom_tower = None
            self._interception_timeout = 0
            self.ship.speed = 3.5
            # Sojusznik z przechwycenia znika (poscig przerwany); tryb 'strike'
            # (atak na wrogow) moze zostac - sam odplynie po salwie.
            if self.ally_ship and getattr(self.ally_ship, "mode", None) != "strike":
                self.ally_ship = None
        # DEBUG LOG
        try:
            with open("wave_debug.log", "a") as f:
                f.write(f"advance_wave: wave {self.wave} -> {self.wave+1}, enemies={len(self.enemies)}, waiting={self.waiting_for_clear}\n")
        except:
            pass
        # Achievements: czysta fala (bez utraty zyc) - liczy tez fale 1
        _lives_lost_this_wave = self._wave_start_lives - self.lives
        if _lives_lost_this_wave == 0:
            self._ach_stats["flawless_waves"] = self._ach_stats.get("flawless_waves", 0) + 1
        # 9: raport po fali
        if self.wave > 0 or self.endless_wave > 0:
            kills = self.stats_kills - self._wave_kills_start
            gold = self.stats_gold - self._wave_gold_start
            lives_lost = self._wave_start_lives - self.lives
            # MVP: wieza z najwieksza liczba zabojstw
            mvp = max(self.towers, key=lambda t: t.kills, default=None)
            mvp_text = f"{i18n.tower_name(type(mvp).__name__, getattr(mvp, 'display_name', mvp.name))} ({mvp.kills})" if mvp else "-"
            report = tr("report.wave", wave=self.wave + 1, kills=kills, lives=lives_lost, gold=gold, mvp=mvp_text)
            self.wave_report = [report, 240]
        self._wave_kills_start = self.stats_kills
        self._wave_gold_start = self.stats_gold
        sound_fanfare.play()  # 40: fanfara fali
        # Repair Drones: +1 zycie co 2 fale (do maxa)
        if "drones" in self.building_upgrades:
            self._drone_wave_count = getattr(self, "_drone_wave_count", 0) + 1
            if self._drone_wave_count >= 2:
                self._drone_wave_count = 0
                if self.lives < self._start_lives:
                    self.lives += 1
                    self.gold_notifications.append([tr("notif.life_drones"), 150])
        if self.endless:
            # Tryb endless: generuj fale proceduralnie z rosnacym HP
            self._setup_endless_wave()
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
            self._ach_stats["gold_earned"] = self._ach_stats.get("gold_earned", 0) + total
            # Widoczne powiadomienie o zlocie
            parts = [tr("notif.wave_base", gold=base_gold)]
            if bonus > 0:
                parts.append(tr("notif.wave_clean", bonus=bonus))
            self.gold_notifications.append([" | ".join(parts), 180])
            self.wave += 1
            # Achievements: max_wave = wyswietlany numer fali (wave+1)
            self._ach_stats["max_wave"] = max(self._ach_stats.get("max_wave", 0), self.wave + 1)
            # Achievements: fala 8 z pelnymi zyciami
            if self.wave + 1 == 8 and self.lives == self._start_lives:
                self._ach_stats["full_lives_wave8"] = self._ach_stats.get("full_lives_wave8", 0) + 1
            self.current_wave = waves[self.wave][:]
            self._wave_start_lives = self.lives
            self.wave_banner_text = tr("banner.wave", n=self.wave + 1)  # V3
            self.wave_banner_timer = 120  # 2 sekundy
            # U8: modyfikator co 3 fale (nie na bossach)
            self.wave_modifier = None
            wave_num = self.wave + 1
            if wave_num % 3 == 0 and wave_num % 4 != 0 and wave_num != 10:
                mod = random.choice(["swift", "rich", "swarm"])
                self.wave_modifier = mod
                if mod == "swift":
                    self.wave_banner_text += tr("banner.swift")
                elif mod == "rich":
                    self.wave_banner_text += tr("banner.rich")
                elif mod == "swarm":
                    self.current_wave = [int(c * 1.5) for c in self.current_wave]
                    self.wave_banner_text += tr("banner.swarm")
            # 7: deszcz na losowych falach (nie na bossach)
            # Storm Caller: podwaja szanse na burze (20% -> 40%) i burze
            # trwaja dluzej (2 fale zamiast 1).
            # Tesla Coil nie zmienia szansy - daje gwarantowana burze przy zakupie.
            was_raining = self.raining
            _tesla_guaranteed = getattr(self, "_tesla_guaranteed_storm", 0) > 0
            if _tesla_guaranteed:
                self._tesla_guaranteed_storm -= 1
            if "storm" in self.building_upgrades and was_raining and self._storm_extra:
                self._storm_extra = False  # druga fala burzy
            elif _tesla_guaranteed:
                # Tesla Coil: gwarantowana burza w nastepnej rundzie (nawet
                # na fali z bossem - gwarantowana to gwarantowana). Ze Storm
                # Caller _storm_extra przedluza ja na 2 rundy.
                if not was_raining:
                    self.raining = True
                    self.wave_banner_text += tr("banner.rain")
                    self.raindrops = [(random.randint(0, self.width), random.randint(0, self.height),
                                       random.randint(8, 14)) for _ in range(100)]
                    sound_rain.play(loops=-1)  # 38: szum deszczu
                # (jesli juz padalo, burza trwa dalej)
                self._storm_extra = "storm" in self.building_upgrades
            else:
                self.raining = False
                # Szansa na burze wg trudnosci: EASY 20%, NORMAL 15%,
                # HARD 10%. Storm Caller PODWAJA szanse poziomu
                # (40/30/20%). Tesla Coil NIE zwieksza szansy -
                # daje tylko gwarantowana burze przy zakupie.
                if "storm" in self.building_upgrades:
                    storm_chance = self._diff("storm_chance") * 2
                else:
                    storm_chance = self._diff("storm_chance")
                if wave_num % 4 != 0 and wave_num != 10 and random.random() < storm_chance:
                    self.raining = True
                    self.wave_banner_text += tr("banner.rain")
                    self.raindrops = [(random.randint(0, self.width), random.randint(0, self.height),
                                       random.randint(8, 14)) for _ in range(100)]
                    sound_rain.play(loops=-1)  # 38: szum deszczu
                    self._storm_extra = "storm" in self.building_upgrades
                elif was_raining:
                    sound_rain.stop()
                    # B4: tecza po deszczu
                    self._rainbow_timer = 600  # 10s
            # Boss na falach 4 i 8; fala 10 (ostatnia) to sam boss FINALNY.
            # Boss spawnuje sie dopiero gdy statek zadokuje (pending_bosses).
            if (self.wave + 1) % 4 == 0 and self.wave + 1 < 10:
                self.pending_bosses.append(Boss(hp=self._boss_hp(self.wave + 1)))
                self.wave_banner_text = tr("banner.wave_boss", n=self.wave + 1)
            elif self.wave + 1 == 10:
                # Boss finalny: 950 bazowo (-50, jak reszta bossow), skalowany trudnoscia
                self.pending_bosses.append(Boss(final=True, hp=int(950 * self._diff("enemy_hp_mult"))))
                self.wave_banner_text = tr("banner.final_boss")
        self.waiting_for_clear = False
    def _close_all_menus(self, refund_placement=True):
        """Close every open menu / cancel in-progress actions so the cinematic is visible."""
        self._building_menu_open = False
        self._tent_menu_open = False
        self._show_help = False
        self.menu_dragging = False
        if getattr(self, "selected_tower", None) is not None:
            try:
                self.selected_tower.selected = False
            except Exception:
                pass
            self.selected_tower = None
        for tw in getattr(self, "towers", []):
            try:
                tw.selected = False
            except Exception:
                pass
        if getattr(self, "moving_object", None) is not None:
            if refund_placement:
                try:
                    self.money += self.shop_price(self.moving_object.name)
                except Exception:
                    pass
            try:
                self.moving_object.moving = False
            except Exception:
                pass
            self.moving_object = None
        if getattr(self, "show_menu", False):
            self.show_menu = False
            self.paused = False

    def _start_bombardment(self, num_targets=3):
        """Rozpoczyna cinematic bombardowania: statek plynie na srodek oceanu.
        Call the Cavalry: pierwsze bombardowanie w endless po kupnie - przechwycenie."""
        # Przechwycenie: sojusznik niszczy pirata zamiast barazu w wieze
        if (self.endless and "cavalry" in self.building_upgrades
                and not self.pirate_crippled):
            self._start_interception()
            return
        # Okaleczony pirat juz nigdy nie bombarduje
        if self.pirate_crippled:
            self.ship.sail_out()
            return
        # Zamknij wszystkie menu - cinematic ma byc widoczny, nie zakryty menu
        self._close_all_menus()
        self.bombard_active = True
        self.bombard_phase = 0  # 0: statek plynie na srodek
        self.bombard_timer = 0
        self.bombard_index = 0
        # Wybierz losowe wieze (domyslnie do 3, w endless 2)
        if self.towers:
            self.bombard_targets = random.sample(self.towers, min(num_targets, len(self.towers)))
        else:
            self.bombard_targets = []
        self.wave_banner_text = tr("banner.barrage")
        self.wave_banner_timer = 180
        # Statek plynie na pozycje wybrana przez gracza (867, 603)
        self.ship.sail_to_bombard(867, 603)

    def _start_interception(self):
        """Sojuszniczy statek wplywa z lewej i unieszkodliwia pirata.
        Najpierw pirat na spokojnie doplywa na pozycje, DOPIERO POTEM wplywa sojusznik."""
        # Zamknij wszystkie menu - cinematic ma byc widoczny
        self._close_all_menus()
        self.bombard_active = True
        self.bombard_phase = 10  # 10: czekamy az pirat doplynie
        self.bombard_timer = 0
        self._interception_timeout = 0
        self.wave_banner_text = tr("banner.cavalry")
        self.wave_banner_timer = 200
        # Pirat plynie na pozycje barazu (jak zwykle)
        self.ship.sail_to_bombard(867, 603)
        # Sojusznik wystartuje dopiero gdy pirat bedzie na miejscu
        self.ally_ship = None

    def _update_ally_ship(self):
        """Sojusznik w trybie 'strike': po doplynieciu strzela 1-4 razy w wrogow."""
        if not self.ally_ship or self.ally_ship.mode != "strike":
            return
        if self.ally_ship.state == AllyShip.FIRING:
            living = [en for en in self.enemies
                      if not en.dying and not en.dead and not en.reached_end]
            if not living:
                # Nie ma w kogo strzelic - odplywa
                self.ally_ship.sail_out()
                return
            self._ally_fire_timer -= 1
            if self._ally_fire_timer <= 0:
                if self._ally_shots_left <= 0:
                    # Nowa salwa: 1-4 strzaly
                    self._ally_shots_left = random.randint(1, 4)
                tgt = random.choice(living)
                self._fire_mortar(tgt.x, tgt.y - 20)
                self._ally_shots_left -= 1
                self._ally_fire_timer = 25  # przerwa miedzy strzalami
                if self._ally_shots_left <= 0:
                    self.ally_ship.sail_out()
        elif self.ally_ship.state == AllyShip.AWAY:
            self.ally_ship = None

    def _fire_mortar(self, tx, ty):
        """Pocisk mozdzierzowy: luk paraboliczny, 500 dmg + splash."""
        if not self.ally_ship:
            return
        sx, sy = self.ally_ship.x + 60, self.ally_ship.y - 40
        self.mortar_shots.append({
            "x0": sx, "y0": sy, "x1": tx, "y1": ty,
            "t": 0.0, "dur": 55,  # klatek lotu
            "dmg": 500, "splash": 110,
            "trail": [],
        })
        self.ally_ship.cannon_flash = 20
        try:
            sound_ab_meteor.play()
        except:
            pass

    def _update_mortars(self):
        """Lot pociskow mozdzierzowych po paraboli + eksplozje."""
        for m in self.mortar_shots[:]:
            m["t"] += 1.0 / m["dur"]
            t = m["t"]
            if t >= 1.0:
                self.mortar_shots.remove(m)
                self._mortar_explode(m["x1"], m["y1"], m["dmg"], m["splash"])
            else:
                m["trail"].append((m["x0"] + (m["x1"] - m["x0"]) * t,
                                   m["y0"] + (m["y1"] - m["y0"]) * t
                                   - math.sin(math.pi * t) * 160))
                if len(m["trail"]) > 12:
                    m["trail"].pop(0)

    def _mortar_explode(self, x, y, dmg, splash):
        """Eksplozja mozdzierza: obrazenia obszarowe."""
        self.particles.burst(x, y, (255, 150, 50), count=25, speed=6, life=35, size=5)
        self.particles.burst(x, y, (80, 80, 80), count=12, speed=3, life=50, size=6)
        self.shockwaves.append(Shockwave(x, y, max_r=splash + 30))
        self.screen_shake = 8
        for en in self.enemies[:]:
            if en.dying or en.dead or en.reached_end:
                continue
            d2 = (en.x - x) ** 2 + (en.y - y) ** 2
            if d2 < splash ** 2:
                # Przez hit() jak kazde inne obrazenia - wczesniej zwykle
                # odjecie HP: wrog z HP <= 0 NIGDY nie umieral (hit() jako
                # jedyny ustawial dying), chodzil dalej i nie placil zlota.
                try:
                    en.hit(dmg)
                except Exception:
                    en.health -= dmg
                    if en.health <= 0 and not en.dying:
                        en.dying = True
                self.stats_damage += dmg
                self.damage_numbers.append([en.x, en.y - 40, str(dmg), 60])

    def _draw_mortars(self):
        """Rysuje pociski mozdzierzowe (kule z ognistym sladem)."""
        for m in self.mortar_shots:
            # Slad
            for i, (tx, ty) in enumerate(m["trail"]):
                a = int(120 * i / max(1, len(m["trail"])))
                pygame.draw.circle(self.win, (255, 150, 50, a), (int(tx), int(ty)), 4)
            # Kula
            t = min(1.0, m["t"])
            x = m["x0"] + (m["x1"] - m["x0"]) * t
            y = m["y0"] + (m["y1"] - m["y0"]) * t - math.sin(math.pi * t) * 160
            pygame.draw.circle(self.win, (40, 40, 40), (int(x), int(y)), 9)
            pygame.draw.circle(self.win, (255, 120, 30), (int(x), int(y)), 9, 2)
            # Plomien
            pygame.draw.circle(self.win, (255, 200, 80, 200), (int(x) - 6, int(y) + 4), 5)

    def _tent_damage_mult(self, en):
        """Mnoznik obrazen z upgradow namiotu (Scout, Guerrilla)."""
        mult = 1.0
        # Scout Reports: +25% w pierwsze 4s po spawnie (zasadzka) - w tickach logiki,
        # wiec pauza i predkosc 2x/3x nie psuja okna (wczesniej time.time()).
        if "scout" in self.tent_upgrades:
            if self._logic_tick - getattr(en, "_spawn_tick", 0) < 400:
                mult *= 1.25
        # Guerrilla Training: +35% vs spowolnionych
        if "guerrilla" in self.tent_upgrades:
            if getattr(en, "slow_timer", 0) > 0:
                mult *= 1.35
        return mult

    def draw_tesla_coil(self):
        """Widoczna cewka Tesli na budynku - stad strzela piorun."""
        tx, ty = 308, 198  # na dachu budynku (z drag tool, 2026-10-14)
        # Podstawa
        pygame.draw.rect(self.win, (60, 65, 75), (tx - 20, ty, 40, 12))
        # Cewka (uzwojenie)
        for i in range(6):
            y = ty - 8 - i * 10
            pygame.draw.ellipse(self.win, (150, 160, 175), (tx - 15, y, 30, 12))
            pygame.draw.ellipse(self.win, (100, 110, 125), (tx - 15, y, 30, 12), 2)
        # Elektroda (kula na gorze)
        pygame.draw.circle(self.win, (180, 190, 205), (tx, ty - 75), 12)
        pygame.draw.circle(self.win, (220, 235, 250), (tx - 4, ty - 79), 5)
        # Iskry (losowe, ciagle)
        if random.random() < 0.4:
            ax = tx + random.randint(-25, 25)
            ay = ty - 75 + random.randint(-20, 20)
            self.particles.burst(ax, ay, (150, 220, 255), count=2, speed=2, life=15, size=2)
        # Pulsujaca aura
        pulse = int(30 + 20 * math.sin(self._anim_s * 3))
        s = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(s, (150, 220, 255, pulse), (50, 50), 40, 2)
        self.win.blit(s, (tx - 50, ty - 120))
        # Pioruny walace W cewke (burza): blysk z nieba w kule, potem
        # wyladowanie splywa po grafice cewki w dol do podstawy.
        for st in getattr(self, "_coil_strikes", []):
            if st["phase"] == "bolt":
                pts = st["pts"]
                pygame.draw.lines(self.win, (255, 250, 200), False, pts, 3)
                pygame.draw.lines(self.win, (255, 255, 255), False, pts, 1)
                pygame.draw.circle(self.win, (255, 255, 220), (308, 123), 14)
            else:
                prog = 1.0 - st["t"] / 16.0
                gy = int(123 + prog * 75)  # kula (123) -> podstawa (198)
                pygame.draw.circle(self.win, (255, 240, 150), (308, gy), 6)
                pygame.draw.circle(self.win, (150, 220, 255), (308, gy), 11, 2)

    def _place_spikes(self):
        """Rozstawia kolce na drodze (3 klastry na sciezce wrogow).
        Kazdy klaster to osobny, klikalny obiekt (upgrade + sprzedaz)."""
        # Punkty na drodze (srodek mapy)
        base_pts = [(696, 570), (944, 477), (448, 414)]
        pm = self._diff("price_mult")
        self._spikes = [SpikeCluster(x + random.randint(-20, 20), y + random.randint(-10, 10), pm)
                        for x, y in base_pts]

    def _update_spikes(self):
        """Kolce rania przechodzacych wrogow (dps wg poziomu klastra: 8/14/22).
        Uzywa hit(), wiec moga zabijac (kills liczone do menu klastra,
        zloto z monety ladowanej przy smierci wroga - jak przy wiezach).
        Zasieg po HITBOXIE sprite'a (promien 55), nie po srodku wroga -
        wczesniej szybcy/grubsi wrogowie przechodzili niemal bez obrazen."""
        if "spikes" not in self.tent_upgrades or not self._spikes:
            return
        for sp in self._spikes:
            for en in self.enemies:
                if en.dying or en.dead or en.reached_end:
                    continue
                if en.hitbox_in_radius(sp.x, sp.y, 55):
                    dmg = sp.damage / 100.0  # dps przy logice 100 Hz
                    was_dying = en.dying
                    try:
                        en.hit(dmg)
                    except Exception:
                        en.health -= dmg
                        if en.health <= 0 and not en.dying:
                            en.dying = True
                    if not was_dying and en.dying:
                        sp.kills += 1
                    self.stats_damage += dmg
                    if random.random() < 0.1:
                        self.damage_numbers.append([en.x, en.y - 40, f"{sp.damage:.0f}", 30])

    def draw_achievement_popup(self):
        """Popup odblokowanego achievementu (prawy gorny rog)."""
        if not self._ach_popup:
            return
        name, desc, icon_cat = self._ach_popup
        pw, ph = 320, 80
        px = self.width - pw - 20
        py = 90
        # Tlo
        s = pygame.Surface((pw, ph), pygame.SRCALPHA)
        s.fill((20, 25, 35, 220))
        pygame.draw.rect(s, (255, 215, 100, 200), s.get_rect(), 2, border_radius=10)
        self.win.blit(s, (px, py))
        # Ikona
        icon = self.ach_mgr.icons.get(icon_cat)
        if icon:
            self.win.blit(icon, (px + 10, py + 16))
        # Tekst
        t1 = self.font_btn18.render(tr("ach.unlocked"), True, (255, 215, 100))
        t2 = self.font_small30.render(name, True, (255, 255, 255))
        self.win.blit(t1, (px + 68, py + 10))
        self.win.blit(t2, (px + 68, py + 35))

    # Linia zrzutu bomb balonu (narysowana przez gracza, 2026-10-14):
    # bomby spadaja PIONOWO z balonu na linie, wprost ponizej balonu.
    _BALLOON_LINE = [(338, 654), (377, 641), (431, 625), (485, 599), (506, 590),
                     (615, 574), (724, 563), (834, 551), (929, 540), (987, 531),
                     (1019, 527), (1046, 505)]

    def _balloon_line_y(self, x):
        """Y linii zrzutu dla danego x (interpolacja). None jesli x poza linia."""
        pts = self._BALLOON_LINE
        if x < pts[0][0] or x > pts[-1][0]:
            return None
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            if x1 <= x <= x2:
                if x2 == x1:
                    return y1
                t = (x - x1) / (x2 - x1)
                return y1 + (y2 - y1) * t
        return pts[-1][1]

    def draw_tent_visuals(self):
        """Wizualne efekty upgradow namiotu: ognisko, kolce, balon. (Choragiew usunieta.)"""
        # Tesla Coil: widoczna cewka na budynku (musi byc przed innymi)
        if "tesla" in self.building_upgrades:
            self.draw_tesla_coil()
        # Honor Banner: bez wizualnej choragwi (wygladala nie na miejscu) - tylko +10% dmg
        # Signal Fire: uzywa istniejacego ogniska (2x wieksze) - brak osobnego wizualu
        # Spike Barricade: kolce na drodze
        if "spikes" in self.tent_upgrades:
            for sp in self._spikes:
                sx, sy = sp.x, sp.y
                for i in range(5):
                    px = sx - 20 + i * 10
                    pygame.draw.polygon(self.win, (139, 90, 43),
                                        [(px - 5, sy + 8), (px + 5, sy + 8), (px, sy - 14)])
                    pygame.draw.polygon(self.win, (90, 60, 30),
                                        [(px - 5, sy + 8), (px + 5, sy + 8), (px, sy - 14)], 1)
        # Recon Balloon: TYLKO rysowanie. Balon istnieje dopiero po
        # zakupie upgradu; ruch, zrzut bomb i wybuchy liczy _update_balloon
        # w logice (ticki) - na pauzie balon stoi w miejscu i nie zrzuca.
        if "balloon" in self.tent_upgrades:
            bx = self._balloon_x
            by = 120 + 15 * math.sin(self._balloon_x * 0.01)
            # Balon: model z zakladki upgradow (obrazek), fallback do rysowanego gdy brak pliku
            if getattr(self, "_balloon_img", None) is not None:
                self.win.blit(self._balloon_img, (int(bx - 32), int(by - 51)))
            else:
                pygame.draw.ellipse(self.win, (200, 80, 80), (bx - 30, by - 40, 60, 50))
                pygame.draw.ellipse(self.win, (220, 120, 120), (bx - 20, by - 35, 40, 40))
                pygame.draw.rect(self.win, (101, 67, 33), (bx - 12, by + 15, 24, 18))
                pygame.draw.line(self.win, (80, 50, 25), (bx - 20, by + 10), (bx - 12, by + 15), 2)
                pygame.draw.line(self.win, (80, 50, 25), (bx + 20, by + 10), (bx + 12, by + 15), 2)
        # Spadajace bomby balonu (pozycje liczy logika, tu tylko obrazek)
        for bomb in self._balloon_bombs:
            pygame.draw.circle(self.win, (50, 50, 60), (int(bomb["x"]), int(bomb["y"])), 8)
            pygame.draw.rect(self.win, (100, 100, 110), (int(bomb["x"]) - 3, int(bomb["y"]) - 12, 6, 5))

    def _update_balloon(self):
        """Logika balonu w tickach logiki (100 Hz): ruch, zrzut bomb co 3 s
        pionowo na linie bomby, lot bomb i wybuchy. Wywolywane tylko z
        update_game_logic - pauza zatrzymuje balon i bomby w powietrzu."""
        if "balloon" not in self.tent_upgrades:
            return
        self._balloon_x += 0.3  # 30 px/s (dawniej 0.5 px na klatke rysowania)
        if self._balloon_x > self.width + 100:
            self._balloon_x = -100
        bx = self._balloon_x
        by = 120 + 15 * math.sin(bx * 0.01)
        # Zrzut bomby co 3s, PIONOWO na narysowana linie (wprost ponizej balonu).
        # Timer liczy tylko gdy balon jest nad linia (od punktu 1). Bez celowania we wrogow.
        line_y = self._balloon_line_y(bx)
        if line_y is not None:
            self._balloon_bomb_cd -= 1
            if self._balloon_bomb_cd <= 0:
                self._balloon_bombs.append({"x": bx, "y": by + 55, "vy": 1.2, "land_y": line_y})
                self._balloon_bomb_cd = 300  # 3 s przy 100 Hz
        # Bomby spadaja PIONOWO na linie (wprost ponizej miejsca zrzutu).
        for bomb in self._balloon_bombs[:]:
            bomb["vy"] += 0.054  # grawitacja (0.15/klatke 60 FPS przeliczone na ticki)
            bomb["y"] += bomb["vy"]
            # Wybuch na linii (land_y), nie na stalym y=640
            if bomb["y"] >= bomb["land_y"]:
                ex, ey = bomb["x"], bomb["land_y"]
                self._balloon_bombs.remove(bomb)
                self.particles.burst(ex, ey, (255, 150, 50), count=25, speed=5, life=35, size=6)
                self.particles.burst(ex, ey, (100, 100, 100), count=15, speed=3, life=50, size=8)
                self.shockwaves.append(Shockwave(ex, ey, max_r=90, color=(255, 150, 50)))
                for en in self.enemies:
                    if en.dying or en.dead or en.reached_end:
                        continue
                    if (en.x - ex) ** 2 + (en.y - ey) ** 2 < 90 ** 2:
                        try:
                            en.hit(150)
                        except Exception:
                            en.health -= 150
                            if en.health <= 0 and not en.dying:
                                en.dying = True
                        self.stats_damage += 150
                        self.damage_numbers.append([en.x, en.y - 40, "150", 60])

    def _update_bombardment(self):
        """Cinematic bombardowania - fazy."""
        if not self.bombard_active:
            return
        self.bombard_timer += 1
        if self.bombard_phase == 0:
            # Czekamy az statek doplynie na srodek
            if self.ship.state == Ship.BOMBARD:
                self.bombard_phase = 1
                self.bombard_timer = 0
                self.bombard_index = 0
        elif self.bombard_phase == 1:
            # Wybierz nastepny cel lub zakoncz
            if self.bombard_index >= len(self.bombard_targets):
                # Koniec - statek odplywa
                self.bombard_phase = 3
                self.bombard_timer = 0
                self.ship.sail_out_from_bombard()
            else:
                tw = self.bombard_targets[self.bombard_index]
                # Sprawdz czy wieza jeszcze istnieje (mogla zostac sprzedana)
                if tw not in self.towers:
                    self.bombard_index += 1
                    return
                self.bombard_zoom_tower = tw
                self.bombard_zoom = 1  # zoom in
                self.bombard_phase = 2
                self.bombard_timer = 0
        elif self.bombard_phase == 2:
            # Zoom in (60 tickow), potem strzal
            if self.bombard_timer == 60:
                # Wystrzel!
                tw = self.bombard_zoom_tower
                sx, sy = self.ship.x, self.ship.y - 20
                self.cannonballs.append({
                    "x": sx, "y": sy,
                    "tx": tw.x, "ty": tw.y,
                    "tower": tw,
                    "speed": 10,
                    "trail": [],
                    "bombard": True,  # flaga zeby wiedziec ze to z cinematic
                })
                self.ship.cannon_flash = 30
                try:
                    sound_ab_meteor.play()
                except:
                    pass
            # Czekamy az pocisk trafi (obslugiwane w _update_cannonballs)
            # Przejscie do nastepnego celu nastepuje po trafieniu
        elif self.bombard_phase == 3:
            # Statek odplywa - czekamy az zniknie
            if self.ship.state == Ship.AWAY:
                self.bombard_active = False
                self.bombard_phase = 0
                self.bombard_zoom = 0
                self.bombard_zoom_tower = None
                # Normalny przeplyw: statek juz odplynal, czekamy na wyczyszczenie
        # === PRZECHWYCENIE (Call the Cavalry) ===
        elif self.bombard_phase == 10:
            # Faza 10a: czekamy az pirat na spokojnie doplynie na pozycje
            # Timeout awaryjny: jesli pirat nie doplywa, odblokuj
            self._interception_timeout += 1
            if self._interception_timeout > 1800:  # 30s
                self.bombard_active = False
                self.bombard_phase = 0
                self.ally_ship = None
                self.ship.sail_out_from_bombard()
                return
            if self.ship.state == Ship.BOMBARD and not self.ally_ship:
                # Pirat na miejscu - DOPIERO TERAZ wplywa sojusznik (powoli, do portu)
                self.ally_ship = AllyShip(os.path.join("images", "ship_ally.png"),
                                          screen_w=self.width)
                self.ally_ship.sail_in("cripple", fire_x=350)
            # Faza 10b: czekamy az sojusznik doplynie
            if (self.ally_ship and self.ally_ship.state == AllyShip.FIRING):
                self.bombard_phase = 11
                self.bombard_timer = 0
                self._interception_timeout = 0
        elif self.bombard_phase == 11:
            # Sojusznik wali salwa w pirata (3 potezne strzaly)
            if self.bombard_timer == 30:
                self._ally_broadside_at_pirate()
            if self.bombard_timer >= 150:
                # Pirat okaleczony - UCIEKA w prawo, sojusznik GONI!
                self.pirate_crippled = True
                self._ach_stats["pirate_crippled"] = 1
                self.wave_banner_text = tr("banner.crippled")
                self.wave_banner_timer = 200
                # Pirat ucieka w prawo (szybciej niz zwykle)
                self.ship.state = Ship.OUT
                self.ship.from_left = False  # w prawo
                self.ship.speed = 5.0
                if self.ally_ship:
                    self.ally_ship.chase()
                self.bombard_phase = 12
                self.bombard_timer = 0
        elif self.bombard_phase == 12:
            # Poscig: oba statki w prawo. Odblokowanie dopiero jak oba znikna.
            # Timeout awaryjny 20s
            self._interception_timeout += 1
            ally_gone = not self.ally_ship or self.ally_ship.state == AllyShip.AWAY
            if (self.ship.state == Ship.AWAY and ally_gone) or self._interception_timeout > 1200:
                self.bombard_active = False
                self.bombard_phase = 0
                self.ship.speed = 3.5
                self.ship.state = Ship.AWAY
                self.ally_ship = None

    def _ally_broadside_at_pirate(self):
        """Salwa sojusznika w piracki statek (wizualne zniszczenie)."""
        if not self.ally_ship:
            return
        sx, sy = self.ally_ship.x + 80, self.ally_ship.y - 20
        tx, ty = self.ship.x, self.ship.y - 20
        for i in range(3):
            self.cannonballs.append({
                "x": sx, "y": sy,
                "tx": tx + random.randint(-30, 30), "ty": ty + random.randint(-20, 20),
                "speed": 12,
                "trail": [],
                "ally_vs_pirate": True,  # nie rani wiez, tylko efekt
            })
        self.ally_ship.cannon_flash = 30
        try:
            sound_ab_meteor.play()
        except:
            pass

    def _update_cannonballs(self):
        """Aktualizacja pociskow armatnich."""
        for cb in self.cannonballs[:]:
            # Ruch w strone celu
            dx = cb["tx"] - cb["x"]
            dy = cb["ty"] - cb["y"]
            dist = max(1, (dx*dx + dy*dy) ** 0.5)
            if dist < 15:
                # Trafienie!
                self.cannonballs.remove(cb)
                # Salwa sojusznika w pirata: tylko efekt wizualny
                if cb.get("ally_vs_pirate"):
                    self.particles.burst(cb["tx"], cb["ty"], (255, 150, 50), count=25, speed=6, life=40, size=5)
                    self.particles.burst(cb["tx"], cb["ty"], (80, 80, 80), count=15, speed=3, life=60, size=6)
                    self.screen_shake = 10
                    self.shockwaves.append(Shockwave(cb["tx"], cb["ty"], max_r=100))
                    continue
                tw = cb["tower"]
                # Eksplozja
                self.particles.burst(cb["tx"], cb["ty"], (255, 150, 50), count=20, speed=5, life=30, size=4)
                self.screen_shake = 8
                # 50% szans na zniszczenie wiezy (Field Medic: 25%)
                destroy_chance = 0.25 if "medic" in self.tent_upgrades else 0.5
                if random.random() < destroy_chance and tw in self.towers:
                    # Wieza rozpada sie na kawalki
                    for _ in range(15):
                        self.particles.burst(tw.x + random.randint(-20, 20),
                                           tw.y + random.randint(-20, 20),
                                           (139, 90, 43), count=3, speed=4, life=40, size=5)
                    self.towers.remove(tw)
                    self.stats_towers_lost += 1
                    if self.selected_tower == tw:
                        self.selected_tower = None
                    self.gold_notifications.append([tr("notif.tower_destroyed"), 150])
                else:
                    self.gold_notifications.append([tr("notif.tower_survived"), 120])
                # Jesli to byl strzal z cinematic, przejdz do nastepnego celu
                if cb.get("bombard") and self.bombard_active and self.bombard_phase == 2:
                    self.bombard_index += 1
                    self.bombard_zoom = 2  # zoom out
                    self.bombard_phase = 1
                    self.bombard_timer = 0
            else:
                cb["x"] += dx / dist * cb["speed"]
                cb["y"] += dy / dist * cb["speed"]
                cb["trail"].append((cb["x"], cb["y"]))
                if len(cb["trail"]) > 10:
                    cb["trail"].pop(0)

    def _draw_cannonballs(self):
        """Rysowanie pociskow armatnich - duze, widoczne, z ogniowa smuga."""
        for cb in self.cannonballs:
            # Ognista smuga
            for i, (tx, ty) in enumerate(cb["trail"]):
                alpha = int(200 * (i / max(1, len(cb["trail"]))))
                size = int(4 + 6 * (i / max(1, len(cb["trail"]))))
                # Pomaranczowa smuga
                pygame.draw.circle(self.win, (255, 150, 50, alpha), (int(tx), int(ty)), size)
            # Duza kula armatnia z ogniem
            x, y = int(cb["x"]), int(cb["y"])
            # Zewnetrzny ogien
            pygame.draw.circle(self.win, (255, 100, 30, 180), (x, y), 14)
            pygame.draw.circle(self.win, (255, 180, 60, 220), (x, y), 10)
            # Rdzen kuli
            pygame.draw.circle(self.win, (40, 40, 40), (x, y), 7)
            pygame.draw.circle(self.win, (120, 120, 120), (x - 2, y - 2), 3)

    def run(self):
        self._music_intense = False
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

            # Spawn wrogow: w update_game_logic (ticki logiki 100Hz), wiec
            # predkosc 2x/3x naprawde przyspiesza rozladunek statku.
            # Statek w tempie logiki 100Hz (akumulator, z capem) - pauza blokuje
            if not self.paused:
                # Statek plynie szybciej w trybie 2x/3x (jak reszta logiki).
                ship_acc = min(ship_acc + (LOGIC_HZ / RENDER_FPS) * self.speed, 5.0)
                while ship_acc >= 1.0:
                    self.ship.update()
                    if self.ally_ship:
                        self.ally_ship.update()
                        self._update_ally_ship()
                    ship_acc -= 1.0
                self._update_cannonballs()
                self._update_bombardment()
                self._update_mortars()
            if self.ship.state == Ship.AWAY and not self.won:
                if self.last_wave_done:
                    self.won = True
                elif self.waiting_for_clear:
                    # Statek odplynal po rozladunku - czekamy na wyczyszczenie planszy.
                    # Nastepna fala dopiero gdy nie ma wrogow.
                    if len(self.enemies) == 0:
                        self._clear_timer = 0
                        self.advance_wave()
                        if not self.last_wave_done:
                            # Statek wraca losowo z lewej lub prawej (sail_in losuje strone)
                            self.ship.sail_in()
                    else:
                        # Zabezpieczenie: awans TYLKO gdy wrogowie NAPRAWDE utkneli
                        # (nic sie nie rusza ani nie ginie przez 20s). Wczesniej
                        # licznik odpalal tez przy zywych, walczacych wrogach -
                        # w endless (fala 20+) kasowal ich i statek od razu
                        # zaczynal nastepna fale. Pauza nie liczy sie do czasu.
                        if self.paused:
                            self._clear_timer = 0
                            self._clear_snap = None
                        else:
                            _snap = (len(self.enemies),
                                     tuple((round(en.x, 1), round(en.y, 1), bool(en.dying))
                                           for en in self.enemies))
                            if _snap != getattr(self, "_clear_snap", None):
                                self._clear_snap = _snap
                                self._clear_timer = 0
                            else:
                                self._clear_timer += 1
                                if self._clear_timer > 1200:  # 20 sekund przy 60 FPS
                                    self._clear_timer = 0
                                    self._clear_snap = None
                                    self.enemies.clear()
                                    self.advance_wave()
                                    if not self.last_wave_done:
                                        self.ship.sail_in()
                else:
                    self.ship.sail_in()
            pos = self._mouse_pos()                 
            if self.moving_object:
                self.moving_object.move(pos[0], pos[1])
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                # Przeciganie sklepu
                if event.type == pygame.MOUSEMOTION and self.menu_dragging:
                    _gx, _gy = self._to_game_pos(event.pos)
                    self.menu.x = max(100, min(self.width - 100, _gx + self.menu_drag_dx))
                    self.menu.y = max(190, min(self.height - 190, _gy + self.menu_drag_dy))
                if event.type == pygame.MOUSEBUTTONUP:
                    self.menu_dragging = False
                if event.type == pygame.KEYDOWN:
                    # ESC = cancel first, pause menu only if nothing to cancel
                    if event.key == pygame.K_ESCAPE:
                        if getattr(self, '_show_help', False):
                            self._show_help = False
                        elif getattr(self, '_building_menu_open', False):
                            self._building_menu_open = False
                        elif getattr(self, '_tent_menu_open', False):
                            self._tent_menu_open = False
                        elif getattr(self, 'moving_object', None) is not None:
                            # Anuluj stawianie wiezy (zwrot kasy)
                            try:
                                self.money += self.shop_price(self.moving_object.name)
                            except Exception:
                                pass
                            try:
                                self.moving_object.moving = False
                            except Exception:
                                pass
                            self.moving_object = None
                        elif getattr(self, 'selected_tower', None) is not None:
                            # Odznacz wieze (zamknij jej menu upgrade)
                            try:
                                self.selected_tower.selected = False
                            except Exception:
                                pass
                            self.selected_tower = None
                        elif getattr(self, 'menu_dragging', False):
                            self.menu_dragging = False
                        elif getattr(self, 'show_menu', False):
                            # Esc w menu = zamknij menu i kontynuuj gre (takze podczas barazu)
                            self.show_menu = False
                            self.paused = False
                        else:
                            # Nic do anulowania - otworz menu pauzy (takze podczas barazu:
                            # pauza zamraza cinematic, drugie Esc wznawia gre)
                            self.show_menu = True
                            self.paused = True
                        continue
                    # Blokada wszystkich klawiszy podczas cinematic (faza 12 - poscig - nie blokuje)
                    if self.bombard_active and self.bombard_phase != 12:
                        continue
                    # Pole fali w menu pauzy ma fokus: klawisze edytuja numer
                    if self.show_menu and getattr(self, "_pause_wave_focus", False):
                        if event.key == pygame.K_BACKSPACE:
                            self._pause_wave_txt = self._pause_wave_txt[:-1]
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            self._do_pause_jump()
                        elif event.unicode and event.unicode.isdigit() and len(self._pause_wave_txt) < 3:
                            self._pause_wave_txt += event.unicode
                        continue
                    # Gdy menu otwarte: blokuj wszystkie akcje wiez
                    if self.show_menu:
                        continue
                    # Q: aktywacja umiejetnosci wybranej wiezy
                    if event.key == pygame.K_q and self.selected_tower:
                        self.selected_tower.activate_ability(self.enemies, self.projectiles)
                    # F11: przelacz fullscreen / okno 1:1 (ostrzejsze piksele)
                    if event.key == pygame.K_F11:
                        self._fullscreen = not self._fullscreen
                        if self._fullscreen:
                            self._screen = pygame.display.set_mode(
                                (self._native_w, self._native_h), pygame.FULLSCREEN)
                        else:
                            # Okno w natywnej rozdzielczosci (czarne tlo, gra 1:1 na srodku)
                            self._screen = pygame.display.set_mode((self._native_w, self._native_h))
                        # Zaktualizuj rzeczywisty rozmiar
                        self._native_w, self._native_h = self._screen.get_size()
                    if event.key == pygame.K_F3:
                        self._debug_show = not getattr(self, '_debug_show', False)
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
                                self._add_gold_spent(cost)
                                self.add_tower(tower_names[idx])
                    # U: upgrade wybranej wiezy, S: sprzedaz
                    if event.key == pygame.K_u and self.selected_tower:
                        cost = self.selected_tower.menu.get_item_cost()
                        if cost != "MAX" and "supply" in self.tent_upgrades:
                            cost = int(cost * 0.85)
                        if cost != "MAX" and self.money >= cost:
                            self.money -= cost
                            self._add_gold_spent(cost)
                            self.selected_tower.upgrade(cost)
                            self._on_tower_upgraded(self.selected_tower)
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
                    # Q16: M - TYLKO muzyka (muzyka + muzyka bossa). SFX nietkniete.
                    # (Wczesniej M wyciszal tez SFX - niezgodnie z podzialem Music / Sound Effects.)
                    if event.key == pygame.K_m:
                        self._set_music_muted(not self.music_muted)
                    # Q11: F5 - zapis, F9 - wczytaj
                    if event.key == pygame.K_F5:
                        self.save_game()
                    if event.key == pygame.K_F9:
                        self.load_game()
                    # Q15: C - filtr wiez (cykl po typach)
                    if event.key == pygame.K_c:
                        types = [None, "Wood", "Metal", "Gold", "Fire", "Blaze"]
                        idx = types.index(self.tower_filter) if self.tower_filter in types else 0
                        self.tower_filter = types[(idx + 1) % len(types)]
                    if event.key == pygame.K_s and self.selected_tower:
                        self.money += self.selected_tower.sell_value(self._diff("sell_mult"))
                        self.towers.remove(self.selected_tower)
                        self._recalc_synergy()
                        self.selected_tower = None
                    elif event.key == pygame.K_s and self.selected_spike:
                        self.money += self.selected_spike.sell_value(self._diff("sell_mult"))
                        self._spikes.remove(self.selected_spike)
                        self.selected_spike = None
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = self._mouse_pos()
                    # Menu ESC ma pierwszenstwo - takze podczas barazu (pauza musi byc klikalna)
                    if self.show_menu:
                        if self._show_help:
                            self._show_help = False
                        elif self._pause_jump_input and self._pause_jump_input.collidepoint(pos):
                            self._pause_wave_focus = True
                        elif self._pause_jump_btn and self._pause_jump_btn.collidepoint(pos):
                            self._do_pause_jump()
                        else:
                            self._pause_wave_focus = False
                            for rect, action in self._menu_buttons:
                                if rect.collidepoint(pos):
                                    self._menu_action(action)
                                    break
                        continue
                    # Blokada inputu podczas cinematic bombardowania (poza menu pauzy)
                    # Faza 12 (poscig) NIE blokuje - statki tylko odplywaja, gracz gra dalej
                    if self.bombard_active and self.bombard_phase != 12:
                        continue
                    # Przeciganie sklepu: klik na panel (poza przyciskami) = drag
                    if self.menu.get_rect().collidepoint(pos):
                        if not self.menu.get_clicked(pos[0], pos[1]):
                            self.menu_dragging = True
                            self.menu_drag_dx = self.menu.x - pos[0]
                            self.menu_drag_dy = self.menu.y - pos[1]
                            continue
                    # Q3: Shift+klik = szybka sprzedaz wiezy / klastra kolcow
                    keys = pygame.key.get_mods()
                    if keys & pygame.KMOD_SHIFT and self.selected_tower:
                        self.money += self.selected_tower.sell_value(self._diff("sell_mult"))
                        self.towers.remove(self.selected_tower)
                        self._recalc_synergy()
                        self.selected_tower = None
                        continue
                    if keys & pygame.KMOD_SHIFT and self.selected_spike:
                        self.money += self.selected_spike.sell_value(self._diff("sell_mult"))
                        self._spikes.remove(self.selected_spike)
                        self.selected_spike = None
                        continue
                    # Ability dock - klikniecie aktywuje umiejetnosc
                    if hasattr(self, 'ability_slots'):
                        for rect, tname in self.ability_slots:
                            if rect.collidepoint(pos):
                                # WSZYSTKIE wieze tego typu z gotowym cooldownem aktywuja umiejetnosc
                                activated = False
                                for tw in self.towers:
                                    if type(tw).__name__.startswith(tname) and tw.ability_cooldown <= 0:
                                        tw.activate_ability(self.enemies, self.projectiles)
                                        activated = True
                                if activated:
                                    self.stats_abilities_used += 1
                                    self._ach_stats["abilities_used"] = self._ach_stats.get("abilities_used", 0) + 1
                                    # Unikalny dzwiek dla kazdej umiejetnosci
                                    snd = {"Wood": sound_ab_rapid, "Metal": sound_ab_frost,
                                           "Gold": sound_ab_gold, "Fire": sound_ab_meteor,
                                           "Blaze": sound_ab_arma}.get(tname)
                                    if snd:
                                        snd.play()
                                continue
                    # R2: przycisk wczesniejszej fali
                    if self.early_wave_rect and self.early_wave_rect.collidepoint(pos):
                        # Nie mozna pominac gdy boss zyje
                        boss_alive = any(isinstance(en, Boss) for en in self.enemies)
                        if boss_alive:
                            self.gold_notifications.append([tr("notif.cannot_skip"), 150])
                        else:
                            bonus = len(self.enemies) * 5
                            self.money += bonus
                            self._ach_stats["gold_earned"] = self._ach_stats.get("gold_earned", 0) + bonus
                            self.gold_notifications.append([tr("notif.rush_bonus", bonus=bonus), 150])
                            # Pozostali wrogowie ZYJA - ida dalej, nowa fala dolacza
                            self.advance_wave()
                            if self.last_wave_done:
                                self.won = True
                            elif not self.won:
                                self.ship.sail_in()
                        continue
                    # Przycisk predkosci (pauza tylko przez ESC)
                    if self.speed_btn_rect.collidepoint(pos):
                        self.speed = self.speed % 3 + 1  # 1->2->3->1
                        continue
                    # Menu upgradow budynku - klik na budynek lub w otwarte menu
                    if self._building_menu_open:
                        if self._building_menu_close_rect.collidepoint(pos):
                            self._building_menu_open = False
                            continue
                        for rect, uid in self._building_menu_buttons:
                            if rect.collidepoint(pos):
                                self._buy_building_upgrade(uid)
                                break
                        continue
                    # Menu upgradow namiotu - klik na namiot lub w otwarte menu
                    if self._tent_menu_open:
                        if self._tent_menu_close_rect.collidepoint(pos):
                            self._tent_menu_open = False
                            continue
                        for rect, uid in self._tent_menu_buttons:
                            if rect.collidepoint(pos):
                                self._buy_tent_upgrade(uid)
                                break
                        continue
                    if self.moving_object:
                        if self.moving_object.name in towers_names:
                            # Swobodne stawianie (bez przyciagania do siatki)
                            mx, my = self.moving_object.x, self.moving_object.y
                            if self.is_valid_placement(mx, my):
                                self.moving_object.menu.x, self.moving_object.menu.y = mx, my
                                self.moving_object.menu.update()
                                # Q14: Shift = kolejka budowy
                                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                                    self.build_queue.append((self.moving_object.name, gx, gy))
                                    self.money += self.shop_price(self.moving_object.name)  # zwrot, pobierze przy budowie
                                else:
                                    self.towers.append(self.moving_object)
                                    self._apply_tower_upgrade_flags(self.moving_object)
                                    self._on_tower_built(self.moving_object)
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
                        continue  # A: stawianie zjada klik - budynek/namiot nie kradna go
                    else:
                        pass
                    side_menu_button = self.menu.get_clicked(pos[0], pos[1])
                    if side_menu_button:
                        # Supply Lines: pobieramy CENE Z RABATEM (wczesniej pobierano
                        # pelna, mimo ze sklep wyswietlal przekreslona - gracz przeplacal).
                        cost = self.shop_price_for_button(side_menu_button)
                        if self.money >= cost:
                            self.money -= cost
                            self._add_gold_spent(cost)
                            self.add_tower(side_menu_button)
                        # Klik w sklep zjada klik - budynek/namiot NIE otwieraja
                        # sie spod sklepu (np. gdy panel nachodzi na namiot).
                        continue
                    
                    btn_clicked = None
                    if self.selected_tower:
                        btn_clicked = self.selected_tower.menu.get_clicked(pos[0], pos[1])
                        if btn_clicked:
                            if btn_clicked == "Upgrade":
                                cost = self.selected_tower.menu.get_item_cost()
                                if cost != "MAX" and "supply" in self.tent_upgrades:
                                    cost = int(cost * 0.85)
                                if cost != "MAX" and self.money >= cost:
                                    self.money -= cost
                                    self._add_gold_spent(cost)
                                    self.selected_tower.upgrade(cost)
                                    self._on_tower_upgraded(self.selected_tower)
                            elif btn_clicked == "Sell":
                                self.money += self.selected_tower.sell_value(self._diff("sell_mult"))
                                self.towers.remove(self.selected_tower)
                                self._recalc_synergy()
                                self.selected_tower = None
                            # Upgrade/Sell zjada klik - budynek/namiot NIE otwieraja sie spod menu
                            continue
                    if self.selected_spike:
                        btn_clicked = self.selected_spike.menu.get_clicked(pos[0], pos[1])
                        if btn_clicked:
                            if btn_clicked == "Upgrade":
                                # Kolce: bez rabatu Supply Lines (rabat dotyczy wiez).
                                # Koszt w menu jest juz skalowany trudnoscia (price_mult).
                                cost = self.selected_spike.menu.get_item_cost()
                                if cost != "MAX" and self.money >= cost:
                                    self.money -= cost
                                    self._add_gold_spent(cost)
                                    self.selected_spike.upgrade(cost)
                            elif btn_clicked == "Sell":
                                self.money += self.selected_spike.sell_value(self._diff("sell_mult"))
                                self._spikes.remove(self.selected_spike)
                                self.selected_spike = None
                            continue
                    # Klik w PANEL menu wiezy (nie tylko w przyciski) zjada klik:
                    # wczesniej klik w puste miejsce panelu (np. obok przycisku)
                    # przechodzil dalej i otwieral budynek/namiot spod menu wiezy.
                    if self.selected_tower is not None:
                        _pr = getattr(self.selected_tower.menu, "panel_rect", None)
                        if _pr is not None and _pr.collidepoint(pos):
                            continue
                    if self.selected_spike is not None:
                        _pr = getattr(self.selected_spike.menu, "panel_rect", None)
                        if _pr is not None and _pr.collidepoint(pos):
                            continue
                    clicked_tower = None
                    for tw in self.towers:
                        if tw.click(pos[0], pos[1]):
                            tw.selected = True
                            clicked_tower = tw
                        else:
                            tw.selected = False
                    # Klik w puste miejsce = odznacz (menu znika jak kiedys)
                    self.selected_tower = clicked_tower
                    # Kolce: klikalne jak wieze (po wiezach, przed budynkiem/namiotem)
                    clicked_spike = None
                    for sp in self._spikes:
                        if sp.click(pos[0], pos[1]):
                            clicked_spike = sp
                            break
                    if clicked_spike is not None:
                        self.selected_spike = clicked_spike
                        self.selected_tower = None
                        for tw in self.towers:
                            tw.selected = False
                    else:
                        # Klik w wieze tez zamyka menu kolca (i odwrotnie -
                        # patrz wyzej); klik w puste miejsce zamyka oba.
                        self.selected_spike = None
                    # C: budynek/namiot otwieraja sie OSTATNIE i tylko gdy nie kliknieto wiezy
                    # (wczesniej kradly klikniecia przy stawianiu/upgradowaniu wiez)
                    if clicked_tower is None and clicked_spike is None:
                        if self._point_in_poly(pos[0], pos[1], self._building_highlight_pts):
                            self._building_menu_open = True
                            continue
                        if self._point_in_poly(pos[0], pos[1], self._tent_highlight_pts):
                            self._tent_menu_open = True
                            continue
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

            if self._forfeit:
                self._forfeit = False
                sound_lose.play()
                result = self.show_end_screen(False, forfeited=True)
                if result == "restart":
                    self.reset_game()
                elif result == "menu":
                    return "menu"
                else:
                    run = False
            elif self.lives <= 0:
                sound_lose.play()
                result = self.show_end_screen(False)
                if result == "restart":
                    self.reset_game()
                elif result == "menu":
                    return "menu"
                else:
                    run = False
            elif self.won:
                sound_win.play()
                result = self.show_end_screen(True)
                if result == "restart":
                    self.reset_game()
                elif result == "menu":
                    return "menu"
                elif result == "continue":
                    # Tryb endless: od razu fala 11 (bez pustego rejsu statku z fali 10)
                    self._ach_stats["endless_entered"] = self._ach_stats.get("endless_entered", 0) + 1
                    self.endless = True
                    self.won = False
                    self.last_wave_done = False
                    self._setup_endless_wave()
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
        self.cannonballs = []
        self.damage_numbers = []
        # Achievements: NIE zeruj _ach_stats - sa skumulowane (plik achievements.json).
        # Zeruj tylko liczniki per-run (Fire/Golden "in one game") i flage wygranej.
        self._run_fire_towers = 0
        self._run_golden_towers = 0
        self._win_recorded = False
        self.lives = self._start_lives
        self.money = self._start_money
        self.wave = 0
        self.current_wave = waves[self.wave][:]
        self.waiting_for_clear = False
        self.won = False
        self.last_wave_done = False
        self.endless = False
        self.endless_wave = 0
        self.paused = False
        self.speed = 1
        self.selected_tower = None
        self.moving_object = None
        self._logic_tick = 0
        self._spawn_cd = 0
        self._wave_start_lives = self._start_lives
        self.stats_kills = 0
        self.stats_gold = 0
        self.stats_damage = 0
        self.stats_kills_by_type = {}
        self.stats_towers_built = 0
        self.stats_towers_lost = 0
        self.stats_abilities_used = 0
        self.stats_gold_spent = 0
        # Reset upgradow budynku
        self.building_upgrades = set()
        self._building_menu_open = False
        self._drone_angle = 0.0
        self._tesla_cooldown = 0
        # Combat drone (Drone Launch Facility) - 100Hz logic ticks
        self._combat_drone = None
        self._facility_rearm = 0
        self._coil_strikes = []  # pioruny walace w cewke Tesli (burza)
        self._facility_tracers = []
        self._facility_blasts = []
        self._facility_rockets = []  # lecace rakiety drona bojowego
        self.pirate_crippled = False
        self.ally_ship = None
        self._ally_strike_at = None
        self._ally_shots_left = 0
        self._ally_fire_timer = 0
        self.mortar_shots = []
        self._storm_extra = False
        # Reset upgradow namiotu
        self.tent_upgrades = set()
        self._tent_menu_open = False
        self._balloon_x = -100
        self._balloon_bomb_cd = 0
        self._balloon_bombs = []
        self._spikes = []
        self.selected_spike = None
        self.pending_bosses = []  # reset: bez zaleglych bossow z poprzedniego runu
        self._tesla_guaranteed_storm = 0
        self._endless_rain_left = 0
        self._clear_snap = None
        self._dancers = [
            {"x": 377, "y": 352, "home_x": 377, "home_y": 352, "alive": True, "sex": "m", "name": "Clyde", "kills": 0, "cd": 0, "mode": "guard", "target": None, "duel_t": 0, "swing": 0},
            {"x": 183, "y": 357, "home_x": 183, "home_y": 357, "alive": True, "sex": "f", "name": "Bonnie", "kills": 0, "cd": 0, "mode": "guard", "target": None, "duel_t": 0, "swing": 0},
        ]
        self._tombstones = []  # reset: no graves in a fresh run
        self._guard_arrows = []  # reset: no arrows in flight in a fresh run
        self.ship = Ship(os.path.join("images", "ship.png"), dock_x=278, dock_y=669,
                         screen_w=self.width)
        self.ship.sail_in()

    def _recalc_synergy(self):
        """Linki sasiadow - tylko gdy wieze sie zmienia, nie co tick.
        Plaskie +15% dmg usuniete: kazdy typ ma unikatowy bonus linku."""
        for tw in self.towers:
            tw._synergy = 1.0
            tw._link = tw.get_link_type(self.towers)

    def _tesla_zap(self, storm=False):
        """Tesla Coil: piorun z kuli (308,123) w najblizszego wroga.
        Pogoda: 75 dmg, zasieg 400, pojedynczy cel (strzal z cooldownu).
        Burza: 100 dmg, zasieg 700, do 3 celow (glowny + 2 w lancuchu) -
        wywolywane TYLKO z konca animacji uderzenia pioruna w cewke.
        Wrogowie wciaz na pomoście (_PIER_RECT) sa ZAWSZE pomijani."""
        bx, by = 308, 123  # electrode ball (z drag tool, 2026-10-14) - zasieg od kuli
        zap_r = 700 if storm else 400  # zasieg w burze: o wiele wiekszy
        _px0, _py0, _pw, _ph = _PIER_RECT

        def _on_pier(en):
            return _px0 <= en.x < _px0 + _pw and _py0 <= en.y < _py0 + _ph

        best, best_d2 = None, zap_r ** 2  # radius z drag tool (bylo 450 od srodka budynku)
        for en in self.enemies:
            if en.dying or en.dead or en.reached_end or _on_pier(en):
                continue
            d2 = (en.x - bx) ** 2 + (en.y - by) ** 2
            if d2 < best_d2:
                best, best_d2 = en, d2
        if not best:
            return
        dmg = 100 if storm else 75
        targets = [best]
        if storm:
            # Lancuch: +2 najblizszych od glownego celu (razem max 3)
            near = sorted(
                (en for en in self.enemies
                 if en is not best and not en.dying and not en.dead and not en.reached_end
                 and not _on_pier(en)
                 and (en.x - best.x) ** 2 + (en.y - best.y) ** 2 < 200 ** 2),
                key=lambda e: (e.x - best.x) ** 2 + (e.y - best.y) ** 2)[:2]
            targets.extend(near)
        prev = (308, 123)  # zap origin z drag tool (electrode ball: coil 308,198 - 75)
        for tgt in targets:
            # hit() ustawia dying przy smierci - liczymy zabojstwa Tesli
            _died = tgt.hit(dmg)
            if _died:
                self._ach_stats["tesla_kills"] = self._ach_stats.get("tesla_kills", 0) + 1
            self.stats_damage += dmg
            self.damage_numbers.append([tgt.x, tgt.y - 40, str(dmg), 60])
            self.particles.burst(tgt.x, tgt.y - 30, (150, 220, 255), count=12, speed=4, size=3)
            # Wizualny piorun (zapisany do rysowania)
            if not hasattr(self, '_tesla_bolts'):
                self._tesla_bolts = []
            self._tesla_bolts.append([prev, (tgt.x, tgt.y - 30), 12])
            prev = (tgt.x, tgt.y - 30)

    def _update_coil_strikes(self):
        """Pioruny walace W cewke Tesli podczas burzy: blysk z nieba w kule,
        potem wyladowanie splywa po grafice cewki w dol do podstawy."""
        if not hasattr(self, "_coil_strikes"):
            self._coil_strikes = []
        if not self._coil_strikes and random.random() < 0.004:  # ~co 2.5 s
            x0 = 308 + random.randint(-60, 60)
            # Poszarpana linia niebo -> kula (308, 123), policzona raz (nie migocze)
            pts = [(x0, 0)]
            for i in range(1, 6):
                t = i / 6
                pts.append((int(x0 + (308 - x0) * t + random.randint(-15, 15)),
                            int(123 * t + random.randint(-8, 8))))
            pts.append((308, 123))
            self._coil_strikes.append({"phase": "bolt", "t": 8, "pts": pts})
        for st in list(self._coil_strikes):
            st["t"] -= 1
            if st["phase"] == "bolt" and st["t"] <= 0:
                st["phase"] = "travel"
                st["t"] = 16
            elif st["phase"] == "travel" and st["t"] <= 0:
                self._coil_strikes.remove(st)
                # Cewka naladowana uderzeniem - wyladowanie idzie we wrogow
                # (to jedyny sposob strzalu Tesli podczas burzy)
                self._tesla_zap(storm=True)

    def update_game_logic(self):
        """Jedna iteracja logiki gry (ruch wrogow, ataki, pociski)."""
        self._logic_tick += 1
        # Spawn wrogow ze statku: w tickach logiki 100Hz, wiec predkosc
        # 2x/3x naprawde przyspiesza rozladunek (wczesniej czas rzeczywisty).
        # Pauza blokuje (update_game_logic nie wywolywane przy pauzie).
        self._spawn_cd -= 1
        if self._spawn_cd <= 0:
            self.gen_enemies()
            self._spawn_cd = int(random.randint(50, 200) * self._diff("spawn_mult"))
        # V3: banner fali
        if self.wave_banner_timer > 0:
            self.wave_banner_timer -= 1
        # Tesla Coil: bez burzy strzal co 180 tickow (75 dmg, 1 cel).
        # W burze NIE ma strzalu z cooldownu - piorun musi najpierw uderzyc
        # w cewke (animacja: bolt z nieba -> travel po cewce), dopiero koniec
        # fazy travel w _update_coil_strikes odpala zap (100 dmg, do 3 celow).
        # Szansa uderzenia 0.004/tick = srednio co ~2.5 s (losowo).
        if "tesla" in self.building_upgrades:
            if self.raining:
                self._update_coil_strikes()
            else:
                self._tesla_cooldown -= 1
                if self._tesla_cooldown <= 0:
                    self._tesla_cooldown = 180
                    self._tesla_zap()
        # Spike Barricade: kolce rania wrogow
        self._update_spikes()
        # Straznicy przy budynku strzelaja z lukow
        self._update_guard_dancers()
        self._update_guard_arrows()
        # Combat drone (Drone Launch Facility)
        self._update_combat_drone()
        self._update_balloon()
        # Achievements: max_gold_held = szczyt kasy (nie tylko przy zabojstwach)
        self._ach_stats["max_gold_held"] = max(self._ach_stats.get("max_gold_held", 0), self.money)
        # Achievements: sprawdzanie co 60 tickow + zapis postepu (kumulatywnie)
        if self.raining:
            self._ach_stats["storm_fights"] = 1
        if self._now % 60 == 0:
            self.ach_mgr.check(self._ach_stats)
            try:
                self.ach_mgr.save_stats(self._ach_stats)
            except:
                pass
            popup = self.ach_mgr.pop_popup()
            if popup:
                self._ach_popup = popup
                self._ach_popup_timer = 300  # 5s
        # Popup achievementu
        if self._ach_popup:
            self._ach_popup_timer -= 1
            if self._ach_popup_timer <= 0:
                self._ach_popup = None
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
                # Moneta doleciala do licznika - DOPIERO TERAZ zloto wchodzi na konto
                amt = getattr(c, "amount", 0) or 0
                if amt:
                    self.money += amt
                    self.stats_gold += amt
                    self._ach_stats["gold_earned"] = self._ach_stats.get("gold_earned", 0) + amt
                    self._ach_stats["max_gold_held"] = max(self._ach_stats.get("max_gold_held", 0), self.money)
                    self.display_money = self.money
                self.coins.remove(c)
        for s in self.shockwaves[:]:
            if s.update():
                self.shockwaves.remove(s)
        if self.screen_shake > 0:
            self.screen_shake -= 1
        if self.boss_intro_dark > 0:
            self.boss_intro_dark -= 1
        for sc in self.scorch_marks[:]:
            sc[2] -= 1
            if sc[2] <= 0:
                self.scorch_marks.remove(sc)
        self.game_time += 1
        # 39: losowe krakanie mew
        self.gull_timer -= 1
        if self.gull_timer <= 0:
            self.gull_timer = random.randint(1200, 2400)
            if not self.sfx_muted:
                sound_gull.play()
        # Q14: kolejka budowy - stawiaj po kolei
        if self.build_queue and not self.moving_object:
            name, gx, gy = self.build_queue[0]
            cost = self.shop_price(name)
            if self.money >= cost and self.is_valid_placement(gx, gy):
                self.money -= cost
                self._add_gold_spent(cost)
                tower_map = {"t1": WoodenTower, "t2": MetalTower, "t3": GoldenTower,
                             "t4": FireTower, "t5": BlazeTower}
                tw = tower_map[name](gx, gy)
                self.towers.append(tw)
                self._apply_tower_upgrade_flags(tw)
                self._on_tower_built(tw)
                self._recalc_synergy()
                self.build_queue.pop(0)
            else:
                self.build_queue.pop(0)  # nie da sie - usun z kolejki
        # Niespodzianka 4: animowany licznik zlota (dogania prawdziwa wartosc)
        if self.display_money < self.money:
            self.display_money = min(self.money, self.display_money + max(1, (self.money - self.display_money) // 10))
        elif self.display_money > self.money:
            self.display_money = self.money
        # Dynamiczna muzyka: intensywna TYLKO podczas bossa (nie przy malych zyciach).
        if self.sound and not self.music_muted:
            boss_alive = any(isinstance(en, Boss) for en in self.enemies)
            want_intense = boss_alive
            if want_intense != self._music_intense:
                self._music_intense = want_intense
                track = "sounds/music_intense.wav" if want_intense else "sounds/music.wav"
                try:
                    pygame.mixer.music.load(track)
                    pygame.mixer.music.play(loops=-1)
                except:
                    pass
        # Animowany licznik zyc
        if self.display_lives < self.lives:
            self.display_lives = min(self.lives, self.display_lives + 1)
        elif self.display_lives > self.lives:
            self.display_lives = max(self.lives, self.display_lives - 1)
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
            # A7: kurz - usuniety na prosbe gracza
            # Slad lodu za spowolnionymi - usuniety na prosbe gracza
            # Slady stop bossa - usuniete na prosbe gracza
            # Boss finalny: ryk przy enrage
            if isinstance(en, Boss) and en.get_roar_request():
                sound_roar.play()
                self.wave_banner_text = tr("banner.enraged")
                self.wave_banner_timer = 90
            # Boss finalny przywoluje miniony
            if isinstance(en, Boss) and en.get_summon_request():
                for _ in range(2):
                    m = Forkman()
                    m.x, m.y = en.x - 30, en.y + 20
                    m.path_pos = en.path_pos
                    m.update()  # inicjalizuj img zeby byly widoczne
                    m.x, m.y = en.x - 30, en.y + 20
                    self.enemies.append(m)
                self.gold_notifications.append([tr("notif.boss_reinforcements"), 120])
        to_del = []
        for en in self.enemies:
            if en.reached_end:
                to_del.append(en)
            elif en.dead:
                to_del.append(en)

        for d in to_del:
            if d.reached_end:
                # Signal Fire: tancerz poswieca sie zamiast utraty zycia
                if self._dancer_sacrifice(d):
                    continue
                sound_1.play()
                sound_glass.play()  # tluczone szklo - budynek jest szklany
                self.lives -= 1
                # Efekt tluczonego szkla przy budynku
                self.particles.burst(300, 350, (180, 220, 255), count=15, speed=3, life=40, size=4, gravity=0.3)
                # Q6: auto-pauza przy 3 zyciach - usunieta na prosbe gracza
            else:
                # Wrog zabity - kasa za niego. WSZYSTKIE mnozniki skladaja sie
                # multiplikatywnie na bazie i zaokraglaja RAZ, w gore (ceil),
                # na samym koncu - wczesniej int() po kazdym kroku zjadal
                # procenty (1 zlota x 1.25 na EASY dawal 1 zamiast 2, a stack
                # bonusow tracil po kilka zlota na kazdym ucienciu).
                # Podloga: zabity wrog NIGDY nie daje mniej niz 1 zlota
                # (tez na HARD: 1 x 0.85 -> ceil = 1).
                _mult = 1.0
                # Golden Touch: podwojna kasa (oznaczeni lub globalny buff)
                if getattr(d, '_gold_marked', False):
                    _mult *= 2.0
                # Link Gold (Midas): zabojstwo zaliczone zlinkowanej wiezy
                # Gold placi +50% zlota
                if getattr(getattr(d, 'last_hit_by', None), '_link', None) == 'gold':
                    _mult *= 1.5
                # Bounty Board: bossowie i elity +50% zlota
                if "bounty" in self.building_upgrades and (isinstance(d, Boss) or d.elite):
                    _mult *= 1.5
                # U8: RICH - +50% zlota
                if self.wave_modifier == "rich":
                    _mult *= 1.5
                # 7: deszcz +15% zlota (Storm Caller: +25%)
                if self.raining:
                    _mult *= 1.25 if "storm" in self.building_upgrades else 1.15
                # War Treasury: +25% zlota
                if "treasury" in self.building_upgrades:
                    _mult *= 1.25
                # Trudnosc: mnoznik zlota za zabojstwa (EASY +25%, HARD -15%)
                _mult *= self._diff("gold_mult")
                reward = max(1, math.ceil(d.money * _mult))
                # self.money += reward - ODLOZONE: moneta doda zloto przy ladowaniu
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
                self._ach_stats["kills"] += 1
                if isinstance(d, Boss):
                    self._ach_stats["boss_kills"] += 1
                if getattr(d, "elite", False):
                    self._ach_stats["elite_kills"] += 1
                # Zloto NIE od razu - dopiero gdy moneta doleci do licznika
                # (patrz update_game_logic: coin landing). Stats zlota tez tam.
                # Zabicia wg typu wroga
                etype = type(d).__name__
                self.stats_kills_by_type[etype] = self.stats_kills_by_type.get(etype, 0) + 1
                # 21: skrzynia skarbow po bossie - usunieta na prosbe gracza
                # 37: spiker serii zabojstw
                now = self._now
                self.kill_streak = [t for t in getattr(self, 'kill_streak', []) if now - t < 3000]
                self.kill_streak.append(now)
                n = len(self.kill_streak)
                if n == 2: self.announce(tr("ann.double"))
                elif n == 3: self.announce(tr("ann.triple"))
                elif n == 5: self.announce(tr("ann.rampage"))
                elif n == 8: self.announce(tr("ann.unstoppable"))
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
                # Lucky Charm: 10% szansy na 2x obrazen krytycznych.
                # Bez Lucky NIE ma krytow (wczesniej: stale 15% dla wszystkich
                # + osobny rzut 10% w wiezy = podwojne krytyki do 4x).
                is_crit = ("lucky" in self.building_upgrades) and random.random() < 0.10
                if is_crit:
                    self._ach_stats["crits"] = self._ach_stats.get("crits", 0) + 1
                crit_mult = 2.0 if is_crit else 1.0
                # Efekty specjalne pociskow umiejetnosci
                if proj.special == "frost_nova":
                    # Frost Nova: spowolnienie wszystkich w duzym promieniu
                    for en in self.enemies:
                        if en.dying or en.dead or en.reached_end:
                            continue
                        if en.hitbox_in_radius(hit_enemy.x, hit_enemy.y, 150):
                            en.apply_slow(240)
                            en.hit(5)
                    self.damage_numbers.append([hit_enemy.x, hit_enemy.y - 50, "FROST NOVA!", 40, (150, 220, 255)])
                elif proj.special == "meteor":
                    # Meteor: 3x obrazen, duzy splash
                    for en in self.enemies:
                        if en.dying or en.dead or en.reached_end:
                            continue
                        if en.hitbox_in_radius(hit_enemy.x, hit_enemy.y, 120):
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
                    # Golden Touch: zamiana sprite'ow na zlote + podwojna kasa.
                    # Elitarni (juz zloci, 5x kasy) dostaja tylko obrazenia - bez extra zlota.
                    if not hit_enemy.elite:
                        hit_enemy.apply_golden()
                        hit_enemy._gold_marked = True
                    dmg = proj.damage * hit_enemy.get_damage_mult(proj.damage_type)
                    hit_enemy.hit(dmg)
                    self.damage_numbers.append([hit_enemy.x, hit_enemy.y - 40, str(int(dmg)), 30, (255, 215, 0)])
                # Splash damage: obrazenia obszarowe dla Fire/Blaze.
                elif proj.splash_radius > 0:
                    for en in self.enemies:
                        if en.dying or en.dead or en.reached_end:
                            continue
                        if en.hitbox_in_radius(hit_enemy.x, hit_enemy.y, proj.splash_radius):
                            dmg = proj.damage * crit_mult * en.get_damage_mult(proj.damage_type)
                            dmg *= self._tent_damage_mult(en)
                            if en.hit(dmg):
                                tower_sound_3.play()
                            dmg_text = str(int(dmg)) + ("!" if is_crit else "")
                            dmg_color = (255, 220, 50) if is_crit else None
                            self.damage_numbers.append([en.x, en.y - 40, dmg_text, 30, dmg_color])
                            self.stats_damage += int(dmg)
                else:
                    dmg = proj.damage * crit_mult * hit_enemy.get_damage_mult(proj.damage_type)
                    dmg *= self._tent_damage_mult(hit_enemy)
                    if hit_enemy.hit(dmg):
                        tower_sound_3.play()
                    dmg_text = str(int(dmg)) + ("!" if is_crit else "")
                    dmg_color = (255, 220, 50) if is_crit else None
                    self.damage_numbers.append([hit_enemy.x, hit_enemy.y - 40, dmg_text, 30, dmg_color])
                    self.stats_damage += int(dmg)
                # Link Blaze: lancuch na najblizszego INNEGO wroga w 140px
                # od trafionego - 50% obrazen pocisku (zwykle trafienia,
                # nie umiejetnosci specjalne)
                if proj.special is None and getattr(proj.source_tower, '_link', None) == 'blaze':
                    _chain, _chain_d2 = None, 140 ** 2
                    for en in self.enemies:
                        if en is hit_enemy or en.dying or en.dead or en.reached_end:
                            continue
                        _d2 = (en.x - hit_enemy.x) ** 2 + (en.y - hit_enemy.y) ** 2
                        if _d2 < _chain_d2:
                            _chain, _chain_d2 = en, _d2
                    if _chain is not None:
                        _cdmg = max(1, int(proj.damage * 0.5)) * _chain.get_damage_mult(proj.damage_type)
                        _cdmg *= self._tent_damage_mult(_chain)
                        if _chain.hit(_cdmg):
                            tower_sound_3.play()
                        self.damage_numbers.append([_chain.x, _chain.y - 40, str(int(_cdmg)), 30, (255, 170, 80)])
                        self.stats_damage += int(_cdmg)
                        self.particles.burst(_chain.x, _chain.y - 30, (255, 150, 60), count=6, speed=3, size=3)
                # Slow: MetalTower spowalnia trafionych.
                # Link Metal: spowolnienie trzyma duzo dluzej (240 zamiast 90).
                if proj.slow_on_hit:
                    _slow_dur = 240 if getattr(proj.source_tower, '_link', None) == 'metal' else 90
                    hit_enemy.apply_slow(_slow_dur)
            if proj.done:
                self.projectiles.remove(proj)
        # Aktualizacja latajacych liczb obrazen
        for dn in self.damage_numbers[:]:
            dn[1] -= 1  # w gore
            dn[3] -= 1  # timer
            if dn[3] <= 0:
                self.damage_numbers.remove(dn)

    def _draw_victory_map(self):
        """Victory #5: ekran jak stara mapa piratow - 'ISLAND SECURED'."""
        w, h = self.width, self.height
        # Pergamin
        self.win.fill((196, 164, 120))
        # Przyciemnione krawedzie (winieta)
        for i in range(60):
            alpha = int(120 * (i / 60) ** 2)
            edge = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(edge, (101, 67, 33, alpha), (i, i, w - 2*i, h - 2*i), 2)
            self.win.blit(edge, (0, 0))
        # Podwojna ramka mapy
        pygame.draw.rect(self.win, (101, 67, 33), (24, 24, w - 48, h - 48), 4)
        pygame.draw.rect(self.win, (101, 67, 33), (36, 36, w - 72, h - 72), 2)
        # Roza wiatrow (prawy gorny rog)
        cx, cy, r = w - 120, 120, 44
        for ang in range(0, 360, 45):
            rad = math.radians(ang)
            x2, y2 = cx + r * math.cos(rad), cy + r * math.sin(rad)
            col = (140, 40, 40) if ang % 90 == 0 else (101, 67, 33)
            pygame.draw.line(self.win, col, (cx, cy), (x2, y2), 3 if ang % 90 == 0 else 2)
        pygame.draw.circle(self.win, (101, 67, 33), (cx, cy), 6)
        n_lbl = self.font_btn18.render("N", True, (140, 40, 40))
        self.win.blit(n_lbl, (cx - n_lbl.get_width()//2, cy - r - 24))
        # Przerywana sciezka do X (po lewej stronie, nie zachodzi na statystyki)
        path_pts = [(140, h - 160), (300, h - 220), (450, h - 180),
                    (600, h - 260), (w - 260, h//2 + 60)]
        for i in range(len(path_pts) - 1):
            x1, y1 = path_pts[i]
            x2, y2 = path_pts[i + 1]
            segs = 12
            for s in range(0, segs, 2):
                t1, t2 = s / segs, (s + 1) / segs
                px1, py1 = x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1
                px2, py2 = x1 + (x2 - x1) * t2, y1 + (y2 - y1) * t2
                pygame.draw.line(self.win, (101, 67, 33), (px1, py1), (px2, py2), 3)
        # Wielki czerwony X na wyspie (z boku, poza statystyki)
        ix, iy, s = w - 260, h // 2 + 60, 46
        pygame.draw.line(self.win, (170, 30, 30), (ix - s, iy - s), (ix + s, iy + s), 10)
        pygame.draw.line(self.win, (170, 30, 30), (ix - s, iy + s), (ix + s, iy - s), 10)
        # Morskie bazgroly w rogach
        for sx, sy in [(100, 140), (w - 220, h - 140)]:
            pygame.draw.arc(self.win, (101, 67, 33), (sx - 30, sy - 14, 60, 28), 0.3, 2.8, 2)
            pygame.draw.arc(self.win, (101, 67, 33), (sx - 20, sy - 8, 40, 18), 0.3, 2.8, 2)

    def _draw_defeat_minimal(self):
        """Defeat #10: minimalistyczny ciemny ekran - tylko statystyki i motywujacy napis."""
        w, h = self.width, self.height
        # Bardzo ciemne tlo z delikatna winieta
        self.win.fill((12, 14, 18))
        for i in range(50):
            alpha = int(80 * (i / 50) ** 2)
            edge = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(edge, (0, 0, 0, alpha), (i, i, w - 2*i, h - 2*i), 2)
            self.win.blit(edge, (0, 0))
        # Cienka linia pod tytulem (tytul jest na h//2 - 160)
        pygame.draw.line(self.win, (80, 30, 30), (w//2 - 200, h//2 - 70), (w//2 + 200, h//2 - 70), 2)

    def _end_stats_list(self):
        """Rozszerzone statystyki koncowe: ogolne + zabicia wg typu wroga."""
        lines = [
            f"Wave reached: {self.wave + 1} / {len(waves)}",
            f"Monsters slain: {self.stats_kills}",
            f"Damage dealt: {int(round(self.stats_damage))}",
            f"Gold earned: {self.stats_gold}   |   Gold spent: {self.stats_gold_spent}",
            f"Towers built: {self.stats_towers_built}   |   Towers lost: {self.stats_towers_lost}",
            f"Abilities used: {self.stats_abilities_used}",
        ]
        # Zabicia wg typu (top 5)
        by_type = sorted(self.stats_kills_by_type.items(), key=lambda kv: -kv[1])[:5]
        if by_type:
            lines.append("")
            lines.append("Kills by type:")
            for etype, count in by_type:
                # Ladna nazwa: EvilVillager -> Evil Villager
                nice = "".join(" " + c if c.isupper() and i else c
                               for i, c in enumerate(etype)).strip()
                lines.append(f"  {nice}: {count}")
        return lines

    def _draw_glass_button(self, rect, label_text, glow_color, hover=False, font=None):
        """Szklany przycisk (glassmorphism): poswiata, matowe szklo, jasna krawedz, blysk u gory."""
        win = self.win
        # Tekst MUSI miescic sie w przycisku: kurcz czcionke (30/26/22/18) az wejdzie
        # (wczesniej ENDLESS MODE przy 30px byl szerszy niz przycisk 170px i wylewal sie poza)
        _cands = [font or self.font_small30, self.font_small26, self.font_small22, self.font_small18]
        font = _cands[0]
        for _f in _cands:
            if _f.size(label_text)[0] <= rect.w - 16 and _f.size(label_text)[1] <= rect.h - 10:
                font = _f
                break
        # Miekka poswiata za przyciskiem (kilka warstw = przyblizony blur)
        # Pady mniejsze (14/9/4 zamiast 22/14/7): przy gap 28 poswiaty sie tylko stykaja, nie zlewaja
        for pad, alpha in ((14, 18), (9, 30), (4, 45)):
            glow = pygame.Surface((rect.w + pad * 2, rect.h + pad * 2), pygame.SRCALPHA)
            a = alpha + (20 if hover else 0)
            pygame.draw.rect(glow, (*glow_color, a), glow.get_rect(), border_radius=18)
            win.blit(glow, (rect.x - pad, rect.y - pad))
        # Matowe szklo
        glass = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(glass, (235, 240, 250, 95 if not hover else 125),
                         glass.get_rect(), border_radius=14)
        # Kolorowy tint
        tint = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        tint.fill((*glow_color, 50 if not hover else 70))
        glass.blit(tint, (0, 0))
        win.blit(glass, rect.topleft)
        # Jasna krawedz
        pygame.draw.rect(win, (255, 255, 255, 170), rect, 2, border_radius=14)
        # Blysk u gory szkla
        hl = pygame.Surface((rect.w - 20, rect.h // 3), pygame.SRCALPHA)
        pygame.draw.rect(hl, (255, 255, 255, 45), hl.get_rect(), border_radius=9)
        win.blit(hl, (rect.x + 10, rect.y + 7))
        # Tekst z cieniem
        label = font.render(label_text, True, (255, 255, 255))
        tsh = font.render(label_text, True, (0, 0, 0))
        lx = rect.x + rect.width // 2 - label.get_width() // 2
        ly = rect.y + rect.height // 2 - label.get_height() // 2
        win.blit(tsh, (lx + 2, ly + 2))
        win.blit(label, (lx, ly))

    def show_end_screen(self, won, forfeited=False):
        # Monety w locie: dolicz od razu, zeby statystyki koncowe byly pelne
        for c in list(getattr(self, "coins", [])):
            amt = getattr(c, "amount", 0) or 0
            if amt:
                self.money += amt
                self.stats_gold += amt
                self._ach_stats["gold_earned"] = self._ach_stats.get("gold_earned", 0) + amt
                self._ach_stats["max_gold_held"] = max(self._ach_stats.get("max_gold_held", 0), self.money)
        self.coins = []
        self.display_money = self.money
        # Achievements: wygrana / perfekcyjna / comeback (raz na wygrana)
        if won and not forfeited and not getattr(self, "_win_recorded", False):
            self._win_recorded = True
            self._ach_stats["wins"] = self._ach_stats.get("wins", 0) + 1
            if self.lives == self._start_lives:
                self._ach_stats["perfect_wins"] = self._ach_stats.get("perfect_wins", 0) + 1
            if self.lives == 1:
                self._ach_stats["comeback_wins"] = self._ach_stats.get("comeback_wins", 0) + 1
        """Ekran koncowy. Zwraca 'restart', 'continue' (endless), 'menu' lub 'quit'."""
        big_font = self.font_big70
        small_font = self.font_small30
        if forfeited:
            title = tr("end.forfeited")
            color = (255, 180, 80)
            title_bg = None
        elif won:
            title = tr("end.secured")
            color = (101, 45, 20)  # ciemny braz na pergaminie
            title_bg = None
        else:
            title = tr("end.lost")
            color = (150, 60, 60)  # przygaszona czerwien na ciemnym tle
            title_bg = None
        # Przyciski - szersze + wiekszy odstep (wczesniej 170x52, gap 20: ciasno + ENDLESS MODE wylewal sie)
        bw, bh = 210, 56
        by = self.height // 2 + 200
        gap = 28
        if won and not forfeited:
            total = 4 * bw + 3 * gap
            x0 = self.width // 2 - total // 2
            restart_rect = pygame.Rect(x0, by, bw, bh)
            continue_rect = pygame.Rect(x0 + (bw + gap), by, bw, bh)
            menu_rect = pygame.Rect(x0 + 2 * (bw + gap), by, bw, bh)
            quit_rect = pygame.Rect(x0 + 3 * (bw + gap), by, bw, bh)
        else:
            total = 3 * bw + 2 * gap
            x0 = self.width // 2 - total // 2
            restart_rect = pygame.Rect(x0, by, bw, bh)
            menu_rect = pygame.Rect(x0 + (bw + gap), by, bw, bh)
            quit_rect = pygame.Rect(x0 + 2 * (bw + gap), by, bw, bh)
            continue_rect = None
        # Tlo: mapa skarbow (win) / minimalistyczna porazka (lose) / ciemne (forfeit)
        is_defeat = not won and not forfeited
        if won and not forfeited:
            self._draw_victory_map()
            stat_color = (80, 50, 25)
            sub_color = (101, 67, 33)
        elif is_defeat:
            self._draw_defeat_minimal()
            stat_color = (160, 170, 185)
            sub_color = (120, 130, 145)
        else:
            self.win.blit(self.bg, (0, 0))
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            self.win.blit(overlay, (0, 0))
            stat_color = (200, 200, 200)
            sub_color = (255, 255, 255)
        text = big_font.render(title, 1, color)
        # Cien pod tytulem dla czytelnosci
        shadow = big_font.render(title, 1, (0, 0, 0))
        tx = self.width // 2 - text.get_width() // 2
        ty = self.height // 2 - 160
        self.win.blit(shadow, (tx + 3, ty + 3))
        self.win.blit(text, (tx, ty))
        stats_font = self.font_stats24
        def _draw_static():
            # Tlo
            if won and not forfeited:
                self._draw_victory_map()
            elif is_defeat:
                self._draw_defeat_minimal()
            else:
                self.win.blit(self.bg, (0, 0))
                ov = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                ov.fill((0, 0, 0, 170))
                self.win.blit(ov, (0, 0))
            # Tytul
            self.win.blit(shadow, (tx + 3, ty + 3))
            self.win.blit(text, (tx, ty))
            # Statystyki: PELNY zestaw na KAZDYM ekranie koncowym (wygrana,
            # porazka i poddanie) - wczesniej poddanie/wygrana mialy tylko
            # 3 linijki. Dwie kolumny: ogolne (lewa) + zabicia wg typu (prawa).
            col_y = self.height // 2 - 60
            left_x = self.width // 2 - 330
            right_x = self.width // 2 + 30
            if self.endless:
                wave_line = tr("end.wave_endless", a=self.wave + 1)
            else:
                wave_line = tr("end.wave_reached", a=self.wave + 1, b=len(waves))
            general = [
                wave_line,
                tr("end.monsters", n=self.stats_kills),
                tr("end.damage", n=int(round(self.stats_damage))),
                tr("end.gold_earned", n=self.stats_gold),
                tr("end.gold_spent", n=self.stats_gold_spent),
                tr("end.towers", a=self.stats_towers_built, b=self.stats_towers_lost),
                tr("end.abilities", n=self.stats_abilities_used),
            ]
            for i, s in enumerate(general):
                label = stats_font.render(s, True, stat_color)
                self.win.blit(label, (left_x, col_y + i * 28))
            by_type = sorted(self.stats_kills_by_type.items(), key=lambda kv: -kv[1])[:7]
            if by_type:
                hdr = stats_font.render(tr("end.kills_by_type"), True, sub_color)
                self.win.blit(hdr, (right_x, col_y))
                for i, (etype, count) in enumerate(by_type):
                    nice = "".join(" " + c if c.isupper() and j else c
                                   for j, c in enumerate(etype)).strip()
                    label = stats_font.render(f"{nice}: {count}", True, stat_color)
                    self.win.blit(label, (right_x, col_y + (i + 1) * 28))
            if is_defeat:
                motto = small_font.render(tr("end.motto"), True, (100, 110, 125))
                self.win.blit(motto, (self.width // 2 - motto.get_width() // 2, col_y + 8 * 28))
        _draw_static()
        # Przyciski - szklane (glassmorphism), z hover w petli
        buttons = [
            (restart_rect, tr("end.restart"), (80, 220, 130)),
            (menu_rect, tr("end.main_menu"), (90, 160, 255)),
            (quit_rect, tr("end.quit"), (255, 100, 100)),
        ]
        if continue_rect:
            buttons.insert(1, (continue_rect, tr("end.endless"), (255, 180, 50)))
        def _draw_buttons(hover_pos=None):
            for rect, label_text, glow_color in buttons:
                hov = hover_pos is not None and rect.collidepoint(hover_pos)
                self._draw_glass_button(rect, label_text, glow_color, hover=hov,
                                        font=small_font)
        _draw_buttons()
        self._present()
        # Petla czeka na klikniecie przycisku
        waiting = True
        mouse = self._mouse_pos()
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.MOUSEMOTION:
                    mouse = self._mouse_pos()
                    _draw_static()
                    _draw_buttons(mouse)
                    self._present()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = self._mouse_pos()
                    if restart_rect.collidepoint(pos):
                        return "restart"
                    if quit_rect.collidepoint(pos):
                        return "quit"
                    if menu_rect.collidepoint(pos):
                        return "menu"
                    if continue_rect and continue_rect.collidepoint(pos):
                        return "continue"
        return "quit"
        
    def draw(self):
        self._frame += 1
        # Jeden odczyt czasu na klatke (wydajnosc) - uzywany w calej klatce
        self._now = pygame.time.get_ticks()
        self._now_s = self._now / 1000.0
        # Zegar animacji stoi na pauzie (patrz __init__): chmury, woda,
        # tancerze, statki i reszta animacji rysowanych nie porusza sie,
        # gdy gra jest zapauzowana.
        if self._anim_last is None:
            self._anim_last = self._now
        if not self.paused:
            self._anim_s += (self._now - self._anim_last) / 1000.0
        self._anim_last = self._now
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
            if getattr(tw, "_link", None):
                for tw2 in self.towers:
                    if tw2 is not tw and type(tw2).__name__ == type(tw).__name__:
                        _dx, _dy = tw2.x - tw.x, tw2.y - tw.y
                        if _dx*_dx + _dy*_dy < 10000:
                            key = tuple(sorted([id(tw), id(tw2)]))
                            if key not in drawn_links:
                                drawn_links.add(key)
                                pygame.draw.line(self.win, (255, 215, 0, 120),
                                               (tw.x, tw.y - 20), (tw2.x, tw2.y - 20), 2)
        # Ognisko z tanczacymi PRZED wiezami - wieze zawsze widoczne nad animacja
        self.draw_campfire()
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
            # Tint modelu na zielono/czerwono wg poprawnosci miejsca (zamiast kolka)
            self.moving_object._placement_valid = self.is_valid_placement(
                self.moving_object.x, self.moving_object.y)
            self.moving_object.draw(self.win)
            # Kolo podgladu: ten sam efektywny zasieg co po postawieniu
            self.moving_object._rain_mod = 0.9 if self.raining else 1.0
            self.moving_object.draw_radius(self.win)
            self.moving_object._placement_valid = None
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
            mx, my = self._mouse_pos()
            for en in self.enemies:
                if en.dying or en.dead or en.reached_end:
                    continue
                if en.get_hitbox().collidepoint(mx, my):
                    self._hover_enemy = en
                    break
        if self._hover_enemy is not None:
            en = self._hover_enemy
            hlabel = self.font_e14.render(tr("hud.hp", hp=int(en.health), max=en.max_health), True, (255, 180, 180))
            self.win.blit(hlabel, (en.x - hlabel.get_width()//2, en.y - 95))
        # Q9: podswietl wrogow w zasiegu wybranej wiezy - usuniete na prosbe gracza
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
        # Statek na wierzchu wrogow (nie wyglada dziwnie przy nachodzeniu)
        self.ship.draw(self.win, self._anim_s)
        # Okaleczony pirat: dym i ogien
        if self.pirate_crippled and self.ship.state != Ship.AWAY:
            if random.random() < 0.3:
                self.particles.burst(self.ship.x + random.randint(-40, 40),
                                     self.ship.y - 40 + random.randint(-20, 20),
                                     (80, 80, 80), count=2, speed=1, life=40, size=5, gravity=-0.05)
            if random.random() < 0.15:
                self.particles.burst(self.ship.x + random.randint(-30, 30),
                                     self.ship.y - 30,
                                     (255, 120, 30), count=2, speed=2, life=25, size=4)
        # Sojuszniczy statek
        if self.ally_ship:
            self.ally_ship.draw(self.win, self._anim_s)
        self._draw_cannonballs()
        self._draw_mortars()
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
                # Nazwa bossa (bez emoji - brak glyfu w czcionce)
                boss_font = self.font_boss16
                skull = tr("boss.name") if not getattr(en, 'final', False) else tr("boss.final")
                if getattr(en, 'enraged', False):
                    skull += tr("boss.enraged")
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
        # (gdy statek odplynal ale wrogowie jeszcze sa na mapie, lub awaryjnie gdy fala utknela)
        if self.waiting_for_clear and not self.won and not self.last_wave_done and (not self.bombard_active or self.bombard_phase == 12):
            btn_w, btn_h = 240, 56
            bx = self.width - btn_w - 20
            # Na samej gorze (y=10) - wczesniej na y=70 nachodzil na popup
            # achievementow (y 90-170).
            by = 10
            self.early_wave_rect = pygame.Rect(bx, by, btn_w, btn_h)
            # Bonus zalezy od liczby pozostalych wrogow
            bonus = len(self.enemies) * 5
            btn_bg = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
            pygame.draw.rect(btn_bg, (30, 90, 50, 230), btn_bg.get_rect(), border_radius=12)
            pygame.draw.rect(btn_bg, (100, 255, 150, 180), btn_bg.get_rect(), 2, border_radius=12)
            self.win.blit(btn_bg, (bx, by))
            btn_font = self.font_btn18
            # Wytlumaczenie: co robi przycisk + ile zlota za skip
            line1 = btn_font.render(tr("hud.skip"), True, (200, 255, 210))
            line2 = btn_font.render(tr("hud.skip_bonus", bonus=bonus), True, (255, 215, 100))
            self.win.blit(line1, (bx + btn_w//2 - line1.get_width()//2, by + 6))
            self.win.blit(line2, (bx + btn_w//2 - line2.get_width()//2, by + 28))
        else:
            self.early_wave_rect = None
        
        # Ability dock - pasek umiejetnosci na dole
        self.draw_ability_dock()

        # Podswietlenie klikalnego budynku + dron + menu upgradow
        # Dron PO tent_visuals (Cewka Tesli), zeby nie byl przez nia przycinany
        self.draw_building_highlight()
        self.draw_tent_highlight()
        self.draw_tent_visuals()
        self.draw_repair_drone()
        self.draw_facility()
        self.draw_combat_drone()
        self.draw_tesla_bolts()
        self.draw_building_menu()
        self.draw_tent_menu()
        self.draw_achievement_popup()

        # Przyciemnienie przy wejsciu bossa (dramatyczny efekt)
        if self.boss_intro_dark > 0:
            alpha = int(120 * (self.boss_intro_dark / 180))
            dark = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            dark.fill((0, 0, 0, alpha))
            self.win.blit(dark, (0, 0))
        
        # U9: podglad zasiegu wiezy ze sklepu (hover)
        # Q12: porownanie DPS
        if not self.moving_object:
            pos = self._mouse_pos()
            hovered = self.menu.get_hovered(pos[0], pos[1])
            if hovered:
                tmp = {"t1": WoodenTower, "t2": MetalTower, "t3": GoldenTower,
                       "t4": FireTower, "t5": BlazeTower}.get(hovered)
                if tmp:
                    tw = tmp(pos[0], pos[1])
                    tw._rain_mod = 0.9 if self.raining else 1.0
                    tw.draw_radius(self.win)
                    # Q12: DPS vs srednia
                    avg = sum(t.damage for t in self.towers) / max(1, len(self.towers))
                    diff = tw.damage - avg
                    cfont = self.font_c13
                    ctxt = tr("hud.dps_avg", dmg=tw.damage, diff=f"{'+' if diff >= 0 else ''}{diff:.0f}")
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
        # A4: chmury (wolno, pozycja bazowa + przesuniecie czasowe).
        # NIE rysujemy przy otwartym menu upgradów budynku/namiotu: chmury sa
        # rysowane PO menu (draw() wywoluje menu przed chmurami), wiec lecialy
        # po wierzchu panelu i zaslanialy widok.
        # UWAGA: t = _now_s MUSI zostac poza ifem - uzywaja go tez mewy/liscie ponizej.
        t = self._anim_s
        if not (self._building_menu_open or self._tent_menu_open):
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
        # Pochodnie przy zamku - usuniete na prosbe gracza

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
        # Slady stop bossa - usuniete na prosbe gracza
        # (Ognisko przeniesione przed wieze - wieze zawsze nad animacja tanczacych)
        self.draw_chests()
        self.draw_announcements()
        # Q17: zegar sesji
        mins = self.game_time // 3600
        secs = (self.game_time // 60) % 60
        qfont = self.font_q14
        tlabel = qfont.render(f"{mins:02d}:{secs:02d}", True, (200, 200, 200))
        self.win.blit(tlabel, (self.width - 70, self.height - 30))
        
        # 8: wskaznik pauzy z informacja o budowaniu - tylko dla pauzy bez
        # menu ESC; z menu widoczna jest jedna PAUSED (ta z menu)
        if self.paused and not self.show_menu:
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
            self.wave_banner_text = tr("banner.warning")
            self.wave_banner_timer = 150
            sound_horn.play()  # Niespodzianka 5: rog ostrzegawczy
        if not self.waiting_for_clear:
            self._boss_warned = False
        
        discount = 0.85 if "supply" in self.tent_upgrades else 1.0
        # Sklep: DMG na zywo (nie statyczny z init) - bazowe x Honor Banner.
        # Wczesniej sklep pokazywal stare 8/10 dla Fire/Blaze mimo rebalansu
        # (9/12) i nie uwzglednial Bannera.
        _dmgm = 1.1 if "banner" in self.tent_upgrades else 1.0
        for _btn, _cls in zip(self.menu.buttons,
                              (WoodenTower, MetalTower, GoldenTower, FireTower, BlazeTower)):
            _btn.damage = math.ceil(_cls.base_damage * _dmgm)
        self.menu.draw(self.win, self._mouse_pos(), discount=discount)
        self.draw_hud()
        # Cinematic bombardowania - zoom na wieze
        self._draw_bombard_zoom()
        # Menu wybranej wiezy NA SAMYM KONCU - nad wrogami, pociskami, HUDem, wszystkim
        if self.selected_tower is not None and self.selected_tower in self.towers:
            discount = 0.85 if "supply" in self.tent_upgrades else 1.0
            self.selected_tower.menu.draw(self.win, self.money, discount=discount,
                                           sell_rate=self._diff("sell_mult"))
        # Menu wybranego klastra kolcow - tak samo na wierzchu
        if self.selected_spike is not None and self.selected_spike in self._spikes:
            self.selected_spike.menu.draw(self.win, self.money, discount=1.0,
                                           sell_rate=self._diff("sell_mult"))
            # Podswietlenie wybranego klastra (okrag, jak zasieg wiezy)
            pygame.draw.circle(self.win, (255, 200, 80),
                               (int(self.selected_spike.x), int(self.selected_spike.y)), 34, 2)

        # Menu ESC rysowane OSTATNIE - pauza ma priorytet na ekranie nad
        # menu wiezy i kolcow (wczesniej menu kolcow wchodzilo na pauze)
        if self.show_menu:
            self.draw_pause_menu()

        self._present()

    def _draw_bombard_zoom(self):
        """Subtelne oznaczenie celu podczas bombardowania."""
        # Wylaczone na prosbe gracza - kule po prostu leca ze statku
        return

    def _set_music_muted(self, on):
        """Muzyka = TYLKO mixer music (zwykla + bossa/intense). SFX nietkniete.
        Muzyka bossa to sciezka music_intense.wav przez mixer music, wiec
        pauza mixer music wycisza i muzyke, i muzyke bossa."""
        self.music_muted = on
        if on:
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()

    def _set_sfx_muted(self, on):
        """SFX = WSZYSTKIE dzwieki poza muzyka (strzaly, umiejetnosci, wieze,
        deszcz, minigun, rakiety - z ich bazowymi glosnosciami przy wlaczeniu)."""
        self.sfx_muted = on
        vol = 0 if on else 1
        for s in (sound_1, sound_2, sound_3, sound_4, sound_5, sound_glass,
                  sound_ab_rapid, sound_ab_frost, sound_ab_gold, sound_ab_meteor, sound_ab_arma,
                  sound_win, sound_lose, sound_roar,
                  sound_levelup, sound_horn, sound_gull, sound_fanfare,
                  tower_sound_1, tower_sound_2, tower_sound_3, tower_sound_4, tower_sound_5,
                  *shoot_sounds.values()):
            s.set_volume(vol)
        # Bazowe glosnosci (ciszej niz reszta - nie 1.0)
        sound_rain.set_volume(0 if on else 0.35)
        sound_minigun.set_volume(0 if on else 0.35)
        sound_rocket.set_volume(0 if on else 0.5)
        sound_rocket_boom.set_volume(0 if on else 0.6)

    def _menu_action(self, action):
        """Akcje przyciskow menu ESC."""
        if action == "resume":
            self.show_menu = False
            self.paused = False
        elif action == "restart":
            self.show_menu = False
            self.reset_game()
        elif action == "forfeit":
            # Rezygnacja: zamknij menu, pokaz podsumowanie ze statystykami
            self.show_menu = False
            self.paused = False
            self._forfeit = True
        elif action == "help":
            self._show_help = True
        elif action == "music":
            self._set_music_muted(not self.music_muted)
        elif action == "sfx":
            self._set_sfx_muted(not self.sfx_muted)
        elif action == "fullscreen":
            self._fullscreen = not self._fullscreen
            if self._fullscreen:
                self._screen = pygame.display.set_mode(
                    (self._native_w, self._native_h), pygame.FULLSCREEN)
            else:
                self._screen = pygame.display.set_mode((self._native_w, self._native_h))
            self._native_w, self._native_h = self._screen.get_size()
        elif action == "speed":
            self.speed = {1: 2, 2: 3, 3: 1}[self.speed]
        elif action == "quit":
            pygame.quit()
            raise SystemExit

    def draw_pause_menu(self):
        """Menu pauzy (ESC): wznow, restart, pomoc, dzwiek, fullscreen, predkosc, rezygnacja, wyjscie."""
        # Przyciemnienie tla
        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 140))
        self.win.blit(dim, (0, 0))
        # Panel: wysokosc DOKLADNIE na miare przyciskow (wczesniej stale 520,
        # a 9 przyciskow potrzebuje 562 - Quit wystawal 26px poza panel).
        _items = [
            (tr("pause.resume"), "resume"),
            (tr("pause.restart"), "restart"),
            (tr("pause.forfeit"), "forfeit"),
            (tr("pause.help"), "help"),
            (tr("pause.music"), "music", not self.music_muted),
            (tr("pause.sfx"), "sfx", not self.sfx_muted),
            (tr("pause.fullscreen", state=tr("common.on") if self._fullscreen else tr("common.off")), "fullscreen"),
            (tr("pause.speed", n=self.speed), "speed"),
            (tr("pause.quit"), "quit"),
        ]
        pw = 340
        ph = 70 + (len(_items) - 1) * 54 + 44 + 16 + 78  # tytul + przyciski 44px co 54px + wiersz skoku do fali + margines
        px, py = (self.width - pw) // 2, (self.height - ph) // 2
        pygame.draw.rect(self.win, (25, 30, 38), (px, py, pw, ph), border_radius=16)
        pygame.draw.rect(self.win, (70, 80, 95), (px, py, pw, ph), 2, border_radius=16)
        title = self.font_p36.render(tr("hud.paused"), True, (255, 255, 255))
        self.win.blit(title, (px + (pw - title.get_width()) // 2, py + 22))
        # Przyciski
        self._menu_buttons = []
        mx, my = self._mouse_pos()
        items = _items
        by = py + 70
        for item in items:
            if len(item) == 3:
                label, action, checked = item
                has_check = True
            else:
                label, action = item
                has_check = False
                checked = False
            rect = pygame.Rect(px + 40, by, pw - 80, 44)
            hover = rect.collidepoint(mx, my)
            col = (55, 65, 80) if not hover else (75, 90, 110)
            pygame.draw.rect(self.win, col, rect, border_radius=10)
            if action == "quit":
                pygame.draw.rect(self.win, (120, 50, 50), rect, 2, border_radius=10)
            if has_check:
                # Checkmark box
                cb = pygame.Rect(rect.x + 16, rect.y + 12, 20, 20)
                pygame.draw.rect(self.win, (30, 35, 45), cb, border_radius=4)
                pygame.draw.rect(self.win, (120, 130, 145), cb, 2, border_radius=4)
                if checked:
                    # Zielony ptaszek
                    pygame.draw.line(self.win, (80, 220, 100), (cb.x + 4, cb.y + 10), (cb.x + 9, cb.y + 15), 3)
                    pygame.draw.line(self.win, (80, 220, 100), (cb.x + 9, cb.y + 15), (cb.x + 16, cb.y + 5), 3)
                txt = self.font_btn18.render(label, True, (240, 240, 240))
                self.win.blit(txt, (cb.x + 28, rect.y + (rect.h - txt.get_height()) // 2))
            else:
                txt = self.font_btn18.render(label, True, (240, 240, 240))
                self.win.blit(txt, (rect.x + (rect.w - txt.get_width()) // 2,
                                    rect.y + (rect.h - txt.get_height()) // 2))
            self._menu_buttons.append((rect, action))
            by += 54
        # Wiersz skoku do fali endless (jak w menu glownym): etykieta, pole
        # z numerem fali i przycisk SKOCZ. Skok czysci plansze i zachowuje
        # setup; skoczona fala nie placi bonusu startowego.
        jy = by + 6
        lbl = self.font_btn18.render(tr("menu.endless_title"), True, (255, 215, 100))
        self.win.blit(lbl, (px + 40, jy))
        self._pause_jump_input = pygame.Rect(px + 40, jy + 26, 120, 38)
        self._pause_jump_btn = pygame.Rect(px + 168, jy + 26, pw - 208, 38)
        r = self._pause_jump_input
        pygame.draw.rect(self.win, (10, 16, 28), r, border_radius=8)
        pygame.draw.rect(self.win, (255, 215, 100) if self._pause_wave_focus else (120, 135, 155),
                         r, 2, border_radius=8)
        txt = self._pause_wave_txt if self._pause_wave_txt else str(self.wave + 1)
        col = (240, 244, 248) if self._pause_wave_txt else (110, 120, 135)
        tv = self.font_btn18.render(txt, True, col)
        self.win.blit(tv, (r.x + 10, r.y + r.h // 2 - tv.get_height() // 2))
        if self._pause_wave_focus and (pygame.time.get_ticks() // 500) % 2 == 0:
            cx = r.x + 10 + tv.get_width() + 3
            pygame.draw.line(self.win, (255, 215, 100), (cx, r.y + 8), (cx, r.bottom - 8), 2)
        jb = self._pause_jump_btn
        pygame.draw.rect(self.win, (75, 90, 110) if jb.collidepoint(mx, my) else (55, 65, 80),
                         jb, border_radius=10)
        jt = self.font_btn18.render(tr("menu.endless_go"), True, (240, 240, 240))
        self.win.blit(jt, (jb.x + (jb.w - jt.get_width()) // 2,
                           jb.y + (jb.h - jt.get_height()) // 2))
        # Pod-ekran pomocy
        if self._show_help:
            self.draw_help_overlay()

    def draw_help_overlay(self):
        hw, hh = 560, 440
        hx, hy = (self.width - hw) // 2, (self.height - hh) // 2
        pygame.draw.rect(self.win, (20, 25, 32), (hx, hy, hw, hh), border_radius=16)
        pygame.draw.rect(self.win, (70, 80, 95), (hx, hy, hw, hh), 2, border_radius=16)
        title = self.font_p36.render(tr("menu.help"), True, (255, 215, 100))
        self.win.blit(title, (hx + (hw - title.get_width()) // 2, hy + 20))
        lines = [
            tr("help.l1"),
            tr("help.l2"),
            tr("help.l3"),
            "",
            tr("help.l4"),
            tr("help.l5"),
            tr("help.l6"),
            tr("help.l7"),
            tr("help.l8"),
            "",
            tr("help.esc"),
        ]
        y = hy + 70
        for ln in lines:
            t = self.font_btn18.render(ln, True, (220, 220, 220))
            self.win.blit(t, (hx + 30, y))
            y += 28

    def _present(self):
        """Wyswietla bufor 1124x720 w natywnej rozdzielczosci (smoothscale HQ)."""
        _sw, _sh = self._screen.get_size()
        if self._fullscreen:
            pygame.transform.smoothscale(self.win, (_sw, _sh), self._screen)
        else:
            # Okno 1:1 - bez skalowania, wycentrowane
            self._screen.fill((0, 0, 0))
            ox = (_sw - self.width) // 2
            oy = (_sh - self.height) // 2
            self._screen.blit(self.win, (ox, oy))
        pygame.display.flip()

    def _to_game_pos(self, pos):
        """Przelicza wspolrzedne ekranu (natywne) na wspolrzedne gry (1124x720)."""
        if self._fullscreen:
            sx = self._native_w / self.width
            sy = self._native_h / self.height
            return (pos[0] / sx, pos[1] / sy)
        else:
            ox = (self._native_w - self.width) // 2
            oy = (self._native_h - self.height) // 2
            return (pos[0] - ox, pos[1] - oy)

    def _mouse_pos(self):
        """Pozycja myszy w wspolrzednych gry."""
        return self._to_game_pos(pygame.mouse.get_pos())

    def draw_castle_damage(self):
        """1: Wizualne uszkodzenia zamku zaleza od liczby zyc."""
        cx, cy = 300, 375  # koniec sciezki (baza)
        t = self._anim_s
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
        # Banner ponizej paska Enemies (konczy sie na y=127) - wczesniej na
        # y=95 wchodzil na licznik wrogow.
        self.win.blit(s, (self.width // 2 - bg_w // 2, 140))

    def draw_ambient_life(self):
        """11-20, 22-25: zycie na wyspie (animacje 30Hz - pozycje co 2. klatke)."""
        if self._frame % 2 == 0:
            self._ambient_t = self._anim_s
        t = self._ambient_t
        phase = (self.wave // 2) % 4
        night = (phase == 2)

        # 11: wodospad - usuniety na prosbe gracza

        # 13: usuniety wulkan na horyzoncie (na prosbe gracza)

        # 14: balon - REMOVED: single Recon Balloon in draw_tent_visuals now handles it
        # (Previously this ambient balloon + the upgrade balloon = two balloons at once.)

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
            # Wynurzenie TYLKO poza pomostem (pomost: x 240-580) - ciemne
            # cielsko na tle desek wygladalo jak przeciecie grafiki pomostu
            _wx = random.randint(90, 180) if random.random() < 0.3 else random.randint(650, 1000)
            self.whale = [_wx, 0]
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
        _px0, _py0, _pw, _ph = _PIER_RECT
        for cr in self.crabs:
            cr[2] += 0.05 * cr[3]
            cr[0] += 0.6 * cr[3]
            if cr[0] > 1050: cr[3] = -1
            if cr[0] < 80: cr[3] = 1
            # Pomost jest NAD woda - krab przechodzi POD nim (nie rysujemy
            # na pomoście; ruch idzie dalej, wiec wylania sie z drugiej strony)
            if _px0 - 15 < cr[0] < _px0 + _pw + 15 and _py0 < cr[1] < _py0 + _ph:
                continue
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
            # Jak wieloryb: poza pomostem (x 240-580), zeby macka nie
            # wyrastala przez deski pomostu
            _ox = random.randint(90, 180) if random.random() < 0.3 else random.randint(650, 1000)
            self.octo = [_ox, 0]
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

        # 23: swiecace grzyby - usuniete na prosbe gracza

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
        t = self._anim_s
        cx, cy = 1041, 410  # moved via drag tool (was 830, 385)
        # Signal Fire: ognisko 2x wieksze
        s = 2.0 if "signal" in self.tent_upgrades else 1.0
        for i in range(8):
            ang = i * math.pi / 4
            pygame.draw.circle(self.win, (120, 120, 120),
                             (int(cx + 18 * s * math.cos(ang)), int(cy + 10 * s * math.sin(ang))), int(6 * s))
        pygame.draw.line(self.win, (101, 67, 33), (cx - 12 * s, cy), (cx + 12 * s, cy - 8 * s), int(4 * s))
        for i, (col, h) in enumerate([((255, 80, 20), 28), ((255, 160, 40), 20), ((255, 230, 120), 12)]):
            fh = (h + 6 * math.sin(t * 12 + i * 2)) * s
            pygame.draw.polygon(self.win, col, [(cx - 10 * s + i*2, cy), (cx, cy - fh), (cx + 10 * s - i*2, cy)])
        if random.random() < 0.3 * s:
            self.particles.burst(cx, cy - 20 * s, (255, 180, 80), count=1, speed=1, life=20, size=2, gravity=-0.12)
        # Tancerze: przy ognisku (normalnie) lub na strazy przy budynku (Signal Fire)
        if "signal" in self.tent_upgrades:
            self.draw_guard_dancers()
        else:
            self.draw_campfire_dancers(cx, cy, t)

    def draw_guard_dancers(self):
        """Guards on duty: hold bows always. Melee weapon only when charging/dueling/returning."""
        t = self._anim_s
        self.draw_tombstones()
        # Widoczne strzaly straznikow (w locie)
        for a in getattr(self, "_guard_arrows", []):
            ax, ay = a["x"], a["y"]
            tx, ty = a.get("tx", ax), a.get("ty", ay)
            ang = math.atan2(ty - ay, tx - ax)
            # Strzala: drzewce + grot w kierunku lotu
            ex = ax + math.cos(ang) * 12
            ey = ay + math.sin(ang) * 12
            pygame.draw.line(self.win, (200, 180, 150), (ax, ay), (ex, ey), 2)
            pygame.draw.polygon(self.win, (220, 220, 220),
                                [(ex, ey),
                                 (ex - math.cos(ang + 2.6) * 6, ey - math.sin(ang + 2.6) * 6),
                                 (ex - math.cos(ang - 2.6) * 6, ey - math.sin(ang - 2.6) * 6)])
        for d in self._dancers:
            if not d["alive"]:
                continue
            dx, dy = d["x"], d["y"]
            mode = d.get("mode", "guard")
            # Deploying: ida do posterunku (bieg, bron biala, twarz w kierunku marszu)
            if mode == "deploying":
                face = d.get("deploy_face", 1)
                run = 6 * math.sin(t * 12)
                pygame.draw.line(self.win, (50, 50, 80), (dx, dy), (dx - 6 + run, dy + 14), 3)
                pygame.draw.line(self.win, (50, 50, 80), (dx, dy), (dx + 6 - run, dy + 14), 3)
                if d["sex"] == "m":
                    pygame.draw.circle(self.win, (255, 200, 170), (int(dx), int(dy - 28)), 8)
                    pygame.draw.line(self.win, (70, 50, 120), (dx, dy - 20), (dx, dy), 4)
                else:
                    pygame.draw.polygon(self.win, (220, 100, 150), [(dx, dy - 20), (dx - 12, dy + 8), (dx + 12, dy + 8)])
                    pygame.draw.circle(self.win, (255, 210, 180), (int(dx), int(dy - 28)), 7)
                hx = dx + face * 18
                hy = dy - 25
                pygame.draw.line(self.win, (101, 67, 33), (dx + face * 5, dy - 15), (hx, hy), 3)
                if d["sex"] == "m":
                    pygame.draw.polygon(self.win, (180, 180, 180), [(hx, hy - 8), (hx + face * 12, hy), (hx, hy + 8)])
                else:
                    pygame.draw.line(self.win, (255, 210, 180), (dx + face * 5, dy - 18), (hx, hy), 3)
                    pygame.draw.circle(self.win, (80, 80, 80), (int(hx), int(hy)), 7)
                continue
            # Face toward target when dueling/charging, else toward nearest enemy, else right
            face = 1
            tgt = d.get("target")
            if mode in ("charging", "dueling") and tgt is not None and not getattr(tgt, "dead", False) and not getattr(tgt, "dying", False):
                face = 1 if tgt.x >= dx else -1
            else:
                best, best_d2 = None, 1e18
                for en in self.enemies:
                    if en.dying or en.dead or en.reached_end:
                        continue
                    d2 = (en.x - dx) ** 2 + (en.y - dy) ** 2
                    if d2 < best_d2:
                        best, best_d2 = en, d2
                if best is not None:
                    face = 1 if best.x >= dx else -1
            # Legs: running when charging/returning, standing otherwise
            if mode in ("charging", "returning"):
                run = 6 * math.sin(t * 12)
                pygame.draw.line(self.win, (50, 50, 80), (dx, dy), (dx - 6 + run, dy + 14), 3)
                pygame.draw.line(self.win, (50, 50, 80), (dx, dy), (dx + 6 - run, dy + 14), 3)
            else:
                pygame.draw.line(self.win, (50, 50, 80), (dx, dy), (dx - 6, dy + 14), 3)
                pygame.draw.line(self.win, (50, 50, 80), (dx, dy), (dx + 6, dy + 14), 3)
            # Body
            if d["sex"] == "m":
                pygame.draw.circle(self.win, (255, 200, 170), (int(dx), int(dy - 28)), 8)
                pygame.draw.line(self.win, (70, 50, 120), (dx, dy - 20), (dx, dy), 4)
            else:
                pygame.draw.polygon(self.win, (220, 100, 150), [(dx, dy - 20), (dx - 12, dy + 8), (dx + 12, dy + 8)])
                pygame.draw.circle(self.win, (255, 210, 180), (int(dx), int(dy - 28)), 7)
            if mode in ("charging", "dueling", "returning"):
                # Melee weapon in hand, blade AWAY from body toward facing dir
                swing = 0
                if mode == "dueling":
                    swing = 6 * math.sin(d.get("swing", 0) * 0.6)
                hx = dx + face * 18
                hy = dy - 25 + swing
                pygame.draw.line(self.win, (101, 67, 33), (dx + face * 5, dy - 15), (hx, hy), 3)
                if d["sex"] == "m":
                    # Axe: blade points AWAY from body (face dir), not back at the guard
                    pygame.draw.polygon(self.win, (180, 180, 180), [(hx, hy - 8), (hx + face * 12, hy), (hx, hy + 8)])
                else:
                    # Frying pan held out toward the enemy
                    pygame.draw.line(self.win, (255, 210, 180), (dx + face * 5, dy - 18), (hx, hy), 3)
                    pygame.draw.circle(self.win, (80, 80, 80), (int(hx), int(hy)), 7)
            else:
                # Bow ALWAYS in hands on guard duty - celuje w najblizszego
                # wroga (jak minigun), domyslnie W DOL, nie w bok. Luk
                # rysowany na osobnej powierzchni i obracany do celu, z
                # animacja naciegu cieciwy przy strzale.
                best = None
                best_d2 = 350 ** 2
                for en in self.enemies:
                    if en.dying or en.dead or en.reached_end:
                        continue
                    d2 = (en.x - dx) ** 2 + (en.y - dy) ** 2
                    if d2 < best_d2:
                        best, best_d2 = en, d2
                if best is not None:
                    aim = math.atan2((best.y - 20) - (dy - 20), best.x - dx)
                else:
                    aim = math.pi / 2  # w dol, jak minigun bez celu
                bow = pygame.Surface((44, 44), pygame.SRCALPHA)
                # Luk: brzuch w strone +x (celu), chwyt w srodku powierzchni
                pygame.draw.arc(bow, (101, 67, 33), (10, 2, 24, 40), -1.2, 1.2, 3)
                just_shot = d.get("cd", 0) > 105
                if just_shot:
                    # Cieciwa naciagnieta + strzala nalozona (animacja strzalu)
                    pygame.draw.line(bow, (240, 240, 240), (26, 3), (32, 22), 1)
                    pygame.draw.line(bow, (240, 240, 240), (32, 22), (26, 41), 1)
                    pygame.draw.line(bow, (200, 180, 150), (32, 22), (42, 22), 2)
                else:
                    pygame.draw.line(bow, (240, 240, 240), (26, 3), (26, 41), 1)
                rot = pygame.transform.rotate(bow, -math.degrees(aim))
                # Chwyt luku (srodek powierzchni) w rece straznika, w strone celu
                hx = dx + math.cos(aim) * 12
                hy = (dy - 20) + math.sin(aim) * 12
                self.win.blit(rot, (hx - rot.get_width() // 2, hy - rot.get_height() // 2))
                # Wolna reka do luku
                pygame.draw.line(self.win, (255, 200, 170) if d["sex"] == "m" else (255, 210, 180), (dx + face * 5, dy - 15), (hx, hy), 2)

    # Tombstone spots (z drag tool, 2026-10-14): Bonnie 22,393 / Clyde 71,393
    _TOMBSTONE_POS = {"Bonnie": (22, 393), "Clyde": (90, 393)}  # Clyde 8px blizej Bonnie (z 98 na 90)

    def _add_tombstone(self, d):
        """Guard dead -> R.I.P. stone at their placed spot. Kills read live from the guard."""
        if not hasattr(self, "_tombstones"):
            self._tombstones = []
        pos = self._TOMBSTONE_POS.get(d.get("name"), (d["x"], d["y"]))
        self._tombstones.append({"x": pos[0], "y": pos[1], "name": d.get("name", "?"), "d": d})

    def draw_tombstones(self):
        """R.I.P. stones for fallen guards. Font shrink-to-fit: text NEVER goes over the stone.
        Kills: liczba rysowana z minimalnym (2px) odstepem miedzy slowami,
        a nie pelna spacja - dzieki temu miesci sie przy mniejszej czcionce."""
        for tb in getattr(self, "_tombstones", []):
            w, h = 56, 60
            # Clamp so the stone is never cut off by the screen edge (Bonnie sits near x=22)
            cx = max(w // 2, min(self.width - w // 2, tb["x"]))
            cy = tb["y"]
            pygame.draw.ellipse(self.win, (50, 50, 50), (cx - w // 2, cy - 6, w, 10))
            rect = pygame.Rect(cx - w // 2, cy - h, w, h)
            pygame.draw.rect(self.win, (195, 195, 200), rect, border_radius=16)
            pygame.draw.rect(self.win, (100, 100, 110), rect, 2, border_radius=16)
            lines = ["R.I.P.", tb["name"]]
            kills_parts = (tr("tomb.kills"), str(tb['d'].get('kills', 0)))
            font = self._tomb_fonts[5]
            for s in (13, 12, 11, 10, 9, 8, 7, 6, 5):
                f = self._tomb_fonts[s]
                kills_w = f.size(kills_parts[0])[0] + 2 + f.size(kills_parts[1])[0]
                if max([f.size(ln)[0] for ln in lines] + [kills_w]) <= w - 10:
                    font = f
                    break
            # Tekst rzezbiony w kamieniu: ciemne litery (30,30,40) na jasnym
            # kamieniu + jasny offset +1px w dol = efekt dluta, wysoki kontrast
            # (wczesniej 60,60,70 na 195,195,200 byl prawie niewidoczny)
            def _carve(txt, lx, ly):
                lite = font.render(txt, True, (238, 238, 242))
                self.win.blit(lite, (lx, ly + 1))
                dark = font.render(txt, True, (30, 30, 40))
                self.win.blit(dark, (lx, ly))
            ty = cy - h + 7
            for ln in lines:
                lw = font.size(ln)[0]
                _carve(ln, cx - lw // 2, ty)
                ty += font.get_height() + 1
            # Kills: dwie czesci z 2px przerwa (nie pelna spacja)
            w1 = font.size(kills_parts[0])[0]
            w2 = font.size(kills_parts[1])[0]
            total = w1 + 2 + w2
            _carve(kills_parts[0], cx - total // 2, ty)
            _carve(kills_parts[1], cx - total // 2 + w1 + 2, ty)

    # Sciezka wrogow (kopia z enemies/enemy.py) - straznicy ida do posterunkow DROGA
    _GUARD_PATH = [
        (322, 658), (425, 630), (505, 591), (588, 581),
        (696, 570), (792, 558), (890, 546), (953, 536),
        (1034, 523), (1049, 497), (1021, 488), (944, 477),
        (838, 467), (724, 450), (626, 438), (540, 426),
        (448, 414), (359, 399), (264, 387), (250, 351)]

    def _start_guard_deployment(self):
        """Signal Fire kupione: tancerze IDA z ogniska na posterunki droga, nie teleportuja sie.
        Na drodze 2x predkosc mobow (2.0 px/tick), od najblizszego punktu drogi do posterunku
        polowa predkosci (1.0 px/tick)."""
        starts = [(996, 415), (1086, 415)]  # pozycje tancerzy przy ognisku (1041, 410) +-45
        for d, (sx, sy) in zip(self._dancers, starts):
            d["x"], d["y"] = sx, sy
            d["alive"] = True
            d["mode"] = "deploying"
            d["target"] = None
            d["cd"] = 0
            hx, hy = d.get("home_x", sx), d.get("home_y", sy)
            # Najblizszy punkt sciezki do startu i do posterunku
            def _nearest(px, py):
                bi, bd = 0, 1e18
                for i, (qx, qy) in enumerate(self._GUARD_PATH):
                    dd = (qx - px) ** 2 + (qy - py) ** 2
                    if dd < bd:
                        bi, bd = i, dd
                return bi
            ni = _nearest(sx, sy)
            ci = _nearest(hx, hy)
            if ni <= ci:
                pts = list(self._GUARD_PATH[ni:ci + 1])
            else:
                pts = list(reversed(self._GUARD_PATH[ci:ni + 1]))
            pts.append((hx, hy))  # ostatni odcinek: droga -> posterunek (wolniej)
            d["deploy_pts"] = pts
            d["deploy_idx"] = 0
            d["deploy_face"] = 1

    def _update_guard_arrows(self):
        """Strzaly straznikow: leca do celu, przy trafieniu 25 dmg (hit)."""
        for a in list(getattr(self, "_guard_arrows", [])):
            tgt = a.get("target")
            if tgt is None or getattr(tgt, "dying", False) or getattr(tgt, "dead", False) or getattr(tgt, "reached_end", False):
                # Cel zniknal: strzala leci do ostatniego punktu i znika
                tx, ty = a.get("tx", a["x"]), a.get("ty", a["y"])
            else:
                tx, ty = tgt.x, tgt.y - 20
                a["tx"], a["ty"] = tx, ty
            dx, dy = tx - a["x"], ty - a["y"]
            dist = math.hypot(dx, dy) or 1.0
            if dist <= 14:
                # Trafienie
                if tgt is not None and not getattr(tgt, "dying", False) and not getattr(tgt, "dead", False):
                    try:
                        killed = bool(tgt.hit(25))
                    except Exception:
                        tgt.health -= 25
                        if tgt.health <= 0 and not tgt.dying:
                            tgt.dying = True
                            killed = True
                        else:
                            killed = False
                    if killed:
                        self._ach_stats["dancer_kills"] = self._ach_stats.get("dancer_kills", 0) + 1
                        _g = a.get("guard")
                        if _g is not None:
                            _g["kills"] = _g.get("kills", 0) + 1
                    self.stats_damage += 25
                    self.damage_numbers.append([tgt.x, tgt.y - 40, "25", 40])
                    self.particles.burst(a["x"], a["y"], (200, 180, 150), count=3, speed=3, life=15, size=2)
                if a in self._guard_arrows:
                    self._guard_arrows.remove(a)
            else:
                a["x"] += dx / dist * 8.0
                a["y"] += dy / dist * 8.0

    def _update_guard_dancers(self):
        """Guards: bow shooting on post + one random guard duels a close enemy to mutual death."""
        if "signal" not in self.tent_upgrades:
            return
        GATE_X, GATE_Y = 250, 351
        TRIGGER_DIST = 150
        # Only one duel at a time: the other guard keeps bow-guarding until the next trigger
        duel_active = any(dd["alive"] and dd.get("mode") in ("charging", "dueling") for dd in self._dancers)
        for d in self._dancers:
            if not d["alive"]:
                continue
            mode = d.get("mode", "guard")
            if mode == "deploying":
                # Ida droga do posterunku: 2.0 px/tick na drodze, 1.0 na ostatnim odcinku do posterunku
                pts = d.get("deploy_pts") or []
                idx = d.get("deploy_idx", 0)
                if idx >= len(pts):
                    d["mode"] = "guard"
                    continue
                tx, ty = pts[idx]
                vx, vy = tx - d["x"], ty - d["y"]
                dist = math.hypot(vx, vy)
                # Ostatni punkt = posterunek: polowa predkosci
                speed = 1.0 if idx == len(pts) - 1 else 2.0
                if dist <= speed:
                    d["x"], d["y"] = tx, ty
                    d["deploy_idx"] = idx + 1
                    if d["deploy_idx"] >= len(pts):
                        d["mode"] = "guard"
                elif dist > 0:
                    d["x"] += vx / dist * speed
                    d["y"] += vy / dist * speed
                    d["deploy_face"] = 1 if vx >= 0 else -1
                continue
            if mode == "charging":
                tgt = d.get("target")
                if tgt is None or getattr(tgt, "dying", False) or getattr(tgt, "dead", False) or getattr(tgt, "reached_end", False) or getattr(tgt, "attacking", False):
                    d["mode"] = "returning"
                    d["target"] = None
                    continue
                tx, ty = tgt.x, tgt.y - 20
                vx, vy = tx - d["x"], ty - d["y"]
                dist = math.hypot(vx, vy)
                if dist < 32:
                    d["mode"] = "dueling"
                    d["duel_t"] = 30
                    d["swing"] = 0
                elif dist > 0:
                    d["x"] += vx / dist * 3.5
                    d["y"] += vy / dist * 3.5
                continue
            if mode == "dueling":
                tgt = d.get("target")
                d["swing"] = d.get("swing", 0) + 1
                if tgt is None or getattr(tgt, "dying", False) or getattr(tgt, "dead", False):
                    # Enemy died by tower/balloon mid-duel: guard survives, walks back
                    d["mode"] = "returning"
                    d["target"] = None
                    continue
                if getattr(tgt, "reached_end", False) or getattr(tgt, "attacking", False):
                    d["mode"] = "returning"
                    d["target"] = None
                    continue
                d["duel_t"] = d.get("duel_t", 30) - 1
                if d["duel_t"] % 10 == 0:
                    self.particles.burst(tgt.x, tgt.y - 25, (255, 220, 100), count=4, speed=3, life=15, size=2)
                if d["duel_t"] <= 0:
                    # Mutual kill: guard trades their life for the mob
                    dmg = max(0, int(getattr(tgt, "health", 0)))
                    killed = False
                    try:
                        killed = bool(tgt.hit(dmg)) if dmg > 0 else False
                    except Exception:
                        tgt.health = 0
                        tgt.dying = True
                        killed = True
                    if killed or getattr(tgt, "dying", False):
                        self._ach_stats["dancer_kills"] = self._ach_stats.get("dancer_kills", 0) + 1
                        d["kills"] = d.get("kills", 0) + 1
                    if dmg > 0:
                        self.stats_damage += dmg
                    d["alive"] = False
                    d["mode"] = "dead"
                    d["target"] = None
                    self._ach_stats["dancers_sacrificed"] = self._ach_stats.get("dancers_sacrificed", 0) + 1
                    self._add_tombstone(d)
                    self.particles.burst(d["x"], d["y"] - 20, (255, 100, 100), count=20, speed=4, life=40, size=4)
                    self.gold_notifications.append([tr("notif.guard_life"), 180])
                continue
            if mode == "returning":
                hx, hy = d.get("home_x", d["x"]), d.get("home_y", d["y"])
                vx, vy = hx - d["x"], hy - d["y"]
                dist = math.hypot(vx, vy)
                if dist < 5:
                    d["x"], d["y"] = hx, hy
                    d["mode"] = "guard"
                elif dist > 0:
                    d["x"] += vx / dist * 3.5
                    d["y"] += vy / dist * 3.5
                continue
            # mode == "guard": bow shooting
            d["cd"] -= 1
            if d["cd"] <= 0:
                best, best_d2 = None, 350 ** 2
                for en in self.enemies:
                    if en.dying or en.dead or en.reached_end:
                        continue
                    d2 = (en.x - d["x"]) ** 2 + (en.y - d["y"]) ** 2
                    if d2 < best_d2:
                        best, best_d2 = en, d2
                if best:
                    # Strzala jako widoczny pocisk (trafienie w _update_guard_arrows)
                    self._guard_arrows.append({"x": d["x"], "y": d["y"] - 20, "tx": best.x, "ty": best.y - 20, "target": best, "guard": d})
                    self.particles.burst(d["x"], d["y"] - 25, (200, 180, 150), count=3, speed=3, life=15, size=2)
                    d["cd"] = 120  # 2s
                else:
                    d["cd"] = 30
            # Duel trigger: one enemy close to (but not yet at) the gate
            if not duel_active and d.get("mode") == "guard":
                candidates = []
                for en in self.enemies:
                    if en.dying or en.dead or en.reached_end or getattr(en, "attacking", False):
                        continue
                    # Bosses are not dueled: they still use the gate sacrifice fallback
                    if type(en).__name__ == "Boss":
                        continue
                    # Already targeted by another guard?
                    if any(other is not d and other.get("target") is en for other in self._dancers):
                        continue
                    dist_gate = math.hypot(en.x - GATE_X, en.y - GATE_Y)
                    if dist_gate < TRIGGER_DIST:
                        candidates.append((dist_gate, en))
                if candidates:
                    candidates.sort(key=lambda p: p[0])
                    _, chosen_enemy = candidates[0]
                    # One RANDOM guard charges (this guard is the random pick when multiple are free;
                    # to keep it truly random across guards, pick from all free guards here)
                    free = [gg for gg in self._dancers if gg["alive"] and gg.get("mode") == "guard"]
                    if free:
                        pick = random.choice(free)
                        pick["mode"] = "charging"
                        pick["target"] = chosen_enemy
                        pick["swing"] = 0
                        duel_active = True

    def _dancer_sacrifice(self, en):
        """Enemy at the gate kills a guard instead of the building. Returns True if sacrificed."""
        if "signal" not in self.tent_upgrades:
            return False
        # Prefer a guard on post; if the reaching enemy was dueled, kill its duelist
        pick = None
        for dd in self._dancers:
            if dd["alive"] and dd.get("target") is en:
                pick = dd
                break
        if pick is None:
            for dd in self._dancers:
                if dd["alive"] and dd.get("mode") == "guard":
                    pick = dd
                    break
        if pick is None:
            for dd in self._dancers:
                if dd["alive"]:
                    pick = dd
                    break
        if pick is None:
            return False
        pick["alive"] = False
        pick["mode"] = "dead"
        pick["target"] = None
        pick["kills"] = pick.get("kills", 0) + 1  # guard took the gate enemy down with them
        self._add_tombstone(pick)
        self._ach_stats["dancers_sacrificed"] = self._ach_stats.get("dancers_sacrificed", 0) + 1
        self.particles.burst(pick["x"], pick["y"] - 20, (255, 100, 100), count=20, speed=4, life=40, size=4)
        self.gold_notifications.append([tr("notif.guard_life"), 180])
        return True

    def draw_campfire_dancers(self, cx, cy, t):
        """Tancerze przy ognisku (oryginalna animacja)."""
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
        # Axe blade points AWAY from the body (outward from handle tip), not back at the dancer
        _ox, _oy = sx2 - mx, sy2 - (my - 20)
        _ol = math.hypot(_ox, _oy) or 1.0
        _ox, _oy = _ox / _ol, _oy / _ol
        _px, _py = -_oy, _ox
        pygame.draw.polygon(self.win, (180, 180, 180), [(sx2 + _ox * 10 + _px * 4, sy2 + _oy * 10 + _py * 4), (sx2 + _ox * 10 - _px * 4, sy2 + _oy * 10 - _py * 4), (sx2, sy2)])
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
        t = self._anim_s
        if phase == 0:
            # Dzien - brak nakladki (oszczednosc)
            self.morning_fog = 0
            return
        if phase == 1:
            self.win.blit(self._overlay_sunset, (0, 0))
        elif phase == 2:
            self.win.blit(self._overlay_night, (0, 0))
            # B10: latarnie w nocy - usuniete na prosbe gracza
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
                              0, math.pi, 8 - i)
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
        self.gold_notifications.append([tr("notif.saved"), 120])

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
        self.gold_notifications.append([tr("notif.loaded"), 120])

    def draw_sky_effects(self):
        """Wizualne: niebo (slonce, ksiezyc, gwiazdy, zorza, spadajace gwiazdy)."""
        t = self._anim_s
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
            pygame.draw.circle(self.win, (180, 180, 200), (842, 64), 8)  # krater
            # Migoczace gwiazdy
            for i in range(30):
                sx = (i * 173) % self.width
                sy = (i * 97) % 180
                tw = 100 + 80 * math.sin(t * 3 + i)
                pygame.draw.circle(self.win, (255, 255, 255, int(tw)), (sx, sy), 2)
            # Zaczmienie: cien przesuwa sie przez ksiezyc (cykl 50s: 30s
            # przejscie + 20s przerwy). W szczycie (et=15s) zakrywa go
            # W PELNI (ten sam srodek i promien 28) - wczesniej mniejszy,
            # przesuniety "krater" nigdy go nie zakrywal.
            et = t % 50
            if et < 30:
                ex = 850 - 70 + (140 * et / 30)
                pygame.draw.circle(self.win, (15, 15, 35), (int(ex), 70), 28)
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
        t = self._anim_s
        # Fale (3 warstwy) - omijaja pomost (jest NAD woda, fale pod nim)
        _px0, _py0, _pw, _ph = _PIER_RECT
        for layer in range(3):
            for i in range(20):
                wx = (i * 60 + t * (10 + layer * 5)) % (self.width + 60) - 30
                wy = 640 + layer * 25 + 8 * math.sin(t * 1.5 + i + layer)
                if wx + 25 > _px0 and wx - 25 < _px0 + _pw and wy + 8 > _py0 and wy - 8 < _py0 + _ph:
                    continue
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
        # Pecherzyki przy brzegu - omijaja pomost (jak kraby i fale: pomost jest NAD woda)
        for i in range(8):
            bx = (i * 140 + t * 20) % self.width
            by = 630 + 5 * math.sin(t * 2 + i)
            if bx + 3 + 15 > _px0 and bx - 3 - 15 < _px0 + _pw and by + 3 + 15 > _py0 and by - 3 - 15 < _py0 + _ph:
                continue
            pygame.draw.circle(self.win, (200, 230, 255, 120), (int(bx), int(by)), 3)
        # Fale o skaly (splash)
        if random.random() < 0.1:
            self.particles.burst(150, 620, (255, 255, 255), count=3, speed=2, life=20, size=3)

    def _buy_building_upgrade(self, uid):
        """Kupno upgradu budynku."""
        self._buy_upgrade(BUILDING_UPGRADES, self.building_upgrades, uid, "building")

    def _buy_tent_upgrade(self, uid):
        """Kupno upgradu namiotu."""
        self._buy_upgrade(TENT_UPGRADES, self.tent_upgrades, uid, "tent")

    def _add_gold_spent(self, amount):
        """Wydatki: stats_gold_spent (ekran koncowy) + _ach_stats (achievementy, kumulatywnie)."""
        try:
            self.stats_gold_spent += amount
        except AttributeError:
            self.stats_gold_spent = amount
        self._ach_stats["gold_spent"] = self._ach_stats.get("gold_spent", 0) + amount

    def _on_tower_built(self, tower):
        """Wieza postawiona: towers_built + Fire/Golden per-run (max, nie suma)."""
        # Trudnosc: koszty ulepszen wiezy skalowane raz przy postawieniu
        # (wyswietlane w menu + pobierane przy Upgrade - ta sama lista).
        if not getattr(tower, "_diff_cost_scaled", False):
            tower._diff_cost_scaled = True
            _mult = self._diff("price_mult")
            tower.menu.item_cost = [int(round(c * _mult)) if isinstance(c, int) else c
                                    for c in tower.menu.item_cost]
        self.stats_towers_built += 1
        self._ach_stats["towers_built"] = self._ach_stats.get("towers_built", 0) + 1
        _tname = type(tower).__name__
        if _tname == "FireTower":
            self._run_fire_towers += 1
            self._ach_stats["fire_towers"] = max(self._ach_stats.get("fire_towers", 0), self._run_fire_towers)
        elif _tname == "GoldenTower":
            self._run_golden_towers += 1
            self._ach_stats["golden_towers"] = max(self._ach_stats.get("golden_towers", 0), self._run_golden_towers)

    def _on_tower_upgraded(self, tower):
        """Wieza ulepszona: max_level_towers (kumulatywnie) + max_level_at_once (max)."""
        if getattr(tower, "level", 0) >= getattr(tower, "max_level", 3):
            self._ach_stats["max_level_towers"] = self._ach_stats.get("max_level_towers", 0) + 1
        _at_max = sum(1 for _tw in self.towers if getattr(_tw, "level", 0) >= getattr(_tw, "max_level", 3))
        self._ach_stats["max_level_at_once"] = max(self._ach_stats.get("max_level_at_once", 0), _at_max)

    def _buy_upgrade(self, upg_list, owned_set, uid, kind):
        """Generyczne kupno upgradu."""
        upg = next((u for u in upg_list if u["id"] == uid), None)
        if not upg or uid in owned_set:
            return
        # Prerequisite (np. Drone Launch Facility wymaga Repair Drones)
        if upg.get("requires") and upg["requires"] not in owned_set:
            _req = next((u for u in upg_list if u["id"] == upg["requires"]), None)
            _req_name = _req["name"] if _req else upg["requires"]
            self.gold_notifications.append([f"Requires {_req_name} first.", 200])
            return
        # Cavalry: tylko w endless (easter egg w normalnej grze)
        cost = self._price(upg["cost"])
        if upg.get("endless_only") and not self.endless:
            if self.money >= cost:
                self.gold_notifications.append(
                    ["The cavalry doesn't sail in safe waters...", 200])
            else:
                self.gold_notifications.append(
                    ["This secret is not for sale... yet.", 200])
            return
        if self.money < cost:
            self.gold_notifications.append(["Not enough gold!", 150])
            return
        self.money -= cost
        self._add_gold_spent(cost)
        owned_set.add(uid)
        # Achievements: liczniki upgradow (max per-run) + konkretne zakupy
        if kind == "building":
            self._ach_stats["building_upgrades"] = max(self._ach_stats.get("building_upgrades", 0), len(self.building_upgrades))
            if uid == "cavalry":
                self._ach_stats["cavalry_bought"] = 1
        else:
            self._ach_stats["tent_upgrades"] = max(self._ach_stats.get("tent_upgrades", 0), len(self.tent_upgrades))
            if uid == "sabotage":
                self._ach_stats["sabotage_bought"] = 1
            elif uid == "balloon":
                self._ach_stats["balloon_bought"] = 1
            elif uid == "drums":
                self._ach_stats["drums_bought"] = 1
            elif uid == "medic":
                self._ach_stats["medic_bought"] = 1
        self.gold_notifications.append([f"{upg['name']} acquired!", 200])
        # Natychmiastowe efekty budynku
        if uid == "facility":
            self._facility_rearm = 30  # first drone emerges almost immediately
        if uid == "docks":
            # Pomost: spowolnienie dotyczy tez wrogow juz na mapie (na pomoście)
            for en in self.enemies:
                en._docks_slow = True
        if uid == "tesla":
            # Tesla Coil: gwarantowana burza w nastepnej rundzie.
            # Ze Storm Caller (kupionym WCZESNIEJ) burza trwa 2 rundy -
            # ten sam mechanizm _storm_extra co zwykle burze.
            self._tesla_guaranteed_storm = 1
        if uid == "drones":
            # Repair Drones: +1 zycie OD RAZU przy zakupie (potem +1 co 2 fale).
            # Jak Walls: podnosi tez max (start_lives), wiec bonus zawsze dziala.
            self._start_lives += 1
            self.lives += 1
            self.gold_notifications.append([tr("notif.life_drones"), 150])
        if uid == "walls":
            self._start_lives += 5
            self.lives += 5
        elif uid in ("ammo", "lucky"):
            for tw in self.towers:
                self._apply_tower_upgrade_flags(tw)
        if uid == "balloon":
            # Balon pojawia sie dopiero przy zakupie: startuje spoza lewej
            # krawedzi i wlatuje na mape (wczesniej latal od poczatku gry).
            self._balloon_x = -100
            self._balloon_bombs = []
            self._balloon_bomb_cd = 30
        # Natychmiastowe efekty namiotu
        if uid == "signal":
            self._start_guard_deployment()
        if uid == "spikes":
            self._place_spikes()
        elif uid in ("drums", "banner", "signal", "balloon"):
            for tw in self.towers:
                self._apply_tower_upgrade_flags(tw)

    def _apply_tower_upgrade_flags(self, tw):
        """Ustawia flagi upgradow (budynek + namiot) na wiezy."""
        tw._fire_rate_mult = 1.0
        if "ammo" in self.building_upgrades:
            tw._fire_rate_mult *= 1.15
        # Signal Fire: +12% fire rate dla WSZYSTKICH wiez Fire/Blaze (globalnie,
        # bez zasiegu ogniska). Tylko 2 typy wiez, wiec nie jest OP; stary
        # aura 350px dla wszystkich typow usunieta (nikt nie wiedzial co daje).
        if "signal" in self.tent_upgrades and type(tw).__name__ in ("FireTower", "BlazeTower"):
            tw._fire_rate_mult *= 1.12
        tw._dmg_mult = 1.0
        if "banner" in self.tent_upgrades:
            tw._dmg_mult *= 1.10  # Honor Banner: +10% dmg globalnie
        tw._ability_cd_mult = (0.7 if "drums" in self.tent_upgrades else 1.0) * self._diff("ability_cd_mult")

    def draw_building_menu(self):
        """Menu upgradow budynku."""
        self._draw_upgrade_menu(tr("upg.building_title"), BUILDING_UPGRADES,
                                self.building_upgrades, self._building_icons,
                                "_building_menu_open", "_building_menu_buttons",
                                "_building_menu_close_rect")

    def draw_tent_menu(self):
        """Menu upgradow namiotu."""
        self._draw_upgrade_menu(tr("upg.tent_title"), TENT_UPGRADES,
                                self.tent_upgrades, self._tent_icons,
                                "_tent_menu_open", "_tent_menu_buttons",
                                "_tent_menu_close_rect")

    def _draw_upgrade_menu(self, title_text, upg_list, owned_set, icons,
                           open_attr, buttons_attr, close_attr):
        """Generyczne menu upgradow (2 kolumny)."""
        if not getattr(self, open_attr):
            return
        # Przyciemnienie
        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        self.win.blit(dim, (0, 0))
        # Chain: wpis z "requires" (Drone Launch Facility -> Repair Drones)
        # NIE dostaje wlasnego czarnego slotu LOCKED. Dzieli slot rodzica:
        # rodzic niekupiony -> pokaz rodzica; rodzic kupiony, dziecko nie ->
        # ten SAM slot oferuje dziecko; oba kupione -> dziecko jako OWNED.
        _by_id = {u["id"]: u for u in upg_list}
        _children = {}
        for _u in upg_list:
            if _u.get("requires") and _u["requires"] in _by_id:
                _children[_u["requires"]] = _u
        ordered = []
        for _u in sorted(upg_list, key=lambda x: x["cost"]):
            if _u.get("requires") and _u["requires"] in _by_id:
                continue  # dziecko: pokazuje sie w slocie rodzica, nigdy osobno
            if _u["id"] in _children and _u["id"] in owned_set:
                ordered.append(_children[_u["id"]])
            else:
                ordered.append(_u)
        # Panel (wyzszy przy 6 wierszach) - rows policzone z gory, bo panel od niego zalezy
        rows = (len(ordered) + 1) // 2
        pw, ph = 820, 620 if rows <= 5 else 660
        px, py = (self.width - pw) // 2, (self.height - ph) // 2
        pygame.draw.rect(self.win, (22, 28, 38), (px, py, pw, ph), border_radius=16)
        pygame.draw.rect(self.win, (90, 110, 140), (px, py, pw, ph), 2, border_radius=16)
        title = self.font_p36.render(title_text, True, (255, 215, 100))
        self.win.blit(title, (px + (pw - title.get_width()) // 2, py + 18))
        # Przycisk zamkniecia
        setattr(self, close_attr, pygame.Rect(px + pw - 46, py + 12, 34, 34))
        _close_rect = getattr(self, close_attr)
        pygame.draw.rect(self.win, (150, 60, 60),
                         _close_rect, border_radius=8)
        x_lbl = self.font_btn18.render("X", True, (255, 255, 255))
        self.win.blit(x_lbl, (_close_rect.centerx - x_lbl.get_width() // 2,
                              _close_rect.centery - x_lbl.get_height() // 2))
        # Sloty: sortowanie po cenie + uklad KOLUMNOWY (najpierw cala lewa kolumna z gory na dol,
        # potem prawa) - nie wierszowy (lewo-prawo, lewo-prawo).
        # `ordered` policzone wyzej (z chainem: Facility w slocie Drones) - tu tylko rozmiar.
        n = len(ordered)
        # rows policzone wyzej (przed panelem)
        # 11+ widocznych upgradow -> 6 wierszy: kompaktowy uklad, inaczej panel by nie pomiescil
        row_h = 100 if rows <= 5 else 84
        gap_y = 8 if rows <= 5 else 6
        desc_step = 18 if rows <= 5 else 15
        setattr(self, buttons_attr, [])
        mx, my = self._mouse_pos()
        col_w = (pw - 60) // 2
        for i, upg in enumerate(ordered):
            col = i // rows
            row = i % rows
            sx = px + 20 + col * (col_w + 20)
            sy = py + 70 + row * (row_h + gap_y)
            rect = pygame.Rect(sx, sy, col_w, row_h)
            owned = upg["id"] in owned_set
            # Easter egg: cavalry ukryte w normalnej grze
            mystery = upg.get("endless_only") and not self.endless
            # Locked: wymaga innego upgradu (zapasowy mechanizm - chain pokazuje
            # dziecko w slocie rodzica dopiero po kupieniu rodzica, wiec LOCKED
            # w praktyce sie nie pojawia)
            _req_id = upg.get("requires")
            locked = bool(_req_id) and _req_id not in owned_set
            _req_name = next((tr(f"upg.{u['id']}.name", u["name"]) for u in upg_list if u["id"] == _req_id), _req_id) if _req_id else ""
            hover = rect.collidepoint(mx, my) and not owned and not locked
            bg_col = (35, 45, 60) if not hover else (50, 65, 90)
            if owned:
                bg_col = (30, 60, 40)
            if locked:
                bg_col = (28, 30, 38)
            pygame.draw.rect(self.win, bg_col, rect, border_radius=10)
            pygame.draw.rect(self.win, (100, 120, 150) if not owned else (80, 200, 120),
                             rect, 2, border_radius=10)
            # Ikonka
            if mystery:
                # Ciemna sylwetka ze znakiem zapytania
                q_bg = pygame.Surface((56, 56), pygame.SRCALPHA)
                pygame.draw.circle(q_bg, (15, 18, 25), (28, 28), 26)
                pygame.draw.circle(q_bg, (80, 90, 110), (28, 28), 26, 2)
                q = self.font_p36.render("?", True, (120, 130, 150))
                q_bg.blit(q, (28 - q.get_width() // 2, 28 - q.get_height() // 2))
                self.win.blit(q_bg, (sx + 10, sy + (row_h - 56) // 2))
                name = "???"
                desc = tr("upg.mystery_desc")
                price_txt = "???"
            else:
                icon = icons.get(upg["id"])
                if icon:
                    self.win.blit(icon, (sx + 10, sy + (row_h - 56) // 2))
                name = tr(f"upg.{upg['id']}.name", upg["name"])
                desc = tr("upg.requires", name=_req_name) if locked else tr(f"upg.{upg['id']}.desc", upg["desc"])
                price_txt = tr("upg.locked") if locked else f"{self._price(upg['cost']):,}"
            # Opis: wrap po szerokosci w pikselach (nie po liczbie znakow) - nic nie ucina
            desc_col = (110, 115, 125) if mystery else (170, 180, 190)
            desc_font = self._building_desc_font
            max_desc_w = col_w - 76 - 12 - 4  # tekst od sx+76 do prawej krawedzi karty
            words = desc.split()
            lines, cur = [], ""
            for w_ in words:
                test = (cur + " " + w_).strip()
                if cur and desc_font.size(test)[0] > max_desc_w:
                    lines.append(cur)
                    cur = w_
                else:
                    cur = test
            if cur:
                lines.append(cur)
            full_lines = lines
            truncated = len(full_lines) > 2
            # Hover-scroll: karta z opisem dluzszym niz 2 linie przewija go
            # plynnie w dol po najechaniu (0.5 s zwloki, 30 px/s), zeby dalo
            # sie przeczytac calosc w KAZDYM jezyku; po wyjechaniu myszy
            # wraca na gore z forma ucieta ("...").
            if not hasattr(self, "_upg_hover"):
                self._upg_hover = {}
            if rect.collidepoint(mx, my):
                self._upg_hover.setdefault(upg["id"], self._now_s)
                _hstart = self._upg_hover[upg["id"]]
            else:
                self._upg_hover.pop(upg["id"], None)
                _hstart = None
            scroll_off = 0.0
            if truncated and _hstart is not None:
                scroll_off = min((len(full_lines) - 2) * desc_step,
                                 max(0.0, (self._now_s - _hstart - 0.5)) * 30.0)
            if truncated and scroll_off <= 0:
                # Forma ucieta: 2 linie + wielokropek
                lines = full_lines[:2]
                while len(lines) > 1 and desc_font.size(lines[1] + "…")[0] > max_desc_w and len(lines[1]) > 1:
                    lines[1] = lines[1][:-1].rstrip()
                lines[1] = lines[1] + "…"
            else:
                lines = full_lines
            # Tytul + tekst WYCOWANE W PIONIE wzgledem obrazka (ikonka jest
            # wycentrowana w karcie; wczesniej tytul byl przyklejony do gory,
            # a cena do dolu - tekst wygladal na niewycentrowany).
            icon_cy = sy + (row_h - 56) // 2 + 28  # srodek ikonki 56x56
            name_h = self.font_btn18.get_height()
            block_h = name_h + 4 + min(2, len(full_lines)) * desc_step
            block_top = icon_cy - block_h // 2
            # Nazwa
            name_col = (150, 150, 160) if mystery else (240, 240, 240)
            name_lbl = self.font_btn18.render(name, True, name_col)
            self.win.blit(name_lbl, (sx + 76, block_top))
            if scroll_off > 0:
                # Przewijany opis w oknie 2 linii (clip), reszta wyjezdza nizej
                _clip = pygame.Rect(sx + 76, block_top + name_h + 4,
                                    max_desc_w + 4, 2 * desc_step)
                _prev_clip = self.win.get_clip()
                self.win.set_clip(_clip)
                for li, ln in enumerate(full_lines):
                    ly = block_top + name_h + 4 + li * desc_step - int(scroll_off)
                    if ly + desc_step < _clip.top or ly > _clip.bottom:
                        continue
                    d_lbl = desc_font.render(ln, True, desc_col)
                    self.win.blit(d_lbl, (sx + 76, ly))
                self.win.set_clip(_prev_clip)
            else:
                for li, ln in enumerate(lines[:2]):
                    d_lbl = desc_font.render(ln, True, desc_col)
                    self.win.blit(d_lbl, (sx + 76, block_top + name_h + 4 + li * desc_step))
            # Cena / status (prawy GORNY rog, w wierszu tytulu - nie koliduje z opisem)
            if owned:
                st = self.font_btn18.render(tr("upg.owned"), True, (100, 220, 130))
            elif mystery:
                st = self.font_btn18.render("???", True, (120, 130, 150))
            elif locked:
                st = self.font_btn18.render(tr("upg.locked"), True, (130, 130, 140))
            else:
                afford = self.money >= self._price(upg["cost"])
                st = self.font_btn18.render(price_txt,
                                            True, (255, 215, 100) if afford else (200, 100, 100))
            self.win.blit(st, (rect.right - st.get_width() - 12, block_top))
            if not mystery and not locked:
                # Ikona monety zamiast symbolu $ (cena w zlocie)
                self.win.blit(self._coin_icon15,
                              (rect.right - st.get_width() - 12 - 19, block_top + 2))
            if not owned and not locked:
                getattr(self, buttons_attr).append((rect, upg["id"]))

    def _scale_poly(self, pts, factor):
        """Scale polygon around its centroid (for lift effect)."""
        if not pts:
            return pts
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        return [(cx + (x - cx) * factor, cy + (y - cy) * factor) for (x, y) in pts]

    def draw_building_highlight(self):
        """Gwent-style lift + glow on the drawn building polygon (glass-blue, not yellow)."""
        if getattr(self, "moving_object", None) is not None:
            return  # A: podczas przecigania wiezy budynek nie podswietla sie
        t = self._anim_s
        mx, my = self._mouse_pos()
        hovering = self._point_in_poly(mx, my, self._building_highlight_pts)
        menu_open = getattr(self, "_building_menu_open", False)
        if not hovering and not menu_open:
            return
        # Hover: breathing pulse; menu open: steady strong lift
        pulse = 0.5 + 0.5 * math.sin(t * 4) if hovering and not menu_open else 1.0
        lift = 1.03 + 0.015 * pulse if hovering else 1.04
        pts = self._scale_poly(self._building_highlight_pts, lift)
        # Drop shadow under the "lifted" shape
        s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        shadow = [(x, y + 8) for (x, y) in pts]
        pygame.draw.polygon(s, (0, 0, 0, 60), shadow)
        # Outer glow layers
        pygame.draw.polygon(s, (80, 160, 255, 35 + int(25 * pulse)), pts)
        pygame.draw.polygon(s, (120, 200, 255, 60 + int(40 * pulse)), pts, 6)
        pygame.draw.polygon(s, (180, 230, 255, 140 + int(60 * pulse)), pts, 3)
        # Fill
        pygame.draw.polygon(s, (80, 160, 255, 30 + int(20 * pulse)), pts)
        self.win.blit(s, (0, 0))

    def draw_tent_highlight(self):
        """Gwent-style lift + glow on the drawn tent polygon (warm amber, not yellow)."""
        if getattr(self, "moving_object", None) is not None:
            return  # A: podczas przecigania wiezy namiot nie podswietla sie
        t = self._anim_s
        mx, my = self._mouse_pos()
        hovering = self._point_in_poly(mx, my, self._tent_highlight_pts)
        menu_open = getattr(self, "_tent_menu_open", False)
        if not hovering and not menu_open:
            return
        pulse = 0.5 + 0.5 * math.sin(t * 4) if hovering and not menu_open else 1.0
        lift = 1.04 + 0.02 * pulse if hovering else 1.05
        pts = self._scale_poly(self._tent_highlight_pts, lift)
        s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        shadow = [(x, y + 8) for (x, y) in pts]
        pygame.draw.polygon(s, (0, 0, 0, 60), shadow)
        pygame.draw.polygon(s, (255, 170, 40, 35 + int(25 * pulse)), pts)
        pygame.draw.polygon(s, (255, 190, 80, 60 + int(40 * pulse)), pts, 6)
        pygame.draw.polygon(s, (255, 220, 150, 140 + int(60 * pulse)), pts, 3)
        pygame.draw.polygon(s, (255, 180, 60, 30 + int(20 * pulse)), pts)
        self.win.blit(s, (0, 0))

    def draw_repair_drone(self):
        """Wizualny dron krazacy wokol budynku (po kupnie Repair Drones)."""
        if "drones" not in self.building_upgrades:
            return
        if not self.paused:
            self._drone_angle += 0.03
        bx, by = 260, 285  # srodek budynku
        rx, ry = 150, 80
        dx = bx + rx * math.cos(self._drone_angle)
        dy = by + ry * math.sin(self._drone_angle)
        # Korpus drona
        pygame.draw.ellipse(self.win, (70, 80, 95), (dx - 14, dy - 8, 28, 16))
        pygame.draw.ellipse(self.win, (40, 200, 255), (dx - 6, dy - 4, 12, 8))
        # Wirniki
        for ox, oy in [(-16, -10), (16, -10), (-16, 10), (16, 10)]:
            pygame.draw.ellipse(self.win, (200, 220, 235, 160),
                                (dx + ox - 10, dy + oy - 3, 20, 6))
        # Zielony wskaznik naprawy
        if int(self._drone_angle * 10) % 30 == 0:
            self.particles.burst(dx, dy + 10, (100, 255, 150), count=2, speed=1, life=20, size=2)

    # ---- Combat drone (Drone Launch Facility) ----
    # Logika w tickach 100Hz (update_game_logic): 2-4 min zycia = 12000-24000,
    # rearm 3 min = 18000, minigun 0.15s = 15 tickow.
    _FACILITY_POS = (165, 198)  # flat rectangle dock, placed via drag tool
    _DRONE_LIFE = (12000, 24000)
    _DRONE_REARM = 18000
    _DRONE_FIRE_CD = 15
    _DRONE_SPEED = 2.2  # wolniej - wczesniej latal jak rozwscieczony komar
    _DRONE_DIVE = 5.5
    _DRONE_MINIGUN = 8
    _DRONE_KAMIKAZE_DMG = 400
    _DRONE_KAMIKAZE_R = 140
    # Standoff: dron trzyma dystans do celu, nie wlatuje we wrogow
    _DRONE_STANDOFF_MIN = 110
    _DRONE_STANDOFF_MAX = 170
    # Wyrzutnia rakiet: rzadki strzal, obrazenia obszarowe
    _DRONE_ROCKET_CD = 2000  # 20 s miedzy rakietami
    _DRONE_ROCKET_FIRST = 600  # pierwsza rakieta po 6 s od startu
    _DRONE_ROCKET_DMG = 150
    _DRONE_ROCKET_R = 120
    _DRONE_ROCKET_SPEED = 7.0

    def _spawn_combat_drone(self):
        """Drone emerges from the facility box."""
        fx, fy = self._FACILITY_POS
        self._combat_drone = {
            "x": float(fx), "y": float(fy), "state": "emerge", "emerge_t": 40,
            "life": random.randint(*self._DRONE_LIFE), "target": None,
            "wp": None, "fire_cd": 0, "engage_t": 0,
            "kamikaze_target": None, "kamikaze_pos": None,
            "spin": 0.0, "barrel": 0.0, "flash": 0,
            "rocket_cd": self._DRONE_ROCKET_FIRST, "strafe_dir": 1,
            # Wyrzutnia rakiet: -pi/2 = pionowo (spoczynek), celuje tylko przy strzale
            "launcher_ang": math.pi / 2, "launcher_timer": 0, "launcher_target": None,
        }
        self.gold_notifications.append(["Combat drone launched!", 150])

    def _drone_fly_toward(self, d, tx, ty, speed):
        """Fly toward (tx, ty) with a zigzag wobble. True on arrival (within 20px)."""
        vx, vy = tx - d["x"], ty - d["y"]
        dist = math.hypot(vx, vy)
        if dist < 20:
            return True
        if dist > 0:
            px, py = -vy / dist, vx / dist
            wob = math.sin(d.get("spin", 0) * 0.35) * 1.6
            d["x"] += vx / dist * speed + px * wob
            d["y"] += vy / dist * speed + py * wob
            d["x"] = max(20, min(1104, d["x"]))
            d["y"] = max(40, min(700, d["y"]))
        return False

    def _drone_standoff(self, d, tx, ty):
        """Trzyma dystans do celu: zbliza sie gdy dalej niz MAX, cofa gdy
        blizej niz MIN, a w pasmie miedzy nimi strafuje na boki (orbita).
        Dron nigdy nie wlatuje we wrogow, ktorych ostrzeliwuje."""
        vx, vy = tx - d["x"], ty - d["y"]
        dist = math.hypot(vx, vy)
        if dist < 1:
            return
        ux, uy = vx / dist, vy / dist
        wob = math.sin(d.get("spin", 0) * 0.35) * 1.2
        px, py = -uy, ux  # prostopadly (strafe)
        if dist > self._DRONE_STANDOFF_MAX:
            mx, my = ux, uy
        elif dist < self._DRONE_STANDOFF_MIN:
            mx, my = -ux, -uy
        else:
            # W pasmie: orbita + odrobina dryfu, zeby nie stal w miejscu
            if random.random() < 0.005:
                d["strafe_dir"] = -d.get("strafe_dir", 1)
            s = d.get("strafe_dir", 1)
            mx, my = px * s + ux * 0.15, py * s + uy * 0.15
        ml = math.hypot(mx, my) or 1.0
        d["x"] += mx / ml * self._DRONE_SPEED + px * wob
        d["y"] += my / ml * self._DRONE_SPEED + py * wob
        d["x"] = max(20, min(1104, d["x"]))
        d["y"] = max(40, min(700, d["y"]))

    def _drone_living_enemies(self):
        return [e for e in self.enemies if not getattr(e, "dying", False)
                and not getattr(e, "dead", False) and not getattr(e, "reached_end", False)]

    def _update_combat_drone(self):
        # Tracers / blasts decay even when no drone is flying
        for tr in list(getattr(self, "_facility_tracers", [])):
            tr[4] -= 1
            if tr[4] <= 0:
                self._facility_tracers.remove(tr)
        for bl in list(getattr(self, "_facility_blasts", [])):
            bl["ttl"] -= 1
            if bl["ttl"] <= 0:
                self._facility_blasts.remove(bl)
        self._update_drone_rockets()
        if "facility" not in self.building_upgrades:
            return
        d = self._combat_drone
        if d is None:
            if self._facility_rearm > 0:
                self._facility_rearm -= 1
                if self._facility_rearm <= 0:
                    self._spawn_combat_drone()
            return
        d["spin"] += 0.6
        if d["flash"] > 0:
            d["flash"] -= 1
        # Wyrzutnia rakiet celuje w biezacy cel DOKLADNIE jak minigun:
        # gdy dron ma zywy cel (engage), tuba sledzi go caly czas - nie
        # tylko w chwili strzalu. Bez celu wraca do pozycji neutralnej
        # (zwisa w dol, +pi/2, jak minigun). Kat przybliza sie plynnie
        # do docelowego (max 0.25 rad/tick).
        _lt = d.get("target")
        if d.get("launcher_timer", 0) > 0:
            d["launcher_timer"] -= 1
            if _lt is not None and not getattr(_lt, "dying", False) and not getattr(_lt, "dead", False):
                d["launcher_target"] = (float(_lt.x), float(_lt.y - 20))
            _ltg = d.get("launcher_target")
            if _ltg is not None:
                _want = math.atan2(_ltg[1] - (d["y"] - 10), _ltg[0] - (d["x"] + 6))
            else:
                _want = math.pi / 2
        elif (_lt is not None and d.get("state") == "engage"
              and not getattr(_lt, "dying", False) and not getattr(_lt, "dead", False)
              and not getattr(_lt, "reached_end", False)):
            _want = math.atan2((_lt.y - 20) - (d["y"] - 10), _lt.x - (d["x"] + 6))
        else:
            _want = math.pi / 2
        _cur = d.get("launcher_ang", math.pi / 2)
        _dang = (_want - _cur + math.pi) % (2 * math.pi) - math.pi
        d["launcher_ang"] = _cur + max(-0.25, min(0.25, _dang))
        state = d["state"]
        if state == "emerge":
            d["emerge_t"] -= 1
            d["y"] -= 0.45  # rises out of the box
            if d["emerge_t"] <= 0:
                d["state"] = "wander"
                d["wp"] = (random.uniform(60, 1060), random.uniform(120, 660))
            return
        # Lifetime ticks down in wander/engage (kamikaze is already committed)
        if state in ("wander", "engage"):
            d["life"] -= 1
            if d["life"] <= 0:
                d["state"] = "kamikaze"
                d["kamikaze_target"] = None
                d["kamikaze_pos"] = None
                d["target"] = None
                state = "kamikaze"
        if state == "wander":
            wx, wy = d["wp"] or (d["x"], d["y"])
            if self._drone_fly_toward(d, wx, wy, self._DRONE_SPEED):
                living = self._drone_living_enemies()
                if living and random.random() < 0.55:
                    d["target"] = random.choice(living)
                    d["state"] = "engage"
                    d["engage_t"] = 0
                else:
                    # Sometimes it just flies somewhere (idle zigzag, no shooting)
                    d["wp"] = (random.uniform(60, 1060), random.uniform(120, 660))
        elif state == "engage":
            tgt = d.get("target")
            if tgt is None or getattr(tgt, "dying", False) or getattr(tgt, "dead", False) or getattr(tgt, "reached_end", False):
                living = self._drone_living_enemies()
                if living:
                    d["target"] = random.choice(living)
                    tgt = d["target"]
                    d["engage_t"] = 0
                else:
                    d["state"] = "wander"
                    d["wp"] = (random.uniform(60, 1060), random.uniform(120, 660))
                    d["target"] = None
                    return
            d["engage_t"] += 1
            # Standoff: trzyma dystans, nie wlatuje w cel
            self._drone_standoff(d, tgt.x, tgt.y - 20)
            # Animated minigun: rotating barrels + tracer + muzzle flash + sound
            d["fire_cd"] -= 1
            if d["fire_cd"] <= 0:
                d["fire_cd"] = self._DRONE_FIRE_CD
                d["barrel"] += 1.1
                d["flash"] = 4
                if tgt is not None and not getattr(tgt, "dying", False) and not getattr(tgt, "dead", False):
                    self._facility_tracers.append([d["x"], d["y"] - 18, tgt.x, tgt.y - 20, 6])
                    try:
                        sound_minigun.play()
                    except Exception:
                        pass
                    try:
                        tgt.hit(self._DRONE_MINIGUN)
                    except Exception:
                        tgt.health -= self._DRONE_MINIGUN
                        if tgt.health <= 0 and not tgt.dying:
                            tgt.dying = True
                    self.stats_damage += self._DRONE_MINIGUN
                    self.damage_numbers.append([tgt.x, tgt.y - 40, str(self._DRONE_MINIGUN), 40])
            # Wyrzutnia rakiet: rzadki strzal obszarowy (co ~20 s)
            d["rocket_cd"] -= 1
            if d["rocket_cd"] <= 0:
                d["rocket_cd"] = self._DRONE_ROCKET_CD
                if tgt is not None and not getattr(tgt, "dying", False) and not getattr(tgt, "dead", False):
                    self._fire_drone_rocket(d, tgt)
            # Sometimes break off and just fly somewhere (zigzag idle feel)
            if d["engage_t"] > random.randint(300, 600):
                d["state"] = "wander"
                d["wp"] = (random.uniform(60, 1060), random.uniform(120, 660))
                d["target"] = None
        elif state == "kamikaze":
            tgt = d.get("kamikaze_target")
            if tgt is None:
                living = self._drone_living_enemies()
                if living:
                    tgt = random.choice(living)
                    d["kamikaze_target"] = tgt
                    d["kamikaze_pos"] = (tgt.x, tgt.y - 20)
                else:
                    # No enemies: keep flying until one spawns, then dive at it
                    if d.get("wp") is None:
                        d["wp"] = (random.uniform(60, 1060), random.uniform(120, 660))
                    if self._drone_fly_toward(d, d["wp"][0], d["wp"][1], self._DRONE_SPEED):
                        d["wp"] = None
                    return
            if tgt is not None:
                # Track the target while alive; if it dies mid-dive, detonate
                # at its last position anyway (Daniel: "regardless of whether
                # the enemy has died before that").
                if not getattr(tgt, "dying", False) and not getattr(tgt, "dead", False) and not getattr(tgt, "reached_end", False):
                    d["kamikaze_pos"] = (tgt.x, tgt.y - 20)
                tx, ty = d["kamikaze_pos"]
                if self._drone_fly_toward(d, tx, ty, self._DRONE_DIVE):
                    self._detonate_drone()

    def _fire_drone_rocket(self, d, tgt):
        """Wyrzutnia rakiet: rakieta leci do celu i wybucha obszarowo.
        Wyrzutnia obraca sie w strone celu na czas strzalu (animacja celowania)."""
        self._facility_rockets.append({
            "x": float(d["x"]), "y": float(d["y"] - 18),
            "target": tgt, "tx": float(tgt.x), "ty": float(tgt.y - 20),
            "trail": [],
        })
        d["launcher_timer"] = 90  # ~0.9 s celowania (strzal + lot rakiety)
        d["launcher_target"] = (float(tgt.x), float(tgt.y - 20))
        try:
            sound_rocket.play()
        except Exception:
            pass

    def _update_drone_rockets(self):
        """Rakiety leca do celu (sledza go, gdy zyje); na miejscu - wybuch."""
        for r in list(getattr(self, "_facility_rockets", [])):
            tgt = r.get("target")
            if tgt is not None and not getattr(tgt, "dying", False) and not getattr(tgt, "dead", False) and not getattr(tgt, "reached_end", False):
                r["tx"], r["ty"] = float(tgt.x), float(tgt.y - 20)
            vx, vy = r["tx"] - r["x"], r["ty"] - r["y"]
            dist = math.hypot(vx, vy)
            r["trail"].append((r["x"], r["y"]))
            if len(r["trail"]) > 10:
                r["trail"].pop(0)
            if dist <= 16:
                self._facility_rockets.remove(r)
                self._explode_drone_rocket(r["tx"], r["ty"])
            elif dist > 0:
                r["x"] += vx / dist * self._DRONE_ROCKET_SPEED
                r["y"] += vy / dist * self._DRONE_ROCKET_SPEED

    def _explode_drone_rocket(self, x, y):
        """Wybuch rakiety: obrazenia obszarowe dla wielu wrogow."""
        self._facility_blasts.append({"x": x, "y": y, "ttl": 24, "max": 24,
                                      "r": self._DRONE_ROCKET_R})
        self.particles.burst(x, y, (255, 150, 50), count=25, speed=5, life=30, size=4)
        self.particles.burst(x, y, (255, 220, 120), count=15, speed=3, life=22, size=3)
        try:
            sound_rocket_boom.play()
        except Exception:
            pass
        for en in list(self.enemies):
            if getattr(en, "dying", False) or getattr(en, "dead", False) or getattr(en, "reached_end", False):
                continue
            if (en.x - x) ** 2 + (en.y - y) ** 2 <= self._DRONE_ROCKET_R ** 2:
                try:
                    en.hit(self._DRONE_ROCKET_DMG)
                except Exception:
                    en.health -= self._DRONE_ROCKET_DMG
                    if en.health <= 0 and not en.dying:
                        en.dying = True
                self.stats_damage += self._DRONE_ROCKET_DMG
                self.damage_numbers.append([en.x, en.y - 40, str(self._DRONE_ROCKET_DMG), 60])

    def _detonate_drone(self):
        """Kamikaze splash: 400 dmg in 140px, then the 3-min rearm starts."""
        d = self._combat_drone
        if d is None:
            return
        x, y = d["x"], d["y"] - 18
        self._facility_blasts.append({"x": x, "y": y, "ttl": 30, "max": 30,
                                      "r": self._DRONE_KAMIKAZE_R})
        self.particles.burst(x, y, (255, 150, 50), count=40, speed=6, life=40, size=4)
        self.particles.burst(x, y, (255, 220, 120), count=25, speed=4, life=30, size=3)
        for en in list(self.enemies):
            if getattr(en, "dying", False) or getattr(en, "dead", False) or getattr(en, "reached_end", False):
                continue
            if (en.x - x) ** 2 + (en.y - y) ** 2 <= self._DRONE_KAMIKAZE_R ** 2:
                try:
                    en.hit(self._DRONE_KAMIKAZE_DMG)
                except Exception:
                    en.health -= self._DRONE_KAMIKAZE_DMG
                    if en.health <= 0 and not en.dying:
                        en.dying = True
                self.stats_damage += self._DRONE_KAMIKAZE_DMG
                self.damage_numbers.append([en.x, en.y - 40, str(self._DRONE_KAMIKAZE_DMG), 60])
        self._combat_drone = None
        self._facility_rearm = self._DRONE_REARM
        self.gold_notifications.append([tr("notif.drone_down"), 200])

    def draw_facility(self):
        """Flat rectangular dock on the building roof (165, 198).
        No name on it - only the countdown: KAMIKAZE while the drone flies,
        NEXT DRONE while rearming."""
        if "facility" not in self.building_upgrades:
            return
        fx, fy = self._FACILITY_POS
        w, h = 72, 34
        rect = pygame.Rect(fx - w // 2, fy - h // 2, w, h)
        # Flat metal box
        pygame.draw.rect(self.win, (70, 78, 88), rect, border_radius=6)
        pygame.draw.rect(self.win, (40, 46, 54), rect, 2, border_radius=6)
        # Glowing LED strip along the front edge (like the reference image)
        pygame.draw.rect(self.win, (255, 170, 60), (fx - w // 2 + 4, fy + h // 2 - 5, w - 8, 3), border_radius=1)
        d = self._combat_drone
        if d is not None:
            label, secs = tr("dock.kamikaze"), max(0, d["life"] // 100)
            lab_col, time_col = (255, 120, 120), (255, 220, 200)
        else:
            label, secs = tr("dock.next"), max(0, self._facility_rearm // 100)
            lab_col, time_col = (255, 210, 120), (255, 240, 190)
        time_txt = f"{secs // 60}:{secs % 60:02d}"
        lab_font = self._tomb_fonts[6]
        for s in (8, 7, 6):
            if self._tomb_fonts[s].size(label)[0] <= w - 8:
                lab_font = self._tomb_fonts[s]
                break
        time_font = self._tomb_fonts[13]
        for s in (13, 11, 10, 9, 8):
            if self._tomb_fonts[s].size(time_txt)[0] <= w - 8:
                time_font = self._tomb_fonts[s]
                break
        lab = lab_font.render(label, True, lab_col)
        tlab = time_font.render(time_txt, True, time_col)
        self.win.blit(lab, (fx - lab.get_width() // 2, fy - 14))
        # Timer lekko podwyzszony (fy-6, nie fy-3) - nie najezdza na zolty LED,
        # ale nie wchodzi w opis KAMIKAZE / NEXT DRONE.
        self.win.blit(tlab, (fx - tlab.get_width() // 2, fy - 6))

    def draw_combat_drone(self):
        """Flying drone + minigun tracers + kamikaze blast rings + rockets.
        Model po grafice Daniela: jasna sylwetka quadcoptera, 4 ramiona
        z wirnikami, kamera-gimbal pod spodem, minigun po lewej i wyrzutnia
        rakiet po prawej - obie bronie widoczne na modelu."""
        for tr in getattr(self, "_facility_tracers", []):
            a = max(0, min(255, int(255 * tr[4] / 6)))
            s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.line(s, (255, 220, 120, a), (tr[0], tr[1]), (tr[2], tr[3]), 2)
            self.win.blit(s, (0, 0))
        for bl in getattr(self, "_facility_blasts", []):
            prog = 1.0 - bl["ttl"] / bl["max"]
            rmax = bl.get("r", 140) + 20
            r = int(30 + prog * (rmax - 30))
            a = int(220 * (1 - prog))
            s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 150, 50, a), (int(bl["x"]), int(bl["y"])), r, 4)
            pygame.draw.circle(s, (255, 220, 120, a), (int(bl["x"]), int(bl["y"])), int(r * 0.6), 3)
            self.win.blit(s, (0, 0))
        # Lecace rakiety: smuga + korpus z plomieniem
        for r in getattr(self, "_facility_rockets", []):
            trail = r.get("trail", [])
            if len(trail) > 1:
                s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                for i in range(len(trail) - 1):
                    a = int(160 * (i + 1) / len(trail))
                    pygame.draw.line(s, (255, 180, 80, a), trail[i], trail[i + 1], 2)
                self.win.blit(s, (0, 0))
            ang = math.atan2(r["ty"] - r["y"], r["tx"] - r["x"])
            rx, ry = r["x"], r["y"]
            bx, by = rx - math.cos(ang) * 8, ry - math.sin(ang) * 8
            pygame.draw.line(self.win, (255, 120, 60), (bx, by), (rx, ry), 4)
            pygame.draw.circle(self.win, (255, 220, 100), (int(bx), int(by)), 3)
        d = self._combat_drone
        if d is None:
            return
        x, y = d["x"], d["y"] - 18
        # Ground shadow
        pygame.draw.ellipse(self.win, (50, 50, 50), (d["x"] - 24, d["y"] + 12, 48, 10))
        # Ramiona (4) - ciemne, jak w sylwetce z grafiki
        for ox, oy in [(-24, -12), (24, -12), (-24, 12), (24, 12)]:
            pygame.draw.line(self.win, (45, 50, 58), (x, y), (x + ox, y + oy), 3)
        # Wirniki - krecace sie
        spin = d.get("spin", 0)
        for ox, oy in [(-24, -12), (24, -12), (-24, 12), (24, 12)]:
            rw = 9 + 5 * math.sin(spin + ox)
            pygame.draw.ellipse(self.win, (200, 220, 235), (x + ox - rw, y + oy - 2, rw * 2, 4))
        # Korpus - jasna sylwetka (jak na grafice)
        pygame.draw.ellipse(self.win, (210, 215, 222), (x - 16, y - 10, 32, 20))
        pygame.draw.ellipse(self.win, (150, 158, 168), (x - 16, y - 10, 32, 20), 2)
        # Kamera-gimbal pod spodem
        pygame.draw.circle(self.win, (40, 200, 255), (int(x), int(y + 8)), 4)
        pygame.draw.circle(self.win, (20, 60, 90), (int(x), int(y + 8)), 4, 1)
        # Minigun (lewa strona): lufa celuje w cel, blysk przy strzale
        tgt = d.get("target") if d.get("state") == "engage" else None
        if tgt is not None and not getattr(tgt, "dead", False):
            ang = math.atan2((tgt.y - 20) - (y + 8), tgt.x - (x - 12))
        else:
            ang = math.pi / 2
        gx, gy = x - 12, y + 8
        bx2 = gx + math.cos(ang) * 16
        by2 = gy + math.sin(ang) * 16
        pygame.draw.rect(self.win, (35, 38, 45), (gx - 4, gy - 3, 8, 6), border_radius=2)
        pygame.draw.line(self.win, (25, 25, 28), (gx, gy), (bx2, by2), 3)
        if d.get("flash", 0) > 0:
            pygame.draw.circle(self.win, (255, 220, 100), (int(bx2), int(by2)), 5)
        # Wyrzutnia rakiet (prawa strona): tuba + 2 widoczne glowice rakiet.
        # Zwisa w dol gdy nie strzela (launcher_ang = +pi/2, jak minigun),
        # celuje w cel przy strzale.
        lang = d.get("launcher_ang", math.pi / 2)
        lx0, ly0 = x + 6, y + 8  # mocowanie wyrzutni
        lx1, ly1 = lx0 + math.cos(lang) * 16, ly0 + math.sin(lang) * 16
        pygame.draw.line(self.win, (70, 75, 60), (lx0, ly0), (lx1, ly1), 7)
        # Glowice na koncu tuby, prostopadle do jej osi
        px_, py_ = -math.sin(lang), math.cos(lang)
        pygame.draw.circle(self.win, (255, 120, 60), (int(lx1 + px_ * 3), int(ly1 + py_ * 3)), 3)
        pygame.draw.circle(self.win, (255, 120, 60), (int(lx1 - px_ * 3), int(ly1 - py_ * 3)), 3)
        # Kamikaze: czerwona poswiata
        if d.get("state") == "kamikaze":
            pygame.draw.circle(self.win, (255, 60, 60), (int(x), int(y)), 26, 2)

    def draw_tesla_bolts(self):
        """Rysuje pioruny Tesli (krotkotrwale)."""
        if not hasattr(self, '_tesla_bolts') or not self._tesla_bolts:
            return
        for bolt in self._tesla_bolts[:]:
            (x1, y1), (x2, y2), timer = bolt
            if not self.paused:
                bolt[2] -= 1
            if bolt[2] <= 0:
                self._tesla_bolts.remove(bolt)
                continue
            # Lamana linia pioruna (na pauzie bez drgania - obraz stoi)
            _jit = 0 if self.paused else 15
            pts = [(x1, y1)]
            segs = 6
            for i in range(1, segs):
                t = i / segs
                mx = x1 + (x2 - x1) * t + random.randint(-_jit, _jit)
                my = y1 + (y2 - y1) * t + random.randint(-_jit, _jit)
                pts.append((mx, my))
            pts.append((x2, y2))
            alpha = int(255 * bolt[2] / 12)
            for w_, col in ((5, (150, 220, 255)), (2, (255, 255, 255))):
                s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                pygame.draw.lines(s, (*col, alpha), False, [(int(x), int(y)) for x, y in pts], w_)
                self.win.blit(s, (0, 0))

    def draw_ability_dock(self):
        """Nowoczesny pasek umiejetnosci - wieksze czcionki, hover pop, zywe kolory.
        Pasek NIEWIDOCZNY gdy nie ma zadnej wiezy; pokazuje tylko efekty typow
        wiez, ktore stoja na planszy (np. tylko Wood -> tylko Rapid Fire).
        Rosnie/kurczy sie z liczba posiadanych typow; kolejnosc bez zmian."""
        tower_types = [
            ("Wood", "Rapid Fire", (205, 133, 63)),    # jasny braz
            ("Metal", "Frost Nova", (135, 206, 250)),     # jasny blekit
            ("Gold", "Golden Touch", (255, 215, 0)),    # zloto
            ("Fire", "Meteor", (255, 99, 71)),            # pomidorowy
            ("Blaze", "Armageddon", (218, 112, 214)),     # orchidea
        ]
        # Tylko typy, ktore stoja na planszy (sprzedana/zniszczona ostatnia wieza
        # danego typu usuwa jej slot z paska).
        owned_types = [(tname, aname, color) for tname, aname, color in tower_types
                       if any(type(tw).__name__.startswith(tname) for tw in self.towers)]
        self.ability_slots = []
        if not owned_types:
            return  # zadna wieza -> pasek niewidoczny
        slot_w, slot_h = 130, 80
        gap = 12
        total_w = len(owned_types) * slot_w + (len(owned_types) - 1) * gap
        start_x = self.width // 2 - total_w // 2
        y = self.height - slot_h - 12
        t_now = pygame.time.get_ticks() / 1000.0
        mouse_pos = self._mouse_pos()
        # Wieksze czcionki
        f_name = pygame.font.SysFont("arial", 16, bold=True)
        f_status = pygame.font.SysFont("arial", 14, bold=True)
        f_type = pygame.font.SysFont("arial", 12)

        for i, (tname, aname, color) in enumerate(owned_types):
            x = start_x + i * (slot_w + gap)
            rect = pygame.Rect(x, y, slot_w, slot_h)
            self.ability_slots.append((rect, tname))
            # Hover pop effect
            is_hover = rect.collidepoint(mouse_pos)
            scale = 1.12 if is_hover else 1.0
            # Policz gotowe wieze
            ready_count = sum(1 for tw in self.towers
                              if type(tw).__name__.startswith(tname) and tw.ability_cooldown <= 0)
            cooling = None
            for tw in self.towers:
                if type(tw).__name__.startswith(tname) and tw.ability_cooldown > 0:
                    if cooling is None or tw.ability_cooldown < cooling.ability_cooldown:
                        cooling = tw
            has_tower = ready_count > 0 or cooling is not None

            # Rysuj z efektem pop (wiekszy gdy hover)
            draw_w, draw_h = int(slot_w * scale), int(slot_h * scale)
            draw_x = x - (draw_w - slot_w) // 2
            draw_y = y - (draw_h - slot_h) // 2
            
            bg = pygame.Surface((draw_w, draw_h), pygame.SRCALPHA)
            if ready_count > 0:
                # Pulsowanie gdy gotowe
                pulse = int(20 * math.sin(t_now * 5 + i))
                r, g, b = color
                # Glow (wiekszy przy hover)
                glow_size = 12 if is_hover else 8
                glow = pygame.Surface((draw_w + glow_size*2, draw_h + glow_size*2), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*color, 80 + pulse), glow.get_rect(), border_radius=16)
                self.win.blit(glow, (draw_x - glow_size, draw_y - glow_size))
                # Zywe tlo
                pygame.draw.rect(bg, (r, g, b, 245), bg.get_rect(), border_radius=14)
                # Blysk na gorze
                pygame.draw.rect(bg, (255, 255, 255, 70), (0, 0, draw_w, 24), border_radius=14)
                pygame.draw.rect(bg, (255, 255, 255, 230), bg.get_rect(), 3 if is_hover else 2, border_radius=14)
            elif cooling:
                pygame.draw.rect(bg, (40, 48, 62, 245), bg.get_rect(), border_radius=14)
                pygame.draw.rect(bg, (*color, 120), bg.get_rect(), 2, border_radius=14)
                # Pasek cooldownu na dole
                cd_ratio = cooling.ability_cooldown / cooling.ability_max_cooldown
                bar_w = int((draw_w - 20) * (1 - cd_ratio))
                pygame.draw.rect(bg, (100, 110, 125, 100), (10, draw_h - 12, draw_w - 20, 5), border_radius=3)
                pygame.draw.rect(bg, (*color, 220), (10, draw_h - 12, bar_w, 5), border_radius=3)
            else:
                pygame.draw.rect(bg, (28, 33, 44, 180), bg.get_rect(), border_radius=14)
            self.win.blit(bg, (draw_x, draw_y))

            # Teksty - wieksze i czytelniejsze
            cx = draw_x + draw_w // 2
            t1 = f_name.render(tr(i18n.ABILITY_KEYS[tname]) if tname in i18n.ABILITY_KEYS else aname, True, (255, 255, 255))
            # Cien pod tekstem dla czytelnosci
            shadow = f_name.render(tr(i18n.ABILITY_KEYS[tname]) if tname in i18n.ABILITY_KEYS else aname, True, (0, 0, 0))
            self.win.blit(shadow, (cx - t1.get_width()//2 + 1, draw_y + 9))
            self.win.blit(t1, (cx - t1.get_width()//2, draw_y + 8))
            if ready_count > 0:
                badge = f_status.render(tr("ability.ready", n=ready_count), True, (255, 255, 180))
                bshadow = f_status.render(tr("ability.ready", n=ready_count), True, (0, 0, 0))
                self.win.blit(bshadow, (cx - badge.get_width()//2 + 1, draw_y + 33))
                self.win.blit(badge, (cx - badge.get_width()//2, draw_y + 32))
            elif cooling:
                secs = cooling.ability_cooldown // 60
                t2 = f_status.render(f"{secs}s", True, (200, 200, 200))
                self.win.blit(t2, (cx - t2.get_width()//2, draw_y + 32))
            else:
                t2 = f_type.render(tr("hud.no_tower"), True, (140, 140, 140))
                self.win.blit(t2, (cx - t2.get_width()//2, draw_y + 32))
            t3 = f_type.render(tr(i18n.TOWER_SHORT_KEYS[tname]) if tname in i18n.TOWER_SHORT_KEYS else tname, True, (210, 210, 210))
            self.win.blit(t3, (cx - t3.get_width()//2, draw_y + 54))

    def draw_placement_grid(self, win, mx, my):
        """Warcraft-style: mocny wash + kolo na ziemi. Okrag zasiegu bez zmian."""
        valid = self.is_valid_placement(mx, my)
        col = (0, 255, 0) if valid else (255, 0, 0)
        # Kolo na ziemi pod wieza (footprint) - ten sam kolor co wash
        foot = pygame.Surface((80, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(foot, (*col, 70), foot.get_rect())
        pygame.draw.ellipse(foot, (*col, 200), foot.get_rect(), 2)
        win.blit(foot, (mx - 40, my - 8))
        # Okrag zasiegu w miejscu stawiania (bez zmian - nie ruszamy zasiegu)
        if hasattr(self.moving_object, 'range'):
            rg = self.moving_object.range
            surf = pygame.Surface((rg*2, rg*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (150, 220, 255, 60), (rg, rg), rg, 2)
            win.blit(surf, (mx - rg, my - rg))

    def shop_price(self, tower_name):
        """Cena wiezy w sklepie. Mapuje nazwe klasy (woodenTower) na przycisk (t1).
        Supply Lines: -15%. Trudnosc: juz w cenie przycisku (skalowana przy starcie)."""
        base = self.menu.get_item_cost(tower_shop_names.get(tower_name, tower_name))
        if "supply" in self.tent_upgrades:
            base = int(base * 0.85)
        return base

    def shop_price_for_button(self, btn_name):
        """Cena za przycisk sklepu (t1..t5) - z rabatem Supply Lines."""
        for cls_name, b in tower_shop_names.items():
            if b == btn_name:
                return self.shop_price(cls_name)
        return self.menu.get_item_cost(btn_name)

    def _point_in_poly(self, x, y, poly):
        """Test punkt-w-wielokacie (ray casting)."""
        inside = False
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
                inside = not inside
        return inside

    def _is_grass(self, x, y):
        """Czy punkt (x, y) w strefie stawiania (narysowanej przez gracza)."""
        for zone in self._placement_zones:
            if self._point_in_poly(x, y, zone):
                return True
        return False

    def is_valid_placement(self, x, y):
        """R4: Czy mozna postawic wieze w (x, y)."""
        # Poza mapa / na menu bocznym
        if x < 40 or x > self.width - 200 or y < 40 or y > self.height - 40:
            return False
        # Tylko na trawie
        if not self._is_grass(x, y):
            return False
        # Na drodze (aktualna sciezka wroga z enemies/enemy.py)
        path = [
                     (322, 658), (425, 630), (505, 591), (588, 581),
                     (696, 570), (792, 558), (890, 546), (953, 536),
                     (1034, 523), (1049, 497), (1021, 488), (944, 477),
                     (838, 467), (724, 450), (626, 438), (540, 426),
                     (448, 414), (359, 399), (264, 387), (250, 351)]
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
        # DEBUG: F3 pokazuje stan wewnetrzny
        if getattr(self, '_debug_show', False):
            dbg_font = pygame.font.SysFont("consolas", 14)
            lines = [
                f"wave={self.wave} enemies={len(self.enemies)}",
                f"waiting={self.waiting_for_clear} ship={self.ship.state}",
                f"current_wave_sum={sum(self.current_wave)}",
                f"clear_timer={self._clear_timer}",
            ]
            for i, line in enumerate(lines):
                txt = dbg_font.render(line, True, (255, 255, 0))
                self.win.blit(txt, (10, 120 + i*20))
        # Rzad spojnych "pigulek": fala, zycia, kasa (tla prerenderowane)
        pill_h = self._pill_h
        y = 10
        items = [
            (10, 0, None, tr("hud.wave", n=self.wave + 1)),
            (200, 1, self._lives_icon, str(int(self.display_lives))),
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
        # Przycisk predkosci (prawy gorny rog) - pauza tylko przez ESC
        # Predkosc
        sr = self.speed_btn_rect
        s2 = pygame.Surface((sr.width, sr.height), pygame.SRCALPHA)
        pygame.draw.rect(s2, (8, 18, 38, 190), s2.get_rect(), border_radius=10)
        pygame.draw.rect(s2, (255, 255, 255, 70), s2.get_rect(), 2, border_radius=10)
        self.win.blit(s2, sr)
        label = self.hud_font.render(f"{self.speed}x", True, (255, 255, 255))
        self.win.blit(label, (sr.x + sr.width//2 - label.get_width()//2,
                              sr.y + sr.height//2 - label.get_height()//2))
        # Licznik wrogow biezacej fali (nowoczesny, dynamiczny)
        # Zlicz pozostale: niespawned (current_wave) + zywi na mapie
        remaining = []
        for i in range(len(self.enemy_classes)):
            # Niespawned
            unspawned = self.current_wave[i] if i < len(self.current_wave) else 0
            # Zywi na mapie tego typu
            alive = sum(1 for en in self.enemies 
                       if type(en).__name__ == self.enemy_classes[i].__name__ and not en.dead)
            total = unspawned + alive
            if total > 0:
                remaining.append((i, total))
        # Boss
        boss_alive = any(isinstance(en, Boss) and not en.dead for en in self.enemies)
        has_boss = boss_alive or len(getattr(self, 'pending_bosses', [])) > 0
        
        if remaining or has_boss:
            # Najpierw zloz elementy i zmierz ich PRAWDZIWA szerokosc (ikona +
            # liczba), a dopiero potem narysuj panel DOKLADNIE na miare tresci.
            # Wczesniej panel mial stala szerokosc 85px/element, a tresc byla
            # wezsza (60-70px) - po prawej zostawalo puste, ekstra miejsce.
            font_cnt = pygame.font.SysFont("arial", 15, bold=True)
            items = []
            for i, count in remaining:
                try:
                    enemy_cls = self.enemy_classes[i]
                    temp = enemy_cls()
                    icon = pygame.transform.scale(temp.imgs[0], (32, 32))
                    cnt_label = font_cnt.render(str(count), True, (255, 255, 120))
                    items.append((icon, cnt_label))
                except:
                    pass
            if has_boss:
                try:
                    boss_temp = Boss()
                    boss_icon = pygame.transform.scale(boss_temp.imgs[0], (32, 32))
                    blabel = font_cnt.render(tr("hud.boss"), True, (255, 100, 100))
                    items.append((boss_icon, blabel))
                except:
                    pass
            # Szerokosc: 10 (lewy margines) + suma (36 + szer. liczby + 14 odstep)
            # bez odstepu po ostatnim + 10 (prawy margines).
            if not items:
                # Ikony sie nie zaladowaly - nie rysuj pustego panelu.
                # Panel jest ostatnim blokiem draw_hud, wiec return nic nie pomija.
                return
            panel_w = 10 + sum(36 + lab.get_width() + 14 for _, lab in items) - 14 + 10
            panel_h = 62
            # Z powrotem po lewej, pod wave/lives/cash
            preview_x = 10
            preview_y = 65
            # Nowoczesne tlo - glassmorphism
            s = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            pygame.draw.rect(s, (15, 25, 45, 180), s.get_rect(), border_radius=14)
            pygame.draw.rect(s, (100, 150, 200, 60), s.get_rect(), 2, border_radius=14)
            self.win.blit(s, (preview_x, preview_y))
            # Naglowek "Enemies" - wycentrowany
            font_head = pygame.font.SysFont("arial", 14, bold=True)
            label = font_head.render(tr("hud.enemies"), True, (200, 220, 255))
            self.win.blit(label, (preview_x + panel_w//2 - label.get_width()//2, preview_y + 5))
            # Ikony - liczba OBOK sprite'a, wycentrowana w pionie
            x_off = preview_x + 10
            for icon, cnt_label in items:
                icon_y = preview_y + 20
                self.win.blit(icon, (x_off, icon_y))
                cnt_x = x_off + 36
                cnt_y = icon_y + 16 - cnt_label.get_height() // 2
                self.win.blit(cnt_label, (cnt_x, cnt_y))
                x_off += 36 + cnt_label.get_width() + 14
    def add_tower(self, name):
        x, y = self._mouse_pos()
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
    while True:
        start_menu = StartMenu(1124, 720, pygame.image.load(os.path.join("images", "bg.png")))
        settings = start_menu.run()
        if settings is None:
            break
        g = Game(lives=settings["lives"], money=settings["money"], sound=settings["sound"],
                 difficulty=settings["difficulty"])
        # Teleport endless z menu glownego (pole z numerem fali)
        if settings.get("start_wave"):
            g.setup_endless_jump(settings["start_wave"])
        # run() zwraca "menu" gdy gracz chce wrocic do menu glownego
        if g.run() != "menu":
            break
    pygame.quit()