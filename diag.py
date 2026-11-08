# Scena diagnostyczna grafik (naprawa macOS, runda 3; sonda rundy 4;
# strona 2 dokladana w rundzie 5).
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
_PNG2_PATH = os.path.join(os.path.expanduser("~"), "island_diag2.png")
_PNG3_PATH = os.path.join(os.path.expanduser("~"), "island_diag3.png")

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


# ---------------------------------------------------------------------
# RUNDA 5 (po retescie Weroniki, 8.11.2026): strona 1 przeszla czysta -
# sanitize_alpha dziala, a scena F9 renderuje sie poprawnie. Gra dalej
# psuje sie w trzech miejscach, ktorych sondy strony 1 NIE pokrywaja:
# (1) zywe elity wygladaja na polprzezroczyste, (2) ikony wiez w sklepie
# maja czarne tla, (3) pigulki HUD (fala/zycia/zloto) maja czarne konce.
# Strona 2 rysuje PRAWDZIWE sciezki gry (prawdziwy VerticalMenu.draw,
# prawdziwa kompozycja pigulek z draw_hud, zywa klatka elity) - kazda
# DWA razy: bezposrednio (jak strona 1) oraz przez skonwertowany bufor
# .convert() 1:1 (jak Game.win, na ktory gra rysuje kazda klatke).
# Roznica miedzy wersjami na zrzucie wskaże winny etap potoku.
# HUD ma i trzeci wariant: te same surowe napisy po sanitize_alpha -
# font.render zostawia kolor czcionki pod alfa 0 (u nas 740 z 1178 px
# probki), a draw_hud jako jedyna sciezka w grze tego nie czysci;
# jesli wariant 19 wyglada czysto, a 17/18 nie - naprawa jest znana.
# ---------------------------------------------------------------------

def _shop_icon_r5(tower_file, proj_file):
    """DOKLADNA replika budowniczego ikon sklepu z Game.__init__."""
    s = pygame.Surface((46, 46), pygame.SRCALPHA)
    t = pygame.transform.smoothscale(
        pygame.image.load(os.path.join("images", "turrets", "towers",
                                       tower_file)), (46, 46))
    s.blit(t, (0, 0))
    p = pygame.transform.smoothscale(
        pygame.image.load(os.path.join("images", "turrets", "projectiles",
                                       proj_file)), (20, 20))
    s.blit(p, (26, 26))
    return s


def _build_shop_panel_r5():
    """Prawdziwy panel sklepu: VerticalMenu z produkcyjnymi ikonami,
    rysowany metoda draw() w stanie spoczynkowym (mysz poza panelem,
    czyli alfa calosci 150 - stan, w ktorym gracz widzi sklep przez
    wiekszosc gry). Zwraca przechwycona powierzchnie panelu."""
    from menu.menu import VerticalMenu
    menu = VerticalMenu(300, 140, pygame.Surface((375, 475)))
    menu.add_btn(_shop_icon_r5("1.png", "2.png"), "t1", 100, damage=1)
    menu.add_btn(_shop_icon_r5("2.png", "1.png"), "t2", 500, damage=3)
    menu.add_btn(_shop_icon_r5("6.png", "6.png"), "t3", 650, damage=2)
    menu.add_btn(_shop_icon_r5("3.png", "3.png"), "t4", 750, damage=5)
    menu.add_btn(_shop_icon_r5("4.png", "4.png"), "t5", 1000, damage=9)
    menu.add_btn(_shop_icon_r5("5.png", "5.png"), "t6", 2000, damage=12)
    cap = pygame.Surface((620, 520), pygame.SRCALPHA)
    menu.draw(cap, mouse_pos=(-999, -999))
    rect = menu.get_rect()  # te same wspolrzedne, w ktorych draw() rysowal na cap
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    panel.blit(cap, (0, 0), rect)
    return panel


