import pygame
import os
from .enemy import Enemy, load_anim

imgs = []
for x in range(20):
    add_str = str(x)
    if x < 10:
        add_str = "0" + add_str
    imgs.append(pygame.transform.scale(pygame.image.load(os.path.join("images/enemies/8", "8_enemies_1_run_0" + add_str + ".png" )), (160, 160)))

die_imgs = load_anim(8, 'die', (160, 160))
hurt_imgs = load_anim(8, 'hurt', (160, 160))

class Boss(Enemy):
    """Boss pojawiajacy sie co 4 fale. Bardzo wytrzymaly, wolny, wysoka nagroda."""
    def __init__(self):
        super().__init__()
        self.name = "boss"
        self.money = 150
        self.max_health = 600
        self.health = self.max_health
        self.velocity = 1.5
        self.imgs = imgs
        self.die_imgs = die_imgs
        self.hurt_imgs = hurt_imgs
