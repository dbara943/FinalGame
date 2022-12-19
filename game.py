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
import time
import random
pygame.font.init()

lives_img = pygame.image.load(os.path.join("images", "heart.png"))
money_img = pygame.image.load(os.path.join("images", "money.png"))

class Game:
    def __init__(self):
        self.width = 1124
        self.height = 720
        self.win = pygame.display.set_mode((self.width, self.height))
        self.enemies = [Forkman()]
        self.towers = [BlazeTower(750, 500), FireTower(500, 500)]
        self.lives = 10
        self.money = 1000
        self.bg = pygame.image.load(os.path.join("images", "bg.png"))
        self.bg = pygame.transform.scale(self.bg, (self.width, self.height))
        self.timer = time.time()
        self.life_font = pygame.font.SysFont("arial", 30)
        self.money_font = pygame.font.SysFont("arial", 30)

        
    def run(self):
        run = True
        clock = pygame.time.Clock()
        
        while run:
            if time.time() - self.timer >= random.randrange(1, 5):
                self.timer = time.time()
                self.enemies.append(random.choice([Forkman(), Swordman(), Knight(), Goblin(), Cyclop(), Impostor(), Ogre(), EvilVillager()]))
            clock.tick(100)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    
                pos = pygame.mouse.get_pos()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pass
            #loop through enemies
            to_del = []
            for en in self.enemies:
                if en.x <= 285 and en.y <= 400: 
                    to_del.append(en)
                    
            #delete all enemies off the screen
            for d in to_del:
                self.lives -=1
                print(self.lives)
                self.enemies.remove(d)
                
            for tw in self.towers:
                tw.attack(self.enemies)    
            
            # lose condition
            if self.lives <= 0:
                print("You lose")    
                run = False
                
            self.draw()
        pygame.quit
        
    def draw(self):
        self.win.blit(self.bg, (0,0))
        
        #draw towers
        for tw in self.towers:
            tw.draw(self.win)
            
        #draw enemies 
        for en in self.enemies:
            en.draw(self.win)    
        
        #draw lives
        text_lives = self.life_font.render(str(self.lives), 1, (0,0,0))
        life = pygame.transform.scale(lives_img,(32, 32))
        start_x = self.width - life.get_width() - 10
        
        self.win.blit(text_lives, (start_x - text_lives.get_width() - 5, 10)) 
        self.win.blit(life, (start_x, 10)) 
        
        #draw cash
        text_money = self.money_font.render(str(self.money), 1, (0,0,0))
        money = pygame.transform.scale(money_img,(32, 32))
        start_x = self.width - money.get_width() - 10
        
        self.win.blit(text_money, (start_x - text_money.get_width() - 5, 50))   
        self.win.blit(money, (start_x, 50)) 
        pygame.display.update()
        
    def draw_menu(self):
        pass
    
g = Game()
g.run()