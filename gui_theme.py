"""Wspolny styl GUI: drewno + mosiadz (kierunek A - decyzja Daniela 23.10.2026).

Proceduralna tekstura desek orzechowych (cachowana per rozmiar) + mosiadzne
ramki i narozniki. Zastepuje dawny "szklany" wyglad (glassmorphism / hologram).
Tylko wyglad - zadnej logiki gry tu nie ma.
"""
import math
import random

import pygame

# --- Paleta (z mocka A) ---
WOOD_PANEL = (46, 30, 17)        # ciemny orzech - tla paneli
WOOD_PANEL_DARK = (36, 23, 13)   # ciemniejszy wariant (pauza, pomoc)
WOOD_BTN = (74, 50, 27)          # przyciski
WOOD_BTN_HOVER = (94, 64, 35)    # przyciski po najechaniu
WOOD_CARD = (50, 33, 20)         # karty (batch 32: ciemniejsze - kontrast tekstu)
WOOD_CARD_HOVER = (64, 43, 25)
WOOD_INSET = (24, 15, 8)         # wglebienia (pole tekstowe, tag)
BRASS = (196, 154, 74)           # mosiadz - ramki
BRASS_BRIGHT = (238, 200, 105)   # jasny mosiadz - narozniki, akcenty
BRASS_DARK = (138, 106, 50)      # ciemny mosiadz - ramki drugorzedne
CREAM = (252, 245, 226)          # kremowa biel napisow (batch 32: jasniejsza)
WARM_GRAY = (218, 204, 174)      # ciepla szarosc opisow (batch 32: jasniejsza)
WARM_DIM = (176, 158, 130)       # przygaszony cieply tekst (batch 32: jasniejszy)
GOLD_TEXT = (255, 215, 100)      # zloto cen / tytulow (jak dawniej)

_cache = {}

# Zewnetrzne cache powierzchni (np. cache napisow z menu/menu.py)
# rejestruja sie tutaj, zeby JEDNO wywolanie clear_cache() po
# (od)tworzeniu displaya czyscilo wszystko naraz. Powierzchnie
# zbudowane pod poprzedni display potrafia wrocic z popsuta alfa
# na macOS (runda 2 napraw, 24.10.2026 - napisy i trupy).
_extra_clearers = []


def register_cache_clearer(fn):
    """Rejestruje funkcje czyszczaca zewnetrzny cache powierzchni.
    Wywolywana z clear_cache() po kazdym (od)tworzeniu displaya."""
    if fn not in _extra_clearers:
        _extra_clearers.append(fn)


def clear_cache():
    """Czysci cache powierzchni GUI. Powierzchnie z cache'u sa po
    convert_alpha(), czyli zwiazane z formatem displaya, przy ktorym
    powstaly - po kazdym (od)tworzeniu displaya (menu -> gra, F11)
    trzeba je zbudowac od nowa, inaczej potrafia wrocic z popsuta
    alfa (przezroczysty sklep przy pierwszym otwarciu na macOS)."""
    _cache.clear()
    for _fn in list(_extra_clearers):
        try:
            _fn()
        except Exception:
            pass


# --- Zarzadzanie displayem i generacje cache'y (naprawa macOS, runda 3) ---
# Werdykt z prawdziwego Maca po rundach 1-2: objawy wracaly PRZERYWANIE
# (ten sam sklep raz czytelny, raz jako lite prostokaty; trupy dalej
# czarne). Wspolny mianownik przeoczonych sciezek: kazde set_mode
# tworzy display o (potencjalnie) innym formacie niz poprzedni, a gra
# odtwarzala display w wielu miejscach (ekran ladowania -> StartMenu
# -> Game -> F11 -> pauza/fullscreen) i nie kazdy cache byl po tym
# przebudowywany. Dlatego runda 3 jest strukturalna:
#  1) JEDEN punkt tworzenia displaya: set_display() - jesli zaden
#     tryb sie nie zmienia (typowy przeplyw ladowanie -> menu -> gra
#     to TEN SAM fullscreen natywny), display jest REUZYWANY i zaden
#     format sie nie zmienia przez cale zycie procesu.
#  2) Kazda REALNA zmiana trybu podbija GENERACJE displaya i czyści
#     cache przez clear_cache(). Wpisy cache'y nosza znacznik
#     generacji - nawet gdyby jakies miejsce czyszczenia umknelo,
#     wpis spod starej generacji sam sie przebuduje przy uzyciu.
_display_gen = 0
_set_mode_calls = 0
_display_mode = None  # (w, h, fullscreen) RZECZYWISTY tryb aktywnego displaya


