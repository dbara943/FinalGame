# Scena diagnostyczna grafik (naprawa macOS, runda 3; sonda rundy 4).
#
# Ekran dostepny klawiszem F9 z menu glownego. Renderuje na JEDNYM
# ekranie wszystkie podejrzane sciezki rysowania (zywy wrog, trup
# w 3 stadiach fade, trup elity, tekst sklepu z cache, chmura nad
# pigulka HUD, czasteczki) i zapisuje log tekstowy + zrzut ekranu
# do katalogu domowego uzytkownika:
#   ~/island_diag.log, ~/island_diag.png
# Jedno wcisniecie F9 na prawdziwym Macu daje zdjecie ekranu ORAZ
# plik z formatami powierzchni i statystykami alfy - bez tego rundy
# 1-2 naprawialy objawy "na czuja", patrzac tylko na zdjecia.
# Scena niczego nie zmienia w rozgrywce; F9 nie jest reklamowane
# w zadnym UI gry.

import os
import sys
import platform
from datetime import datetime

import pygame

import gui_theme as theme
from menu.menu import render_text, blit_text
from enemies.forkman import Forkman
from effects.particles import ParticleSystem

_LOG_PATH = os.path.join(os.path.expanduser("~"), "island_diag.log")
_PNG_PATH = os.path.join(os.path.expanduser("~"), "island_diag.png")

_SWATCH = (64, 62, 74)
_BG = (24, 19, 13)
_LABEL = (245, 236, 214)


