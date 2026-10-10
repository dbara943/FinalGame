import pygame
import os
from .enemy import Enemy, load_anim

imgs = []
for x in range(20):
    add_str = str(x)
    if x < 10:
        add_str = "0" + add_str
    imgs.append(pygame.transform.scale(pygame.image.load(os.path.join("images/enemies/6", "6_enemies_1_run_0" + add_str + ".png" )), (64, 64)))

die_imgs = load_anim(6, 'die', (64, 64))
hurt_imgs = load_anim(6, 'hurt', (64, 64))

class Impostor(Enemy):
    def __init__(self):
        super().__init__()
        self.name = "impostor"
        self.money = 20
        self.max_health = 30
        self.velocity = 3.0
        self.health = self.max_health
        self.imgs = imgs
        self.die_imgs = die_imgs
        self.hurt_imgs = hurt_imgs