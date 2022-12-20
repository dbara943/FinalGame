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
from towers.woodenTower import WoodenTower, MetalTower, GoldenTower, FireTower, BlazeTower
from menu.menu import VerticalMenu
import time
import random
pygame.font.init()

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
    [20,20,30,40,50,60,70,5],
    [0,0,0,0,0,0,0,0],
]
pygame.mixer.init()
music = pygame.mixer.music.load(os.path.join("sounds", "music.mp3"))
sound_1 = pygame.mixer.Sound("sounds/1.mp3")
sound_2 = pygame.mixer.Sound("sounds/2.mp3")
sound_3 = pygame.mixer.Sound("sounds/3.mp3")
sound_4 = pygame.mixer.Sound("sounds/4.mp3")
sound_5 = pygame.mixer.Sound("sounds/5.mp3")

class Game:
    def __init__(self):
        self.width = 1124
        self.height = 720
        self.win = pygame.display.set_mode((self.width, self.height))
        self.enemies = []
        self.towers = []
        self.lives = 20
        self.money = 200
        self.bg = pygame.image.load(os.path.join("images", "bg.png"))
        self.bg = pygame.transform.scale(self.bg, (self.width, self.height))
        self.timer = time.time()
        self.life_font = pygame.font.SysFont("arial", 30)
        self.money_font = pygame.font.SysFont("arial", 30)
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
        
    def gen_enemies(self):
        if sum(self.current_wave) == 0:
                self.wave += 1
                self.money += self.wave * 100
                self.current_wave = waves[self.wave]
        else:
           wave_enemies = [Forkman(), Swordman(), Knight(), Goblin(), Cyclop(), Impostor(), Ogre(), EvilVillager()]
           for x in range(len(self.current_wave)): 
                if self.current_wave[x] != 0:
                    self.enemies.append(wave_enemies[x])
                    self.current_wave[x] = self.current_wave[x] - 1
                    break
    def run(self):
        pygame.mixer.music.play(loops=-1)
        run = True
        clock = pygame.time.Clock()
        while run:
            clock.tick(100)
            
            if time.time() - self.timer >= random.randrange(1, 5)/2:
                    self.timer = time.time()
                    self.gen_enemies()
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
                                if self.money >= cost:
                                    self.money -= cost
                                    self.selected_tower.upgrade()
                    if not (btn_clicked):    
                        for tw in self.towers:
                            if tw.click(pos[0], pos[1]):
                                tw.selected = True
                                self.selected_tower = tw
                            else:
                                tw.selected = False     
            to_del = []
            for en in self.enemies:
                if en.x <= 300 and en.y <= 375: 
                    to_del.append(en)

            for d in to_del:
                sound_1.play()
                self.lives -=1
                print(self.lives)
                self.enemies.remove(d)
                
            for tw in self.towers:
                self.money += tw.attack(self.enemies)    

            if self.lives <= 0:
                print("You lose!")    
                run = False
            if self.wave >= 10:
                print("You win!")
                
            self.draw()
        pygame.quit
        
    def draw(self):
        self.win.blit(self.bg, (0,0))
        for tw in self.towers:
            tw.draw(self.win)
        if self.moving_object:
            self.moving_object.draw(self.win)
        for en in self.enemies:
            en.draw(self.win)    
        
        self.menu.draw(self.win)
        text_lives = self.life_font.render(str(self.lives), 1, (0,0,0))
        life = pygame.transform.scale(lives_img,(32, 32))
        start_x = self.width - life.get_width() - 10
        
        self.win.blit(text_lives, (start_x - text_lives.get_width() - 5, 10)) 
        self.win.blit(life, (start_x, 10)) 
        
        text_money = self.money_font.render(str(self.money), 1, (0,0,0))
        money = pygame.transform.scale(money_img,(32, 32))
        start_x = self.width - money.get_width() - 10
        
        self.win.blit(text_money, (start_x - text_money.get_width() - 5, 50))   
        self.win.blit(money, (start_x, 50)) 
        
        self.win.blit(wave_bg,(10, 10))
        text = self.life_font.render("Wave #" + str(self.wave), 1, (0,0,0))
        self.win.blit(text, (10 + wave_bg.get_width()/2 - text.get_width()/2, 25))
        
        pygame.display.update()
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

    
g = Game()
g.run()