import pygame
import os
from .enemy import Enemy, load_anim

imgs = []
for x in range(20):
    add_str = str(x)
    if x < 10:
        add_str = "0" + add_str
    imgs.append(pygame.transform.scale(pygame.image.load(os.path.join("images/enemies/7", "7_enemies_1_run_0" + add_str + ".png" )), (96, 96)))
    00
die_imgs = load_anim(7, 'die', (96, 96))
hurt_imgs = load_anim(7, 'hurt', (96, 96))

class Ogre(Enemy):
    def __init__(self):
        super().__init__()
        self.enemy = "ogre"
        self.money = 50
        self.max_health = 60
        self.velocity = 2.0
        self.health = self.max_health
        self.imgs = imgs
        self.die_imgs = die_imgs
        self.hurt_imgs = hurt_imgs