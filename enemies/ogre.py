import pygame
import os
from .enemy import Enemy

imgs = []
for x in range(20):
    add_str = str(x)
    if x < 10:
        add_str = "0" + add_str
    imgs.append(pygame.transform.scale(pygame.image.load(os.path.join("images/enemies/7", "7_enemies_1_run_0" + add_str + ".png" )), (96, 96)))
    00
class Ogre(Enemy):
    def __init__(self):
        super().__init__()
        self.max_health = 1
        self.health = self.max_health
        self.imgs = imgs