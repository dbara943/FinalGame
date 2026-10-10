import pygame
import os
from .enemy import Enemy, load_anim

imgs = []
for x in range(20):
    add_str = str(x)
    if x < 10:
        add_str = "0" + add_str
    imgs.append(pygame.transform.scale(pygame.image.load(os.path.join("images/enemies/8", "8_enemies_1_run_0" + add_str + ".png" )), (128, 128)))

die_imgs = load_anim(8, 'die', (128, 128))
hurt_imgs = load_anim(8, 'hurt', (128, 128))

class EvilVillager(Enemy):
    def __init__(self):
        super().__init__()
        self.name = "evilVillager"
        self.money = 80
        self.max_health = 95
        self.velocity = 1.8
        self.health = self.max_health
        self.imgs = imgs
        self.die_imgs = die_imgs
        self.hurt_imgs = hurt_imgs