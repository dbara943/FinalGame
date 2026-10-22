"""Tresc ekranu "How to Play" - wspoldzielona przez menu glowne i nakladke
pomocy w grze. Strony jako listy (tekst, styl); style: header / text / dim /
tower / sub. Liczby wiez (ceny, obrazenia, DPS, koszty ulepszen) sa liczone
z klas wiez w momencie rysowania - zawsze zgodne z balansem gry, bez
recznego przepisywania po kazdej zmianie liczb."""
import i18n
from towers.woodenTower import (WoodenTower, MetalTower, GoldenTower,
                                FireTower, BlazeTower, IceTower)
from towers.woodenTower import (tower_imgs1, tower_imgs2, tower_imgs3,
                                tower_imgs4, tower_imgs5, tower_imgs6)

# Zdjecia wiez do ekranu pomocy (renderer rysuje je przy bloku wiezy)
TOWER_SPRITES = {
    "WoodenTower": tower_imgs1,
    "MetalTower": tower_imgs2,
    "GoldenTower": tower_imgs3,
    "FireTower": tower_imgs4,
    "BlazeTower": tower_imgs5,
    "IceTower": tower_imgs6,
}

_CLASSES = [WoodenTower, MetalTower, IceTower, GoldenTower, FireTower, BlazeTower]  # jak sklep: rosnaco po cenie
_RATE = 100 / 60.0  # strzalow na sekunde (cooldown 60 tickow przy 100 Hz)

_ROLE_KEYS = {
    "WoodenTower": "help.role.wood",
    "MetalTower": "help.role.metal",
    "GoldenTower": "help.role.gold",
    "FireTower": "help.role.fire",
    "BlazeTower": "help.role.blaze",
    "IceTower": "help.role.ice",
}
_SHORT = {
    "WoodenTower": "Wood",
    "MetalTower": "Metal",
    "GoldenTower": "Gold",
    "FireTower": "Fire",
    "BlazeTower": "Blaze",
    "IceTower": "Ice",
}
_LINK_KEYS = {
    "WoodenTower": "link.wood",
    "MetalTower": "link.metal",
    "GoldenTower": "link.gold",
    "FireTower": "link.fire",
    "BlazeTower": "link.blaze",
    "IceTower": "link.ice",
}


def _fmt(x):
    return f"{x:.1f}".rstrip("0").rstrip(".")


def pages():
    t = i18n.t
    # --- Strona 1: podstawy i sterowanie ---
    p1 = [
        (t("help.h_basics"), "header"),
        (t("help.l1"), "text"),
        (t("help.l2"), "text"),
        (t("help.l3"), "text"),
        (t("help.l9"), "text"),
        ("", "text"),
        (t("help.h_controls"), "header"),
        (t("help.c1"), "text"),
        (t("help.c2"), "text"),
        (t("help.c3"), "text"),
        (t("help.c4"), "text"),
        (t("help.c5"), "text"),
        (t("help.c6"), "text"),
    ]
    # --- Strony 2-3: wieze, po 3 na strone (liczby z klas; renderer
    # doklada zdjecie wiezy przy jej bloku - linia "tower" niesie jako
    # trzeci element nazwe klasy, zeby renderer wiedzial, ktory sprite) ---
    tower_pages = []
    for chunk in (_CLASSES[:3], _CLASSES[3:]):
        p = [(t("help.h_towers"), "header")]
        for cls in chunk:
            name = i18n.tower_name(cls.__name__, cls.display_name)
            ability = ""
            akey = i18n.ABILITY_KEYS.get(_SHORT.get(cls.__name__, ""))
            if akey:
                ability = t(akey, cls.ability_name)
            dmgs = [cls.base_damage + cls.upgrade_dmg * lv for lv in range(3)]
            dpss = [_fmt(d * _RATE) for d in dmgs]
            p.append((t("help.tower_line", name=name, price=cls.buy_price,
                         ability=ability), "tower", cls.__name__))
            p.append((t("help.stats_line",
                         dmg="/".join(str(d) for d in dmgs),
                         dps="/".join(dpss),
                         range=125,
                         upg=f"{cls.upgrade_costs[0]} / {cls.upgrade_costs[1]}"), "sub"))
            p.append((t(_ROLE_KEYS[cls.__name__]) + " " +
                       t(_LINK_KEYS[cls.__name__]), "sub"))
        tower_pages.append(p)
    tower_pages[1].append(("", "text"))
    tower_pages[1].append((t("help.tower_note"), "dim"))
    # --- Strona 3: endless i reszta zasad ---
    p3 = [
        (t("help.h_endless"), "header"),
        (t("help.e1"), "text"),
        (t("help.e2"), "text"),
        (t("help.e3"), "text"),
        (t("help.e4"), "text"),
        (t("help.e5"), "text"),
        (t("help.e6"), "text"),
        (t("help.e8"), "text"),
        ("", "text"),
        (t("help.e7"), "dim"),
    ]
    return [p1] + tower_pages + [p3]
