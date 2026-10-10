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
attack_imgs = load_anim(8, 'attack', (160, 160))

class Boss(Enemy):
    """Boss pojawiajacy sie co 4 fale. Bardzo wytrzymaly, wolny, wysoka nagroda.
    Fala 10: wzmocniony (1000 HP, enrage, przywoluje miniony)."""
    def __init__(self, final=False):
        super().__init__()
        self.name = "boss"
        self.money = 150 if not final else 400
        self.max_health = 400 if not final else 1000
        self.health = self.max_health
        self.velocity = 1.5
        self.base_velocity = 1.5
        self.final = final  # Boss finalny z fali 10
        self.enraged = False
        self.summoned_at = set()  # progi HP przy ktorych przywolal miniony
        self.imgs = imgs
        self.die_imgs = die_imgs
        self.hurt_imgs = hurt_imgs
        self.attack_imgs = attack_imgs
        self._roar_played = False

    def update(self):
        super().update()
        if self.final and not self.dying and not self.dead:
            ratio = self.health / self.max_health
            # Enrage przy 50% HP: +80% predkosci + ryk
            if ratio <= 0.5 and not self.enraged:
                self.enraged = True
                self.velocity = self.base_velocity * 1.8
                # Ryk - flaga do odegrania w game.py
                self._roar_request = True
            # Przywolywanie minionow przy 75%/50%/25%
            for threshold in (0.75, 0.5, 0.25):
                if ratio <= threshold and threshold not in self.summoned_at:
                    self.summoned_at.add(threshold)
                    self._summon_request = True

    def get_roar_request(self):
        if getattr(self, '_roar_request', False):
            self._roar_request = False
            return True
        return False

    def get_summon_request(self):
        """Zwraca True raz gdy boss chce przywolac miniony."""
        if getattr(self, '_summon_request', False):
            self._summon_request = False
            return True
        return False
