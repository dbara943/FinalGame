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
from towers.archerTower import ArcherTowerLong
import time
import random

class Game:
    def __init__(self):
        self.width = 1024
        self.height = 720
        self.win = pygame.display.set_mode((self.width, self.height))
        self.enemies = [Forkman(), Swordman(), Knight(), Goblin(), Cyclop(), Impostor(), Ogre(), EvilVillager()]
        self.towers = [ArcherTowerLong(750, 500), ArcherTowerLong(500, 500), ArcherTowerLong(250, 500)]
        self.progress = 0
        self.money = 1000
        self.bg = pygame.image.load(os.path.join("images", "bg.png"))
        self.bg = pygame.transform.scale(self.bg, (self.width, self.height))
        self.timer = time.time()
        
    def run(self):
        run = True
        clock = pygame.time.Clock()
        
        while run:
            if time.time() - self.timer >= random.randrange(1,3):
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
                if en.x < -15: 
                    to_del.append(en)
                    
                    
            #delete all enemies from the screen
            for d in to_del:
                self.enemies.remove(d)
                
            for tw in self.towers:
                tw.attack(self.enemies)    
                
            self.draw()
        pygame.quit
        
    def draw(self):
        self.win.blit(self.bg, (0,0))
        
        #draw enemies 
        for en in self.enemies:
            en.draw(self.win)
        
        #draw towers
        for tw in self.towers:
            tw.draw(self.win)
        pygame.display.update()
        
g = Game()
g.run()