import pygame
import os
from enemies.forkman import Forkman
from enemies.swordman import Swordman
from enemies.knight import Knight
from enemies.goblin import Goblin
from enemies.cyclop import Cyclop
from enemies.impostor import Impostor
from enemies.ogre import Ogre
from enemies.evilVillager import EvilVillager
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
    [50,0,0,0,0,0,0,0],
    [40,10,0,0,0,0,0,0],
    [30,20,0,0,0,0,0,0],
    [20,20,10,0,0,0,0,0],
    [10,10,20,10,0,0,0,0],
    [5,5,20,10,10,0,0,0],
    [0,0,10,20,20,0,0,0],
    [0,0,0,0,20,20,10,0],
    [0,10,15,15,20,15,35,2],
    [20,20,30,40,50,60,70,25],
    [20,20,30,40,50,60,70,25],
    [20,20,30,40,50,60,70,25],
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
        self.win = pygame.display.set_mode((self.width, self.height))
        self.enemies = []
        self.towers = []
        self.lives = lives
        self.money = money
        self.sound = sound
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
                self.wave += 1
                self.money += self.wave * 100
                self.current_wave = waves[self.wave][:]
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
                if event.type == pygame.MOUSEBUTTONDOWN:
                    
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
            to_del = []
            for en in self.enemies:
                if en.reached_end:
                    to_del.append(en)

            for d in to_del:
                sound_1.play()
                self.lives -= 1
                self.enemies.remove(d)

            for tw in self.towers:
                self.money += tw.attack(self.enemies)

            if self.lives <= 0:
                self.show_end_screen(False)
                run = False
            elif self.won:
                self.show_end_screen(True)
                run = False

            self.draw()
        pygame.quit()

    def show_end_screen(self, won):
        big_font = pygame.font.SysFont("arial", 70)
        small_font = pygame.font.SysFont("arial", 30)
        title = "YOU WIN! The island is saved!" if won else "YOU LOSE! The monsters broke through!"
        color = (60, 200, 90) if won else (220, 60, 60)
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
            self.draw()
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            self.win.blit(overlay, (0, 0))
            text = big_font.render(title, 1, color)
            self.win.blit(text, (self.width // 2 - text.get_width() // 2, self.height // 2 - 60))
            sub = small_font.render("Wave reached: " + str(self.wave + 1) + " / " + str(len(waves)), 1, (255, 255, 255))
            self.win.blit(sub, (self.width // 2 - sub.get_width() // 2, self.height // 2 + 20))
            hint = small_font.render("Click anywhere to quit", 1, (180, 180, 180))
            self.win.blit(hint, (self.width // 2 - hint.get_width() // 2, self.height // 2 + 70))
            pygame.display.update()
        
    def draw(self):
        self.win.blit(self.bg, (0,0))
        self.ship.draw(self.win)
        for tw in self.towers:
            tw.draw(self.win)
        if self.moving_object:
            self.moving_object.draw(self.win)
        for en in self.enemies:
            en.draw(self.win)    
        
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