def _alpha_stats(surf):
    """(min, max, liczba unikalnych) kanalu alfa, probkowane."""
    w, h = surf.get_size()
    step = 1
    while (w // step) * (h // step) > 20000 and step < 64:
        step *= 2
    vals = set()
    mn, mx = 255, 0
    for x in range(0, w, step):
        for y in range(0, h, step):
            a = surf.get_at((x, y)).a
            vals.add(a)
            if a < mn:
                mn = a
            if a > mx:
                mx = a
    return mn, mx, len(vals)


def _report(name, surf):
    """Jedna sekcja logu: format powierzchni + statystyki alfy."""
    try:
        m = surf.get_masks()
        flags = surf.get_flags()
        mn, mx, uniq = _alpha_stats(surf)
        corner = surf.get_at((0, 0))
        center = surf.get_at((surf.get_width() // 2, surf.get_height() // 2))
        return (f"[{name}] size={surf.get_width()}x{surf.get_height()} "
                f"bitsize={surf.get_bitsize()} "
                f"masks=(r={m[0]},g={m[1]},b={m[2]},a={m[3]}) "
                f"SRCALPHA={'yes' if flags & pygame.SRCALPHA else 'no'} "
                f"get_alpha()={surf.get_alpha()} "
                f"alpha min={mn} max={mx} unique={uniq} "
                f"px(0,0)=({corner.r},{corner.g},{corner.b},{corner.a}) "
                f"px(center)=({center.r},{center.g},{center.b},{center.a})")
    except Exception as e:
        return f"[{name}] <report failed: {e}>"


def _probes():
    """Buduje powierzchnie testowe DOKLADNIE produkcyjnymi sciezkami.
    Zwraca (lista (etykieta, powierzchnia), slownik do logu)."""
    f = Forkman()
    die = f.die_imgs[-1]
    elite = Forkman()
    elite.make_elite()
    edie = elite.die_imgs[-1]

    font = pygame.font.SysFont("arial", 20, bold=True)
    raw_text = font.render("Wieża Lodowa", True, (245, 236, 214))
    cached_text = render_text(font, "Wieża Lodowa", (245, 236, 214))

    panel = pygame.Surface((520, 190), pygame.SRCALPHA)
    pbg = theme.wood_panel(520, 190, radius=12).copy()
    pbg.set_alpha(246)
    panel.blit(pbg, (0, 0))
    blit_text(panel, font, "Wieża Lodowa", (245, 236, 214), 24, 24)
    blit_text(panel, font, "Złota Wieża   750", (245, 236, 214), 24, 64)
    panel_a = panel
    panel_a.set_alpha(150)
    panel_b = pygame.Surface((520, 190), pygame.SRCALPHA)
    pbg2 = theme.wood_panel(520, 190, radius=12).copy()
    pbg2.set_alpha(246)
    panel_b.blit(pbg2, (0, 0))
    blit_text(panel_b, font, "Wieża Lodowa", (245, 236, 214), 24, 24)
    blit_text(panel_b, font, "Złota Wieża   750", (245, 236, 214), 24, 64)

    overlay = pygame.Surface((520, 130), pygame.SRCALPHA)
    for ox in (-20, 0, 20):
        pygame.draw.circle(overlay, (255, 255, 255, 90),
                           (110 + ox, 62), 20)

    ps = ParticleSystem()
    ps.burst(60, 60, (255, 200, 60), count=6, speed=1, life=60, size=6)
    ps.burst(120, 60, (120, 200, 255), count=6, speed=1, life=60, size=4)

    items = [
        ("1 LIVE", f.imgs[0]),
        ("2 CORPSE 255", theme.fade_copy(die, 255)),
        ("3 CORPSE 128", theme.fade_copy(die, 128)),
        ("4 CORPSE 40", theme.fade_copy(die, 40)),
        ("5 ELITE 128", theme.fade_copy(edie, 128)),
    ]
    log_surfaces = [
        ("live frame (production load)", f.imgs[0]),
        ("corpse frame as stored", die),
        ("corpse fade_copy 255", items[1][1]),
        ("corpse fade_copy 128", items[2][1]),
        ("corpse fade_copy 40", items[3][1]),
        ("elite corpse frame as stored", edie),
        ("elite corpse fade_copy 128", items[4][1]),
        ("text font.render RAW", raw_text),
        ("text render_text cache entry", cached_text),
        ("shop panel replica A (set_alpha 150)", panel_a),
        ("shop panel replica B (no set_alpha)", panel_b),
        ("cloud overlay SRCALPHA", overlay),
    ]
    extra = {"panels": (panel_a, panel_b), "overlay": overlay, "ps": ps}
    return items, log_surfaces, extra


def draw_diag(win):
    """Rysuje scene diagnostyczna na powierzchni displaya `win`."""
    items, _log_surfaces, extra = _probes()
    canvas = pygame.Surface((1124, 720))
    canvas.fill(_BG)
    font_t = pygame.font.SysFont("arial", 26, bold=True)
    font_l = pygame.font.SysFont("arial", 15, bold=True)
    title = font_t.render("ISLAND DEFENDERS - DIAGNOSTIC (F9)",
                          True, (255, 210, 63))
    canvas.blit(title, (20, 14))
    sub = font_l.render("ESC / F9 / click = close    log: ~/island_diag.log",
                        True, _LABEL)
    canvas.blit(sub, (20, 48))

    # Rząd 1: wrogowie i trupy na szarych polach
    for i, (label, surf) in enumerate(items):
        x = 20 + i * 218
        pygame.draw.rect(canvas, _SWATCH, (x, 76, 200, 200))
        canvas.blit(surf, (x + 100 - surf.get_width() // 2,
                           176 - surf.get_height() // 2))
        lbl = font_l.render(label, True, _LABEL)
        canvas.blit(lbl, (x + 100 - lbl.get_width() // 2, 282))
    # Rząd 2: repliki panelu sklepu
    panel_a, panel_b = extra["panels"]
    canvas.blit(panel_a, (20, 330))
    canvas.blit(panel_b, (584, 330))
    for x, txt in ((20, "7 SHOP TEXT A (set_alpha 150)"),
                   (584, "8 SHOP TEXT B (bez set_alpha)")):
        lbl = font_l.render(txt, True, _LABEL)
        canvas.blit(lbl, (x + 4, 524))

    # Rząd 3: chmura nad pigulka HUD + czasteczki + info
    pill = theme.wood_panel(180, 44, radius=22, corners=False).copy()
    pill.set_alpha(222)
    pygame.draw.rect(canvas, _SWATCH, (20, 556, 520, 130))
    canvas.blit(pill, (44, 596))
    heart = font_l.render("LIVES 12", True, (255, 120, 120))
    canvas.blit(heart, (70, 610))
    canvas.blit(extra["overlay"], (20, 556))
    lbl = font_l.render("9 CLOUD over HUD pill", True, _LABEL)
    canvas.blit(lbl, (24, 690 - 28))

    ps = extra["ps"]
    pygame.draw.rect(canvas, _SWATCH, (584, 556, 250, 130))
    ptmp = pygame.Surface((250, 130), pygame.SRCALPHA)
    ps.draw(ptmp)
    canvas.blit(ptmp, (584, 556))
    lbl = font_l.render("10 PARTICLES", True, _LABEL)
    canvas.blit(lbl, (588, 690 - 28))

    info = [
        f"set_mode calls: {theme.set_mode_call_count()}   "
        f"display generation: {theme.display_generation()}",
        f"platform: {sys.platform}",
    ]
    for i, line in enumerate(info):
        t = font_l.render(line, True, _LABEL)
        canvas.blit(t, (854, 580 + i * 22))

    # Skalowanie do rzeczywistego rozmiaru displaya (menu = natywna rozdz.)
    if win.get_size() != canvas.get_size():
        win.blit(pygame.transform.smoothscale(canvas, win.get_size()), (0, 0))
    else:
        win.blit(canvas, (0, 0))
    return canvas


def write_diag_files(win):
    """Rysuje scene, zapisuje island_diag.png i island_diag.log
    do katalogu domowego. Wolane przy otwarciu ekranu F9."""
    _items, log_surfaces, extra = _probes()
    draw_diag(win)
    pygame.display.flip()
    lines = []
    lines.append("Island Defenders - diagnostic log (macOS graphics, round 4)")
    lines.append(f"time: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"sys.platform: {sys.platform}")
    lines.append(f"platform: {platform.platform()}")
    try:
        lines.append(f"pygame: {pygame.version.ver}  SDL: "
                     f"{'.'.join(str(v) for v in pygame.get_sdl_version())}")
    except Exception as e:
        lines.append(f"pygame/SDL version: <unavailable: {e}>")
    lines.append(f"set_mode calls since process start: "
                 f"{theme.set_mode_call_count()}")
    lines.append(f"display generation: {theme.display_generation()}")
    disp = pygame.display.get_surface()
    if disp is not None:
        lines.append(_report("DISPLAY surface", disp))
    lines.append("--- probe surfaces ---")
    for name, surf in log_surfaces:
        lines.append(_report(name, surf))
    # Runda 4: dowod czyszczenia RGB pod alfa == 0. "As stored" to
    # produkcyjna klatka trupa elity po wszystkich hookach sanitize;
    # replika polysku odtwarza historyczne zabrudzenie filtra zlotego
    # (BLEND_ADD (40,25,0) - dokladnie ten kolor widac bylo w logu
    # rundy 3 jako (40,25,0,0)), zeby log pokazal przed/po na tej
    # samej powierzchni: przed = N brudnych pikseli, po = 0.
    lines.append("--- round 4: sanitize probe ---")
    try:
        _edie = [s for n, s in log_surfaces
                 if n == "elite corpse frame as stored"][0]
        lines.append("[elite corpse frame as stored] "
                     f"dirty px = {theme.dirty_pixel_count(_edie)}")
        _replica = _edie.copy()
        _shine = pygame.Surface(_replica.get_size())
        _shine.fill((40, 25, 0))
        _replica.blit(_shine, (0, 0), special_flags=pygame.BLEND_ADD)
        lines.append("[gold-shine replica - pre-fix dirt] "
                     "dirty px before sanitize = "
                     f"{theme.dirty_pixel_count(_replica)}")
        theme.sanitize_alpha(_replica)
        lines.append("[gold-shine replica after sanitize] "
                     f"dirty px = {theme.dirty_pixel_count(_replica)}")
    except Exception as e:
        lines.append(f"[sanitize probe] <failed: {e}>")
    try:
        with open(_LOG_PATH, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    except Exception:
        pass
    try:
        pygame.image.save(win, _PNG_PATH)
    except Exception:
        pass
    return _LOG_PATH, _PNG_PATH
