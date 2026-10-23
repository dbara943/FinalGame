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
    s = _cache.get(key)
    if s is None:
        s = _wood_raw(w, h, base, plank_h)
        _apply_radius(s, radius)
        pygame.draw.rect(s, (*border, 255), s.get_rect(), 2,
                         border_radius=radius)
        if corners and w >= 90 and h >= 60:
            _brass_corners(s, radius)
        _cache[key] = s
    return s


def wood_button(w, h, radius=12, hover=False, base=None):
    """Powierzchnia przycisku: jasniejsze drewno + mosiadzna ramka + polysk u gory."""
    if base is None:
        base = WOOD_BTN_HOVER if hover else WOOD_BTN
    key = ("btn", w, h, radius, base)
    s = _cache.get(key)
    if s is None:
        s = _wood_raw(w, h, base, plank_h=22)
        _apply_radius(s, radius)
        pygame.draw.rect(s, (*BRASS, 255), s.get_rect(), 2,
                         border_radius=radius)
        # Delikatny polysk u gory (zamiast dawnego "blysk szkla")
        sheen = pygame.Surface((max(1, w - 16), max(1, h // 3)), pygame.SRCALPHA)
        pygame.draw.rect(sheen, (255, 232, 180, 26), sheen.get_rect(),
                         border_radius=8)
        s.blit(sheen, (8, 5))
        _cache[key] = s
    return s


def wood_fill(surf, rect, radius=10, base=WOOD_CARD, border=BRASS_DARK,
              border_w=2):
    """Wypelnia rect na surf tekstura drewna z zaokraglonymi rogami
    (+ opcjonalna ramka). Cachowane per rozmiar/kolor."""
    key = ("fill", rect.w, rect.h, radius, base, border, border_w)
    t = _cache.get(key)
    if t is None:
        t = _wood_raw(rect.w, rect.h, base, plank_h=24)
        _apply_radius(t, radius)
        if border_w:
            pygame.draw.rect(t, (*border, 255), t.get_rect(), border_w,
                             border_radius=radius)
        _cache[key] = t
    surf.blit(t, (rect.x, rect.y))
