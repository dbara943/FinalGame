import pygame
import os
from .enemy import Enemy

imgs = []
for x in range(20):
    add_str = str(x)
    if x < 10:
        add_str = "0" + add_str
    imgs.append(pygame.transform.scale(pygame.image.load(os.path.join("images/enemies/8", "8_enemies_1_run_0" + add_str + ".png" )), (128, 128)))

class EvilVillager(Enemy):
    def __init__(self):
        super().__init__()
        self.name = "evilVillager"
        self.money = 80
        self.max_health = 80
        self.health = self.max_health
        self.imgs = imgs