def display_generation():
    """Numer generacji aktywnego displaya (rosnie przy kazdym set_mode)."""
    return _display_gen


def set_mode_call_count():
    """Ile razy w tym procesie wywolano pygame.display.set_mode
    (przez set_display). Do logu diagnostycznego F9."""
    return _set_mode_calls


def set_display(size, flags=0):
    """Jedyne miejsce wywolan pygame.display.set_mode w grze.

    Jesli aktywny display ma juz dokladnie ten tryb (rozmiar +
    fullscreen), zwraca go BEZ set_mode - format powierzchni w calym
    procesie zostaje wtedy jeden i ten sam. Przy realnej zmianie:
    set_mode + podbicie generacji + clear_cache()."""
    global _display_gen, _set_mode_calls, _display_mode
    want_fs = bool(flags & pygame.FULLSCREEN)
    cur = None
    try:
        cur = pygame.display.get_surface()
    except Exception:
        cur = None
    if cur is not None and _display_mode is not None:
        cw, ch, cfs = _display_mode
        if cfs == want_fs and (tuple(size) == (0, 0)
                               or tuple(size) == (cw, ch)):
            return cur
    surf = pygame.display.set_mode(size, flags)
    _set_mode_calls += 1
    _display_gen += 1
    _display_mode = (surf.get_width(), surf.get_height(), want_fs)
    clear_cache()
    return surf