def _hud_parts_r5():
    """Elementy rzedu HUD dokladnie jak w Game.draw_hud: pigulki
    wood_panel + set_alpha(222), ikony transform.scale 28x28, napisy
    SUROWYM font.render (draw_hud nie uzywa cache render_text)."""
    pill_h = 44
    pills = []
    for w_ in (180, 130, 150):
        s = theme.wood_panel(w_, pill_h, radius=pill_h // 2,
                             corners=False).copy()
        s.set_alpha(222)
        pills.append(s)
    lives = pygame.image.load(os.path.join("images", "heart.png"))
    money = pygame.image.load(os.path.join("images", "coin.png"))
    lives_icon = pygame.transform.scale(lives, (28, 28))
    money_icon = pygame.transform.scale(money, (28, 28))
    hud_font = pygame.font.SysFont("segoe ui, calibri, arial", 26, bold=True)
    items = [(10, 0, None, "FALA 3"),
             (200, 1, lives_icon, "12"),
             (340, 2, money_icon, "1500")]
    return pill_h, pills, items, hud_font


def _draw_hud_row_r5(base, sanitize_labels):
    """Rysuje rzad pigulek na powierzchni `base` (500x60) tak, jak
    draw_hud rysuje bezposrednio na Game.win: pigulka, ikona i surowy
    napis osobnymi blitami - bez kompozycji posredniej, ktora sama
    czyscila brud spod alfy napisow."""
    pill_h, pills, items, hud_font = _hud_parts_r5()
    raw_label = None
    for x, pi, icon, text in items:
        base.blit(pills[pi], (x, 8))
        w_ = pills[pi].get_width()
        label = hud_font.render(text, True, theme.CREAM)
        if raw_label is None:
            raw_label = label
        if sanitize_labels:
            label = theme.sanitize_alpha(label.copy())
        cy = 8 + pill_h // 2 - label.get_height() // 2
        if icon is None:
            base.blit(label, (x + w_ // 2 - label.get_width() // 2, cy))
        else:
            group_w = icon.get_width() + 8 + label.get_width()
            gx = x + w_ // 2 - group_w // 2
            base.blit(icon, (gx, 8 + pill_h // 2 - icon.get_height() // 2))
            base.blit(label, (gx + icon.get_width() + 8, cy))
    return raw_label


def _build_hud_variants_r5():
    """Trzy warianty rzedu HUD (po 500x60, tlo = pole testowe):
    A) produkcyjny: zwykle Surface, surowe napisy (jak strona 1);
    B) produkcyjny na buforze .convert() (jak Game.win);
    C) jak B, ale napisy po sanitize_alpha - kandydat na naprawe.
    Zwraca (warianty, pigulka, surowy napis, ikona) - tez do logu."""
    _ph, pills, _items, _hf = _hud_parts_r5()
    lives_icon = _items[1][2]
    var_a = pygame.Surface((500, 60))
    var_a.fill(_SWATCH)
    raw_label = _draw_hud_row_r5(var_a, sanitize_labels=False)
    var_b = pygame.Surface((500, 60)).convert()
    var_b.fill(_SWATCH)
    _draw_hud_row_r5(var_b, sanitize_labels=False)
    var_c = pygame.Surface((500, 60)).convert()
    var_c.fill(_SWATCH)
    _draw_hud_row_r5(var_c, sanitize_labels=True)
    return (var_a, var_b, var_c), pills[0], raw_label, lives_icon


def _probes_r5():
    """Powierzchnie rundy 5 + lista powierzchni do logu."""
    f = Forkman()
    elite = Forkman()
    elite.make_elite()
    panel = _build_shop_panel_r5()
    hud_variants, pill, raw_label, lives_icon = _build_hud_variants_r5()
    icon1 = _shop_icon_r5("1.png", "2.png")
    log_surfaces = [
        ("r5 live frame (control)", f.imgs[0]),
        ("r5 ELITE live frame as stored", elite.imgs[0]),
        ("r5 shop icon composite t1", icon1),
        ("r5 shop panel composed (VerticalMenu.draw, alpha 150)", panel),
        ("r5 HUD pill (wood_panel + set_alpha 222)", pill),
        ("r5 HUD raw label (font.render, draw_hud path)", raw_label),
        ("r5 HUD raw label SANITIZED",
         theme.sanitize_alpha(raw_label.copy())),
        ("r5 HUD lives icon (transform.scale 28x28)", lives_icon),
    ]
    return {"normal": f.imgs[0], "elite": elite.imgs[0],
            "panel": panel, "hud": hud_variants}, log_surfaces


def _via_canvas(surf, w, h):
    """Rysuje `surf` wycentrowane na skonwertowanym buforze .convert()
    (format Game.win) wypelnionym kolorem pola testowego - produkcyjny
    etap posredni gry, w odroznieniu od zwyklego Surface strony 1."""
    buf = pygame.Surface((w, h)).convert()
    buf.fill(_SWATCH)
    buf.blit(surf, (w // 2 - surf.get_width() // 2,
                    h // 2 - surf.get_height() // 2))
    return buf


def _direct(surf, w, h):
    """Jak _via_canvas, ale na zwyklym Surface (sciezka strony 1)."""
    base = pygame.Surface((w, h))
    base.fill(_SWATCH)
    base.blit(surf, (w // 2 - surf.get_width() // 2,
                     h // 2 - surf.get_height() // 2))
    return base


def draw_diag_r5(win):
    """Strona 2 sceny F9: prawdziwe sciezki gry, bezposrednio vs przez
    bufor .convert(). Zwraca canvas 1124x720 (jak strona 1)."""
    pr, _log = _probes_r5()
    canvas = pygame.Surface((1124, 720))
    canvas.fill(_BG)
    font_t = pygame.font.SysFont("arial", 26, bold=True)
    font_l = pygame.font.SysFont("arial", 15, bold=True)
    title = font_t.render("ROUND 5 - REAL GAME PATHS (direct vs game buffer)",
                          True, (255, 210, 63))
    canvas.blit(title, (20, 14))

    # Rzad A: zywi wrogowie - kontrola i elita, bezposrednio / przez bufor
    cells = [
        ("11 NORMAL direct", _direct(pr["normal"], 200, 150)),
        ("12 ELITE direct", _direct(pr["elite"], 200, 150)),
        ("13 ELITE via buffer", _via_canvas(pr["elite"], 200, 150)),
        ("14 NORMAL via buffer", _via_canvas(pr["normal"], 200, 150)),
    ]
    for i, (label, surf) in enumerate(cells):
        x = 20 + i * 218
        canvas.blit(surf, (x, 60))
        lbl = font_l.render(label, True, _LABEL)
        canvas.blit(lbl, (x + 100 - lbl.get_width() // 2, 216))

    # Rzad B: prawdziwy panel sklepu (stan alfa 150) - dwie drogi
    panel = pr["panel"]
    pw, ph = panel.get_size()
    canvas.blit(panel, (20, 250))
    pbuf = pygame.Surface((pw, ph)).convert()
    pbuf.fill(_BG)
    pbuf.blit(panel, (0, 0))
    canvas.blit(pbuf, (40 + pw, 250))
    for x, txt in ((20, "15 SHOP PANEL direct"),
                   (40 + pw, "16 SHOP PANEL via buffer")):
        lbl = font_l.render(txt, True, _LABEL)
        canvas.blit(lbl, (x + 4, 250 + ph + 6))

    # Rzad B prawa kolumna: rzad pigulek HUD - trzy warianty z draw_hud
    hud_a, hud_b, hud_c = pr["hud"]
    hx = 1124 - 520
    canvas.blit(hud_a, (hx, 250))
    canvas.blit(hud_b, (hx, 336))
    canvas.blit(hud_c, (hx, 422))
    for y, txt in ((250, "17 HUD production (plain surface)"),
                   (336, "18 HUD production (game buffer)"),
                   (422, "19 HUD sanitized labels (game buffer)")):
        lbl = font_l.render(txt, True, _LABEL)
        canvas.blit(lbl, (hx + 4, y + 62))

    info = font_l.render("Buffer = Surface.convert() jak Game.win; "
                         "17 = zwykle Surface (jak strona 1).",
                         True, _LABEL)
    canvas.blit(info, (hx, 508))

    if win.get_size() != canvas.get_size():
        win.blit(pygame.transform.smoothscale(canvas, win.get_size()), (0, 0))
    else:
        win.blit(canvas, (0, 0))
    return canvas


# ---------------------------------------------------------------------
# RUNDA 7 (po tescie rozgrywki rundy 6): dane sa juz czyste (log rundy 6:
# panel sklepu i pigulka dirty = 0), a scena F9 renderuje sie poprawnie -
# ale W GRZE dalej: (1) sklep nie robi sie polprzezroczysty w spoczynku,
# (2) czarne prostokaty przy rzadku fali/zycia/zlota, (3) sklep zaslania
# menu budynku. Strony 1-2 skladaja sondy na zwyklym canvasie menu;
# gra rysuje na bufor Game.win (.convert(), 1124x720) i prezentuje go
# przez smoothscale do natywnej rozdzielczosci (_present, fullscreen).
# Strona 3 odtwarza DOKLADNIE ten potok: prawdziwy rzad HUD, prawdziwy
# sklep w stanie alfa 150 (mysz daleko) i 255 (mysz na przycisku),
# zywi wrogowie - wszystko na buforze .convert() 1124x720 na tle w paski
# (przezroczystosc widac od razu), a na koncu smoothscale na display
# tym samym wywolaniem co _present(). Jesli strona 3 jest czysta,
# a gra dalej nie - zostaje tylko prezentacja zywego okna (dowod:
# zdjecie telefonem, o ktore prosimy osobno).
# ---------------------------------------------------------------------

def _make_menu_r7(x, y):
    """VerticalMenu z produkcyjnymi ikonami (jak _build_shop_panel_r5,
    ale zwraca samo menu do rysowania na buforze gry)."""
    from menu.menu import VerticalMenu
    menu = VerticalMenu(x, y, pygame.Surface((375, 475)))
    menu.add_btn(_shop_icon_r5("1.png", "2.png"), "t1", 100, damage=1)
    menu.add_btn(_shop_icon_r5("2.png", "1.png"), "t2", 500, damage=3)
    menu.add_btn(_shop_icon_r5("6.png", "6.png"), "t3", 650, damage=2)
    menu.add_btn(_shop_icon_r5("3.png", "3.png"), "t4", 750, damage=5)
    menu.add_btn(_shop_icon_r5("4.png", "4.png"), "t5", 1000, damage=9)
    menu.add_btn(_shop_icon_r5("5.png", "5.png"), "t6", 2000, damage=12)
    return menu


def draw_diag_r7(win):
    """Strona 3: jedna klatka zbudowana jak klatka gry i zaprezentowana
    jak _present() w fullscreen. Rysuje bezposrednio na `win`."""
    gwin = pygame.Surface((1124, 720)).convert()
    # Tlo w paski + jasny pas poziomy: przezroczystosc paneli widac od razu
    for i, x in enumerate(range(0, 1124, 92)):
        pygame.draw.rect(gwin, (96, 116, 74) if i % 2 == 0 else (64, 84, 56),
                         (x, 0, 92, 720))
    pygame.draw.rect(gwin, (206, 186, 128), (0, 300, 1124, 60))
    font_l = pygame.font.SysFont("arial", 15, bold=True)

    def label(text, x, y):
        gwin.blit(render_text(font_l, text, _LABEL), (x, y))

    label("ROUND 7 - REAL GAME PIPELINE (_present)", 520, 14)

    # Rzad HUD: produkcyjna kompozycja draw_hud (pigulki + ikony +
    # napisy czyszczone jak po fixie _hud_text), element po elemencie
    pill_h, pills, items, hud_font = _hud_parts_r5()
    for x, pi, icon, text in items:
        gwin.blit(pills[pi], (x, 10))
        w_ = pills[pi].get_width()
        lab = theme.sanitize_alpha(hud_font.render(text, True, theme.CREAM))
        cy = 10 + pill_h // 2 - lab.get_height() // 2
        if icon is None:
            gwin.blit(lab, (x + w_ // 2 - lab.get_width() // 2, cy))
        else:
            group_w = icon.get_width() + 8 + lab.get_width()
            gx = x + w_ // 2 - group_w // 2
            gwin.blit(icon, (gx, 10 + pill_h // 2 - icon.get_height() // 2))
            gwin.blit(lab, (gx + icon.get_width() + 8, cy))
    label("20 HUD row (game buffer)", 10, 60)

    # Sklep A: stan spoczynkowy (mysz daleko) - produkcyjne alfa 150
    menu_a = _make_menu_r7(100, 285)
    menu_a.draw(gwin, mouse_pos=(-999, -999))
    label("21 SHOP alpha 150", 16, 596)
    # Sklep B: mysz na pierwszym przycisku - produkcyjne alfa 255.
    # Pierwszy przebieg na powierzchnie robocza ustawia geometrie
    # przyciskow, drugi rysuje wlasciwie z kursorem na przycisku.
    menu_b = _make_menu_r7(330, 285)
    scratch = pygame.Surface((620, 620), pygame.SRCALPHA)
    menu_b.draw(scratch, mouse_pos=(-999, -999))
    b0 = menu_b.buttons[0]
    hover = (b0.x + b0.width // 2, b0.y + b0.height // 2)
    menu_b.draw(gwin, mouse_pos=hover)
    label("22 SHOP alpha 255", 246, 596)

    # Panel zlozony wczesniej (alfa wpisana w piksele, bez set_alpha)
    panel = _build_shop_panel_r5()
    gwin.blit(panel, (480, 145))
    label("23 SHOP pre-composed (pixel alpha)", 480, 596)

    # Zywi wrogowie bezposrednio na buforze
    f = Forkman()
    elite = Forkman()
    elite.make_elite()
    gwin.blit(f.imgs[0], (760, 180))
    gwin.blit(elite.imgs[0], (900, 172))
    label("24 NORMAL", 736, 262)
    label("25 ELITE", 896, 262)

    # Prezentacja: DOKLADNIE wywolanie z Game._present() (fullscreen)
    pygame.transform.smoothscale(gwin, win.get_size(), win)
    return gwin


# ---------------------------------------------------------------------
# RUNDA 8: przechwycenie PRAWDZIWEJ klatki gry (F9 w trakcie rozgrywki).
# Strony 1-3 sa czyste nawet na Macu i nawet przez potok _present(),
# a rozgrywka dalej pokazuje objawy - wiec zamiast emulowac gre w menu,
# zapisujemy klatke z wnetrza samej gry: bufor Game.win po zlozeniu
# calej klatki oraz ekran po _present(), plus stan gry i pomiary
# (pigulki uzywane przez biezaca instancje Game, liczba w pelni czarnych
# pikseli w rzedzie HUD i w panelu sklepu na samej klatce).
# Rozstrzyga: win brudny -> winny element kompozycji klatki; win czysty,
# disp brudny -> prezentacja; oba czyste -> zywe okno/kompozytor.
# ---------------------------------------------------------------------

def _black_count(surf, rect):
    """Piksele w pelni kryjace i prawie czarne (r,g,b < 10) w prostokacie."""
    cnt = 0
    x0 = max(0, rect.left)
    y0 = max(0, rect.top)
    x1 = min(surf.get_width(), rect.right)
    y1 = min(surf.get_height(), rect.bottom)
    for yy in range(y0, y1):
        for xx in range(x0, x1):
            r, g, b, a = surf.get_at((xx, yy))
            if a == 255 and r < 10 and g < 10 and b < 10:
                cnt += 1
    return cnt


def capture_game_frame(game):
    """Zapisuje biezaca klatke gry; wywolywane z Game.draw() po
    _present(), gdy gracz nacisnal F9 (flaga _diag_capture_pending)."""
    import datetime
    import glob
    home = os.path.expanduser("~")
    n = len(glob.glob(os.path.join(home, "island_game*_win.png"))) + 1
    win_path = os.path.join(home, "island_game%d_win.png" % n)
    disp_path = os.path.join(home, "island_game%d_disp.png" % n)
    try:
        pygame.image.save(game.win, win_path)
    except Exception:
        pass
    try:
        pygame.image.save(game._screen, disp_path)
    except Exception:
        pass
    lines = []
    lines.append("--- game capture #%d %s ---" % (
        n, datetime.datetime.now().isoformat(timespec="seconds")))
    try:
        mouse = game._mouse_pos()
    except Exception:
        mouse = None
    lines.append(
        "wave=%s lives=%s money=%s mouse=%s building_menu=%s "
        "tent_menu=%s selected_tower=%s enemies=%d" % (
            getattr(game, "wave", None), getattr(game, "lives", None),
            getattr(game, "money", None), mouse,
            getattr(game, "_building_menu_open", None),
            getattr(game, "_tent_menu_open", None),
            getattr(game, "selected_tower", None) is not None,
            len(getattr(game, "enemies", []))))
    for name, surf in (("pill wave", game._pills[0]),
                       ("pill lives", game._pills[1]),
                       ("pill gold", game._pills[2])):
        lines.append(_report("game " + name, surf))
    hud_rect = pygame.Rect(0, 0, 540, 64)
    lines.append("win HUD-row opaque-black px = %d"
                 % _black_count(game.win, hud_rect))
    try:
        shop_rect = game.menu.get_rect()
        lines.append("win shop-panel opaque-black px = %d (rect %s)"
                     % (_black_count(game.win, shop_rect), shop_rect))
    except Exception:
        pass
    try:
        sx = game._screen.get_width() / game.win.get_width()
        sy = game._screen.get_height() / game.win.get_height()
        disp_hud = pygame.Rect(0, 0, int(540 * sx), int(64 * sy))
        lines.append("disp HUD-row opaque-black px = %d"
                     % _black_count(game._screen, disp_hud))
    except Exception:
        pass
    lines.append(_report("game win (full frame buffer)", game.win))
    try:
        with open(os.path.join(home, "island_game.log"), "a",
                  encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    except Exception:
        pass


def write_diag_files(win):
    """Rysuje scene, zapisuje island_diag.png i island_diag.log
    do katalogu domowego. Wolane przy otwarciu ekranu F9."""
    _items, log_surfaces, extra = _probes()
    # Runda 6: zapis DOKLADNIE jak w rundzie 4 - kazda strona prosto
    # z powierzchni displaya. Laczenie stron przez kopie i wspolna
    # powierzchnie (runda 5) na macOS niszczylo kanal alfa pliku -
    # nawet niezmieniona strona 1 wrocila jako czarne prostokaty.
    draw_diag(win)
    pygame.display.flip()
    try:
        pygame.image.save(win, _PNG_PATH)
    except Exception:
        pass
    draw_diag_r5(win)
    pygame.display.flip()
    try:
        pygame.image.save(win, _PNG2_PATH)
    except Exception:
        pass
    gwin_r7 = draw_diag_r7(win)
    pygame.display.flip()
    try:
        pygame.image.save(win, _PNG3_PATH)
    except Exception:
        pass
    lines = []
    lines.append("Island Defenders - diagnostic log (macOS graphics, round 8)")
    lines.append("screenshots: island_diag.png (page 1), "
                 "island_diag2.png (page 2), island_diag3.png (page 3)")
    lines.append(_report("r7 game buffer (.convert 1124x720)", gwin_r7))
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
    # Runda 5: prawdziwe sciezki gry - formaty + brudne piksele powierzchni
    # budowanych produkcyjnym kodem (panel sklepu, pigulki HUD, zywa elita).
    lines.append("--- round 5: real game paths ---")
    try:
        _pr5, r5_surfaces = _probes_r5()
        for name, surf in r5_surfaces:
            lines.append(_report(name, surf))
            lines.append(f"[{name}] dirty px = "
                         f"{theme.dirty_pixel_count(surf)}")
    except Exception as e:
        lines.append(f"[round 5 probes] <failed: {e}>")
    try:
        with open(_LOG_PATH, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    except Exception:
        pass
    return _LOG_PATH, _PNG_PATH
