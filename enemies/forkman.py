import pygame
import os
from .enemy import Enemy

class Forkman(Enemy):
    def __init__(self):
        super().__init__()
        self.imgs = []
        self.max_health = 1
        self.health = self.max_health
        
        for x in range(20):
            add_str = str(x)
            if x < 10:
                add_str = "0" + add_str
            self.imgs.append(pygame.transform.scale(pygame.image.load(os.path.join("images/enemies/1", "1_enemies_1_run_0" + add_str + ".png" )), (64, 64)))