def fade_copy(img, alpha):
    """Kopia powierzchni z przemnozonym kanalem alfa (fade trupa).

    Zamiast set_alpha() (SDL_SetSurfaceAlphaMod - modulacja przy
    blicie, ktora na macOS wracala z czarnym tlem trupa w rundach
    1-2) mnozymy SAME piksele kanalu alfa przez PixelArray, a potem
    rysujemy zwyklym blitem - dokladnie ta sciezka, ktora dla zywych
    wrogow na Macu dziala. Powierzchnia zrodlowa nietknieta."""
    alpha = max(0, min(255, int(alpha)))
    s = img.copy()
    # UWAGA: NIE wolac tu set_alpha (ani wartosci, ani None). Kopia ma
    # zostac w DOKLADNIE tym stanie powierzchni, w jakim zywe klatki
    # wrogow blituja sie poprawnie (alfa powierzchniowa 255 = neutralna,
    # odziedziczona po convert_alpha). Eksperyment na VM (batch35,
    # F1-blit/F2b): ta sama kopia z set_alpha(None) blitowala
    # przezroczysty rog na CZARNO - SDL wybiera sciezke blitu po
    # stanie alfy powierzchni, a nie tylko po pikselach.
    if alpha >= 255:
        return sanitize_alpha(s)
    if alpha <= 0:
        s.fill((0, 0, 0, 0))  # same zera - z definicji czysta
        return s
    px = pygame.PixelArray(s)
    try:
        w, h = s.get_size()
        for x in range(w):
            col = px[x]
            for y in range(h):
                c = s.unmap_rgb(col[y])
                if c.a:
                    col[y] = s.map_rgb((c.r, c.g, c.b,
                                        (c.a * alpha) // 255))
    finally:
        del px
    return sanitize_alpha(s)


def sanitize_alpha(surf):
    """Zeruje RGB wszedzie, gdzie alfa == 0 (naprawa macOS, runda 4).

    Log z prawdziwego Maca (25.10.2026, island_diag.log) pokazal, ze
    nasze powierzchnie nosza niezerowe RGB pod w pelni przezroczystymi
    pikselami: trup elity (40,25,0,0) - kolor "polysku" z filtra
    zlotego (BLEND_ADD dopisuje RGB takze pod alfa 0), srodek panelu
    sklepu (42,27,15,0), napisy z kolorem czcionki pod alfa 0.
    Windows/Linux te piksele ignoruje (alfa 0 = niewidzialne), ale
    sciezka SDL/Metal na macOS pokazuje je jako ciemne bloki, duchy
    faktur i przeklamane kolory. Czyszczenie jest niewidoczne na
    poprawnych rendererach - zmienia wylacznie piksele, ktorych i
    tak nie widac. Dziala W MIEJSCU i zwraca te sama powierzchnie.

    Implementacja bez nowych zaleznosci: maska z powierzchni
    (C-predkosc) zamieniona na powierzchnie bialo/czarna i przemnozona
    BLEND_RGBA_MULT - RGB zeruje sie dokladnie tam, gdzie alfa == 0,
    a kanal alfa zostaje nietkniety (alfa maski = 255 wszedzie).
    Powierzchnie bez alfy per piksel (brak SRCALPHA / brak maski
    alfa / colorkey) sa pomijane - nie maja pikseli alfa == 0."""
    try:
        if not (surf.get_flags() & pygame.SRCALPHA):
            return surf
        if surf.get_masks()[3] == 0 or surf.get_colorkey() is not None:
            return surf
        m = pygame.mask.from_surface(surf, threshold=0)
        if m.count() == surf.get_width() * surf.get_height():
            return surf  # brak przezroczystych pikseli - nic do czyszczenia
        ms = m.to_surface(setcolor=(255, 255, 255, 255),
                          unsetcolor=(0, 0, 0, 255))
        surf.blit(ms, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    except Exception:
        pass
    return surf


def dirty_pixel_count(surf):
    """Dokladna liczba 'brudnych' pikseli: alfa == 0 i RGB != 0.

    Tylko do diagnostyki (F9) i testow - PixelArray piksel po pikselu,
    wiec wolac na malych powierzchniach (sprite'y, nie plansze)."""
    try:
        if not (surf.get_flags() & pygame.SRCALPHA):
            return 0
        if surf.get_masks()[3] == 0:
            return 0
    except Exception:
        return 0
    n = 0
    px = pygame.PixelArray(surf)
    try:
        w, h = surf.get_size()
        for x in range(w):
            col = px[x]
            for y in range(h):
                c = surf.unmap_rgb(col[y])
                if c.a == 0 and (c.r or c.g or c.b):
                    n += 1
    finally:
        del px
    return n


def _wood_raw(w, h, base, plank_h=26):
    """Surowa tekstura desek (bez zaokraglen): poziome deski, sloje, seki.
    UWAGA na alfe: pygame.draw na powierzchni SRCALPHA wypala alfe koloru
    w piksele (linie sloi zostawialy alfa 46-200 i panele przeświecaly),
    a na powierzchni bez alfa rysuje pelna sila RGB (za jasne linie).
    Dlatego tekstura powstaje na SRCALPHA (poprawne mieszanie RGB),
    a na koncu jest splaszczana na nieprzezroczysta powierzchnie."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((*base, 255))
    rng = random.Random(w * 7919 + h * 104729 + base[0])
    # Deski: lekka zmiana jasnosci per deska + ciemna spoina + jasna linia pod spoina
    y = 0
    while y < h:
        ph = min(plank_h, h - y)
        jitter = rng.randint(-7, 7)
        if jitter:
            ov = pygame.Surface((w, ph), pygame.SRCALPHA)
            if jitter > 0:
                ov.fill((255, 226, 170, jitter * 2))
            else:
                ov.fill((0, 0, 0, -jitter * 3))
            surf.blit(ov, (0, y))
        if y > 0:
            pygame.draw.line(surf, (12, 7, 3, 200), (0, y), (w, y), 2)
            if y + 2 < h:
                # Jasna linia pod spoina slabsza od batcha 32 - pod tekstem
                # drobnych napisow robila szum obnizajacy czytelnosc.
                pygame.draw.line(surf, (255, 224, 168, 16), (0, y + 2), (w, y + 2), 1)
        # Sloje: faliste poziome linie wewnatrz deski
        for _ in range(3):
            gy = y + rng.randint(4, max(4, ph - 4))
            phase = rng.uniform(0, 6.28)
            amp = rng.uniform(0.6, 1.6)
            dark = rng.random() < 0.7
            col = (16, 9, 4, 46) if dark else (255, 222, 168, 13)
            pts = [(x, gy + amp * math.sin(x * 0.018 + phase))
                   for x in range(0, w + 1, 14)]
            if len(pts) > 1:
                pygame.draw.lines(surf, col, False, pts, 1)
        # Sek (rzadko): ciemna elipsa z pierscieniem
        if rng.random() < 0.30 and w > 60 and ph > 12:
            kx, ky = rng.randint(14, w - 14), y + ph // 2
            pygame.draw.ellipse(surf, (20, 11, 5, 90),
                                (kx - 6, ky - 3, 12, 6), 1)
            pygame.draw.ellipse(surf, (12, 6, 2, 70),
                                (kx - 3, ky - 2, 6, 4))
        y += plank_h
    # Splaszczenie alfy do 255 (RGB bez zmian - kompozycja jak na ekranie)
    flat = pygame.Surface((w, h))
    flat.fill(base)
    flat.blit(surf, (0, 0))
    return flat.convert_alpha()


def _apply_radius(surf, radius):
    """Wycina rogi do zaokraglenia (maska multiply)."""
    w, h = surf.get_size()
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    mask.fill((0, 0, 0, 0))
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(),
                     border_radius=radius)
    surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return surf


def _brass_corners(surf, radius, col=BRASS_BRIGHT, arm=15, width=3, inset=1):
    """Mosiezne narozniki (klamry L) w stylu mocka A."""
    w, h = surf.get_size()
    a = arm
    i = inset
    for cx, cy, dx, dy in ((i, i, 1, 1), (w - 1 - i, i, -1, 1),
                           (i, h - 1 - i, 1, -1), (w - 1 - i, h - 1 - i, -1, -1)):
        pygame.draw.line(surf, col, (cx, cy), (cx + dx * a, cy), width)
        pygame.draw.line(surf, col, (cx, cy), (cx, cy + dy * a), width)


def wood_panel(w, h, radius=14, base=WOOD_PANEL, border=BRASS, corners=True,
               plank_h=26):
    """Gotowa powierzchnia panelu: drewno + zaokraglenie + mosiadzna ramka.
    Cachowana - bezpieczna do rysowania co klatke."""
    key = ("panel", w, h, radius, base, border, corners, plank_h)
    ent = _cache.get(key)
    if ent is not None and ent[0] == _display_gen:
        return ent[1]
    s = _wood_raw(w, h, base, plank_h)
    _apply_radius(s, radius)
    pygame.draw.rect(s, (*border, 255), s.get_rect(), 2,
                     border_radius=radius)
    if corners and w >= 90 and h >= 60:
        _brass_corners(s, radius)
    _cache[key] = (_display_gen, s)
    return s


def wood_button(w, h, radius=12, hover=False, base=None):
    """Powierzchnia przycisku: jasniejsze drewno + mosiadzna ramka + polysk u gory."""
    if base is None:
        base = WOOD_BTN_HOVER if hover else WOOD_BTN
    key = ("btn", w, h, radius, base)
    ent = _cache.get(key)
    if ent is not None and ent[0] == _display_gen:
        return ent[1]
    s = _wood_raw(w, h, base, plank_h=22)
    _apply_radius(s, radius)
    pygame.draw.rect(s, (*BRASS, 255), s.get_rect(), 2,
                     border_radius=radius)
    # Delikatny polysk u gory (zamiast dawnego "blysk szkla")
    sheen = pygame.Surface((max(1, w - 16), max(1, h // 3)), pygame.SRCALPHA)
    pygame.draw.rect(sheen, (255, 232, 180, 26), sheen.get_rect(),
                         border_radius=8)
    s.blit(sheen, (8, 5))
    _cache[key] = (_display_gen, s)
    return s


def wood_fill(surf, rect, radius=10, base=WOOD_CARD, border=BRASS_DARK,
              border_w=2):
    """Wypelnia rect na surf tekstura drewna z zaokraglonymi rogami
    (+ opcjonalna ramka). Cachowane per rozmiar/kolor."""
    key = ("fill", rect.w, rect.h, radius, base, border, border_w)
    ent = _cache.get(key)
    if ent is not None and ent[0] == _display_gen:
        t = ent[1]
    else:
        t = _wood_raw(rect.w, rect.h, base, plank_h=24)
        _apply_radius(t, radius)
        if border_w:
            pygame.draw.rect(t, (*border, 255), t.get_rect(), border_w,
                             border_radius=radius)
        _cache[key] = (_display_gen, t)
    surf.blit(t, (rect.x, rect.y))
