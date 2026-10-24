import pygame
import math
import os
pygame.font.init()

import i18n
from i18n import t as _t
import gui_theme as theme

money_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "coin.png")), (20, 20))
_coin_icon = pygame.transform.scale(money_img, (15, 15))  # mala moneta przy cenach (zamiast $)

# --- Cache fontow i napisow (wydajnosc, batch 32) ---
# Wczesniej kazde draw() sklepu / menu wiezy tworzylo ~30 nowych obiektow
# pygame.font.SysFont (kazdy = wyszukanie + wczytanie pliku fontu z dysku)
# i renderowalo te same napisy od nowa co klatke. Profilowanie: samo
# rysowanie sklepu zjadalo ~84% czasu klatki -> lag zwlaszcza przy
# stawianiu wiezy (duch wiezy musi isc 1:1 za kursorem). Fonty i gotowe
# powierzchnie napisow sa teraz cachowane; wyglad bez zmian.
_FONT_CACHE = {}
_TEXT_CACHE = {}
_TEXT_CACHE_MAX = 800


def sysfont(name, size, bold=False):
    """pygame.font.SysFont z cache - ten sam obiekt dla tych samych parametrow."""
    key = (name, size, bold)
    f = _FONT_CACHE.get(key)
    if f is None:
        f = pygame.font.SysFont(name, size, bold=bold)
        _FONT_CACHE[key] = f
    return f


TEXT_SHADOW = (10, 6, 3)  # prawie czarny braz - cien napisow na drewnie


def blit_text(surf, font, text, color, x, y):
    """Blit napisu z ciemnym cienem 1 px (batch 32: czytelnosc kremowych
    liter na drewnianych panelach). Cien i napis ida przez cache."""
    surf.blit(render_text(font, text, TEXT_SHADOW), (x + 1, y + 1))
    surf.blit(render_text(font, text, color), (x, y))


def render_text(font, text, color):
    """font.render z cache powierzchni (napisy w menu powtarzaja sie co klatke)."""
    key = (id(font), text, color)
    s = _TEXT_CACHE.get(key)
    if s is None:
        if len(_TEXT_CACHE) >= _TEXT_CACHE_MAX:
            _TEXT_CACHE.clear()
        s = font.render(text, True, color)
        # Normalizacja jak przy grafikach (naprawa macOS, runda 2):
        # powierzchnia z font.render ma RGB = jednolity kolor czcionki,
        # a ksztalt liter niesie WYLACZNIE kanal alfa - gdy taka
        # powierzchnia wroci z cache po odtworzeniu displaya i alfa
        # zgubi sie przy blicie, napis renderuje sie jako prostokat
        # w kolorze czcionki. Konwersja do formatu aktywnego displaya
        # (raz, przy tworzeniu wpisu) + czyszczenie cache przy kazdym
        # odtworzeniu displaya (rejestracja nizej) trzymaja napisy
        # w tym samym formacie co reszta gry.
        try:
            if pygame.display.get_surface() is not None:
                s = s.convert_alpha()
        except Exception:
            pass
        _TEXT_CACHE[key] = s
    return s


def clear_text_cache():
    """Czysci cache powierzchni napisow. Wywolywane przez
    gui_theme.clear_cache() po kazdym (od)tworzeniu displaya."""
    _TEXT_CACHE.clear()


theme.register_cache_clearer(clear_text_cache)


class Button():
    def __init__(self, menu, img, name, dx=0, dy=0):
        self.name = name
        self.img = img
        self.menu = menu
        self.dx = dx
        self.dy = dy
        self.width = self.img.get_width()
        self.height = self.img.get_height()
        self.update()

    def click(self, X, Y):
        
        if X <= self.x + self.width and X >= self.x:
            if Y <= self.y + self.height and Y >= self.y:
                return True
        return False
    
    def draw(self, win):
        win.blit(self.img, (self.x, self.y))
    
    def update(self):
        self.x = self.menu.x + self.dx
        self.y = self.menu.y + self.dy
        
class VerticalButton(Button):
    def __init__(self, x, y, img, name, cost, damage=0):
        self.name = name
        self.img = img
        self.x = x
        self.y = y
        self.width = self.img.get_width()
        self.height = self.img.get_height()
        self.cost = cost
        self.damage = damage
                
class Menu():
    def __init__(self, tower, x, y, img, item_cost):
        self.x = x
        self.y = y
        self.width = img.get_width()
        self.height = img.get_height()
        self.item_names = []
        self.buttons = []
        self.item_cost = item_cost
        self.items = 0
        self.bg = img
        self.font = sysfont("segoe ui, calibri, arial", 30)
        self.small_font = sysfont("segoe ui, calibri, arial", 20)
        self.tower = tower

    def add_btn(self, img, name, dx=0, dy=0):
        self.items += 1
        self.buttons.append(Button(self, img, name, dx, dy))
    
    def get_item_cost(self):
        return self.item_cost[self.tower.level - 1]
        
    def draw(self, win, money=None, discount=1.0, sell_rate=0.7):
        # Hologram HUD (wariant D) - kolor zalezny od typu wiezy
        # discount: Supply Lines 0.85 - pokazuje przekreslenie
        # sell_rate: stawka zwrotu wg trudnosci (EASY 0.8 / NORMAL 0.7 / HARD 0.6)
        tw = self.tower
        tname = type(tw).__name__
        colors = {
            "WoodenTower": (139, 90, 43),
            "MetalTower": (120, 150, 180),
            "GoldenTower": (212, 175, 55),
            "FireTower": (220, 80, 40),
            "BlazeTower": (180, 60, 200),
            "IceTower": (110, 200, 245),
            "SpikeCluster": (139, 90, 43),
        }
        holo = colors.get(tname, (0, 255, 204))
        # Jasniejsza wersja koloru wiezy do tekstow - surowy kolor byl wymazany
        bright = tuple(min(255, int(c * 1.4 + 45)) for c in holo)
        panel_w, panel_h = 240, 176
        px = self.x - panel_w // 2
        py = self.y - 210  # calkowicie nad wieza (wieza w pelni widoczna)
        # Clamp do ekranu (Daniel): menu wiezy stojacej przy krawedzi
        # (np. Blaze wysoko przy brzegu) wychodzilo poza plansze -
        # dosuwamy panel do srodka, by byl zawsze w calosci widoczny;
        # przyciski liczone sa od px/py, wiec kliki ida za panelem.
        px = max(4, min(px, win.get_width() - panel_w - 4))
        py = max(14, min(py, win.get_height() - panel_h - 4))
        # Panel rect (razem z paskiem TOWER.EXE nad panelem) - klik w panel
        # (nie tylko w przyciski) zjada klik, nie otwiera budynku/namiotu spod menu.
        self.panel_rect = pygame.Rect(px, py - 10, panel_w, panel_h + 10)
        # Panel w stylu A: ciemne drewno + mosiadzna ramka; narozne kreski
        # zostaja w kolorze wiezy (akcent informacyjny typu)
        bg = theme.wood_panel(panel_w, panel_h, radius=8,
                              base=theme.WOOD_PANEL_DARK, corners=False).copy()
        bg.set_alpha(244)
        c = 12
        for cx, cy in [(0, 0), (panel_w, 0), (0, panel_h), (panel_w, panel_h)]:
            dx = -1 if cx == 0 else 1
            dy = -1 if cy == 0 else 1
            pygame.draw.line(bg, (*bright, 255), (cx, cy), (cx + dx*c, cy), 3)
            pygame.draw.line(bg, (*bright, 255), (cx, cy), (cx, cy + dy*c), 3)
        win.blit(bg, (px, py))
        tag_font = sysfont("consolas, monospace", 11)
        tag = render_text(tag_font, "TOWER.EXE", bright)
        pygame.draw.rect(win, theme.WOOD_INSET, (px + 8, py - 10, tag.get_width() + 8, 14))
        win.blit(tag, (px + 12, py - 8))
        name_font = sysfont("consolas, monospace", 15, bold=True)
        # Nazwa wyswietlana w biezacym jezyku (Wood Tower / Gold Tower...)
        name_text = i18n.tower_name(tname, getattr(tw, 'display_name', None)
                                    or (tw.name if hasattr(tw, 'name') else tname))
        blit_text(win, name_font, f"> {name_text.upper()}", bright, px + 14, py + 14)
        lvl, maxlvl = tw.level, tw.max_level
        bar_x, bar_y, bar_w, bar_h = px + 14, py + 36, panel_w - 28, 8
        pygame.draw.rect(win, (70, 52, 32), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        fill_w = int(bar_w * lvl / maxlvl)
        pygame.draw.rect(win, bright, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
        lvl_txt = render_text(tag_font, f"LV.{lvl}/{maxlvl}", bright)
        blit_text(win, tag_font, f"LV.{lvl}/{maxlvl}", bright,
                  px + panel_w - lvl_txt.get_width() - 14, py + 32)
        stat_font = sysfont("consolas, monospace", 12)
        # Statystyki EFEKTYWNE (na zywo, nie bazowe): Honor Banner +10% (ceil,
        # min +1), synergia +15%, deszcz -10% zasiegu, predkosc strzelania.
        # Wczesniej pokazywano surowe damage/range - upgrade'y budynkow
        # niby dzialaly, ale menu tego nie pokazywalo.
        if tname == "SpikeCluster":
            # Kolce: damage TO juz DPS (obrazenia na sekunde), bez strzalow
            blit_text(win, stat_font, _t("tm.spike_stats", dmg=f"{tw.damage:.0f}", rng=tw.range),
                      bright, px + 14, py + 52)
        else:
            eff_dmg = math.ceil(int(tw.damage * getattr(tw, '_synergy', 1.0)) * getattr(tw, '_dmg_mult', 1.0))
            _frm = getattr(tw, '_fire_rate_mult', 1.0)
            if getattr(tw, '_link', None) == 'wood':
                _frm *= 1.3  # Link Wood w wyswietlanym DPS
            shots_per_s = 100.0 * _frm / 60.0
            dps = eff_dmg * shots_per_s
            _rngm = getattr(tw, '_rain_mod', 1.0)
            if getattr(tw, '_link', None) == 'metal':
                _rngm *= 1.25  # Link Metal w wyswietlanym zasiegu
            eff_rng = int(tw.range * _rngm)
            blit_text(win, stat_font, _t("tm.stats1", dmg=eff_dmg, rng=eff_rng),
                      bright, px + 14, py + 52)
            # Linia DPS w menu wiezy ZOSTAJE (Daniel, batch 28: usuniecie
            # w batchu 27 bylo pomylka - chodzilo o hover w sklepie).
            blit_text(win, stat_font, _t("tm.stats2", dps=f"{dps:.1f}"),
                      bright, px + 14, py + 68)
            # Shrink-to-fit: linia KILLS startuje w polowie panelu (budzet
            # ~104px), a FR "ÉLIMINATIONS 999" ma ~112px i wychodzila poza panel
            _ktxt = _t("tm.kills", n=tw.kills)
            _kfont = stat_font
            if _kfont.size(_ktxt)[0] > panel_w - 122 - 14:
                _kfont = sysfont("consolas, monospace", 10)
            blit_text(win, _kfont, _ktxt, bright, px + 122, py + 68)
        if tname == "SpikeCluster":
            blit_text(win, stat_font, _t("tm.kills", n=tw.kills), bright,
                      px + 14, py + 68)
        btn_y, btn_h = py + 92, 52
        is_max = tw.level >= tw.max_level
        if not is_max:
            up_cost = self.item_cost[tw.level - 1]
            # Wyszarzony gdy nie stac, ale zawsze widoczny koszt (bez -$)
            # Supply Lines: przekreslona oryginalna + nowa cena
            if discount < 1.0:
                disc_cost = int(up_cost * discount)
                affordable = money is not None and money >= disc_cost
                self._draw_holo_btn_sale(win, px + 12, btn_y, 106, btn_h, _t("tm.upgrade"),
                                         up_cost, disc_cost, holo, not affordable)
            else:
                affordable = money is not None and money >= up_cost
                self._draw_holo_btn(win, px + 12, btn_y, 106, btn_h, _t("tm.upgrade"), f"{up_cost}",
                                    holo, not affordable)
        else:
            self._draw_holo_btn(win, px + 12, btn_y, 106, btn_h, _t("tm.max_level"), "", (100, 110, 120), True)
        sell_val = tw.sell_value(sell_rate)
        self._draw_holo_btn(win, px + 122, btn_y, 106, btn_h, _t("tm.sell"), f"+{sell_val}", (255, 100, 100), False)
        # Linia linku sasiada (unikatowy bonus per typ) - zlota, pod przyciskami
        _link = getattr(tw, '_link', None) if tname != "SpikeCluster" else None
        if _link:
            link_font = sysfont("consolas, monospace", 11, bold=True)
            _ltxt = _t(f"link.{_link}")
            # Shrink-to-fit: DE link.metal (~245px) wychodzil poza panel 240px
            if link_font.size(_ltxt)[0] > panel_w - 8:
                link_font = sysfont("consolas, monospace", 9, bold=True)
            ltxt = render_text(link_font, _ltxt, (255, 215, 100))
            blit_text(win, link_font, _ltxt, (255, 215, 100),
                      px + (panel_w - ltxt.get_width()) // 2, py + 152)
        if len(self.buttons) >= 2:
            if not is_max:
                self.buttons[0].x, self.buttons[0].y = px + 12, btn_y
                self.buttons[0].width, self.buttons[0].height = 106, btn_h
            else:
                self.buttons[0].x, self.buttons[0].y = -100, -100
                self.buttons[0].width, self.buttons[0].height = 0, 0
            self.buttons[1].x, self.buttons[1].y = px + 122, btn_y
            self.buttons[1].width, self.buttons[1].height = 106, btn_h

    def _draw_holo_btn(self, win, x, y, w, h, title, sub, color, disabled, sub_color=None):
        # Przyciski w stylu A: drewniany korpus + mosiadzna ramka; kolor
        # wiezy zostaje w tekscie (akcent informacyjny typu)
        br = tuple(min(255, int(c * 1.4 + 45)) for c in color)
        btn = pygame.Surface((w, h), pygame.SRCALPHA)
        r, g, b = br[0], br[1], br[2]
        if disabled:
            pygame.draw.rect(btn, (56, 46, 36, 210), btn.get_rect(), border_radius=6)
            pygame.draw.rect(btn, (150, 128, 92, 170), btn.get_rect(), 1, border_radius=6)
        else:
            theme.wood_fill(btn, btn.get_rect(), radius=6, base=theme.WOOD_BTN,
                            border=theme.BRASS, border_w=2)
        win.blit(btn, (x, y))
        tfont = sysfont("consolas, monospace", 13, bold=True)
        # Shrink-to-fit tytulu (RU "МАКС. УРОВЕНЬ" ~104px w przycisku 106px)
        if tfont.size(title)[0] > w - 6:
            tfont = sysfont("consolas, monospace", 11, bold=True)
        sfont = sysfont("consolas, monospace", 12)
        tcol = (190, 176, 154) if disabled else (r, g, b)
        t = render_text(tfont, title, tcol)
        blit_text(win, tfont, title, tcol, x + w//2 - t.get_width()//2, y + 8)
        if sub:
            scol = sub_color if sub_color else tcol
            s = render_text(sfont, str(sub), scol)
            # Cena w zlocie: ikona monety + kwota jako wycentrowana grupa
            _price_like = str(sub)[0].isdigit() or str(sub)[0] == "+"
            _gw = s.get_width() + (19 if _price_like else 0)
            _gx = x + w // 2 - _gw // 2
            if _price_like:
                win.blit(_coin_icon, (_gx, y + 27))
            blit_text(win, sfont, str(sub), scol,
                      _gx + (19 if _price_like else 0), y + 28)

    def _draw_holo_btn_sale(self, win, x, y, w, h, title, orig_price, sale_price, color, disabled):
        """Przycisk z przekreslona cena (Costco style)."""
        br = tuple(min(255, int(c * 1.4 + 45)) for c in color)
        btn = pygame.Surface((w, h), pygame.SRCALPHA)
        r, g, b = br[0], br[1], br[2]
        if disabled:
            pygame.draw.rect(btn, (56, 46, 36, 210), btn.get_rect(), border_radius=6)
        else:
            theme.wood_fill(btn, btn.get_rect(), radius=6, base=theme.WOOD_BTN,
                            border=theme.BRASS, border_w=2)
        win.blit(btn, (x, y))
        tfont = sysfont("consolas, monospace", 13, bold=True)
        if tfont.size(title)[0] > w - 6:
            tfont = sysfont("consolas, monospace", 11, bold=True)
        sfont = sysfont("consolas, monospace", 11)
        tcol = (190, 176, 154) if disabled else (r, g, b)
        t = render_text(tfont, title, tcol)
        blit_text(win, tfont, title, tcol, x + w//2 - t.get_width()//2, y + 6)
        # Przekreslona oryginalna (z ikona monety)
        o = render_text(sfont, f"{orig_price}", (168, 168, 168))
        _gw = o.get_width() + 17
        ox = x + w//2 - _gw//2
        oy = y + 24
        win.blit(_coin_icon, (ox, oy - 2))
        blit_text(win, sfont, f"{orig_price}", (168, 168, 168), ox + 17, oy)
        pygame.draw.line(win, (200, 80, 80), (ox, oy + 6), (ox + _gw, oy + 6), 2)
        # Nowa cena (z ikona monety)
        s = render_text(sfont, f"{sale_price}", (255, 215, 0))
        _gw2 = s.get_width() + 17
        _sx = x + w//2 - _gw2//2
        win.blit(_coin_icon, (_sx, y + 34))
        blit_text(win, sfont, f"{sale_price}", (255, 215, 0), _sx + 17, y + 36)

            
    def get_clicked(self, X, Y):
        for btn in self.buttons:
            if btn.click(X, Y):
                return btn.name
        return None

    def get_hovered(self, X, Y):
        """U9: zwraca nazwe przycisku pod kursorem (do podgladu zasiegu)."""
        for btn in self.buttons:
            if btn.click(X, Y):
                return btn.name
        return None
    
    def update(self):
        for btn in self.buttons:
            btn.update()
            
class VerticalMenu(Menu):
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.width = img.get_width()
        self.height = img.get_height()
        self.buttons = []
        self.items = 0
        self.bg = img
        self.font = sysfont("segoe ui, calibri, arial", 25)

    def add_btn(self, img, name, cost, damage=0):
        self.items += 1
        btn_x = self.x - 20
        btn_y = self.y - 60 + (self.items-1)*66
        self.buttons.append(VerticalButton(btn_x, btn_y, img, name, cost, damage))

    def get_item_cost(self, name):
        for btn in self.buttons:
            if btn.name == name:
                return btn.cost
        return -1

    def _panel_w(self):
        """Szerokosc panelu sklepu: rosnie wraz z dlugoscia napisow w
        biezacym jezyku (Batch 30 - wczesniej sztywne 164 px ucinalo
        nazwy wiez np. po rosyjsku i polsku). Minimum 164 jak dawniej."""
        hfont = sysfont("segoe ui, calibri, arial", 18, bold=True)
        nfont = sysfont("segoe ui, calibri, arial", 14, bold=True)
        dfont = sysfont("segoe ui, calibri, arial", 12)
        pfont = sysfont("segoe ui, calibri, arial", 14, bold=True)
        names = [_t("tower.wood"), _t("tower.metal"), _t("tower.ice"),
                 _t("tower.gold"), _t("tower.fire"), _t("tower.blaze")]
        # Memoizacja (batch 32): szerokosc zalezy tylko od jezyka i cen/
        # obrazen przyciskow - wczesniej liczona 2x na klatke z pomiarami.
        _key = (tuple(names), _t("shop.title"),
                tuple((b.cost, b.damage) for b in self.buttons))
        if getattr(self, "_panel_w_key", None) == _key:
            return self._panel_w_val
        w = max(164, hfont.size(_t("shop.title"))[0] + 24)
        for idx, item in enumerate(self.buttons):
            nm = names[idx] if idx < len(names) else item.name
            text_w = max(nfont.size(nm)[0],
                         dfont.size(_t("shop.dmg", dmg=item.damage))[0])
            # Cena: zwykla oraz wariant ze znizka (przekreslona + nowa obok)
            price_w = 19 + pfont.size(f"{item.cost}")[0]
            price_w = max(price_w, 19 + pfont.size(f"{item.cost}")[0] + 8
                          + pfont.size(f"{int(item.cost * 0.85)}")[0])
            # Tekst zaczyna sie 70 px od lewej krawedzi panelu + zapas
            w = max(w, 70 + max(text_w, price_w) + 16)
        self._panel_w_key, self._panel_w_val = _key, w
        return w

    def get_rect(self):
        """Prostokat panelu sklepu (do przecigania i hover)."""
        panel_w = self._panel_w()
        panel_h = len(self.buttons) * 66 + 46
        px = max(0, self.x - panel_w // 2)
        return pygame.Rect(px, self.y - 140, panel_w, panel_h)

    def draw(self, win, mouse_pos=None, discount=1.0):
        """Rysuje sklep. discount: mnoznik ceny (Supply Lines: 0.85) - pokazuje przekreslenie."""
        # Nowoczesny sklep: ciemny panel, wyrownane ceny, bez niebieskiego tła
        # mouse_pos w wspolrzednych gry (po przeskalowaniu) - do hovera
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()
        panel_w = self._panel_w()
        panel_h = len(self.buttons) * 66 + 46
        px = max(0, self.x - panel_w // 2)
        py = self.y - 140

        # Przezroczystosc gdy mysz nie jest nad panelem (batch 32: 110 -> 150,
        # przy 110 napisy sklepu tonely w jasnej scenerii planszy)
        mx, my = mouse_pos
        hovered_panel = self.get_rect().collidepoint(mx, my)
        alpha = 255 if hovered_panel else 150

        # Rysuj wszystko na osobnej powierzchni, potem naloz z alfa
        surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        # (panel_w liczony dynamicznie w _panel_w - patrz wyzej)
        # Panel w stylu A: drewno + mosiadzne narozniki
        bg = theme.wood_panel(panel_w, panel_h, radius=16).copy()
        bg.set_alpha(246)
        surf.blit(bg, (0, 0))

        # Naglowek sklepu
        hfont = sysfont("segoe ui, calibri, arial", 18, bold=True)
        ht = render_text(hfont, _t("shop.title"), theme.BRASS_BRIGHT)
        blit_text(surf, hfont, _t("shop.title"), theme.BRASS_BRIGHT,
                  panel_w//2 - ht.get_width()//2, 10)
        
        for idx, item in enumerate(self.buttons):
            bx = px + 12
            by = py + 38 + idx * 66
            # Hover efekt
            hovering = bx <= mx <= bx + panel_w - 24 and by <= my <= by + 58
            # Tlo przycisku: jasniejsze drewno po najechaniu
            btn_bg = pygame.Surface((panel_w - 24, 58), pygame.SRCALPHA)
            theme.wood_fill(btn_bg, btn_bg.get_rect(), radius=10,
                            base=theme.WOOD_CARD_HOVER if hovering else theme.WOOD_CARD,
                            border=theme.BRASS if hovering else theme.BRASS_DARK,
                            border_w=2 if hovering else 1)
            surf.blit(btn_bg, (bx - px, by - py))
            # Ikona: grafika wiezy z pociskiem (kompozyt 46x46, bez skalowania)
            surf.blit(item.img, (bx + 6 - px, by + 6 - py))
            # Schludny layout: nazwa / obrazenia / cena - wszystko wyrownane
            nfont = sysfont("segoe ui, calibri, arial", 14, bold=True)
            dfont = sysfont("segoe ui, calibri, arial", 12)
            pfont = sysfont("segoe ui, calibri, arial", 14, bold=True)
            names = [_t("tower.wood"), _t("tower.metal"), _t("tower.ice"),
                     _t("tower.gold"), _t("tower.fire"), _t("tower.blaze")]
            tx = bx + 58 - px  # wspolna lewa krawedz tekstu
            blit_text(surf, nfont, names[idx] if idx < len(names) else item.name,
                      theme.CREAM, tx, by + 4 - py)
            blit_text(surf, dfont, _t("shop.dmg", dmg=item.damage),
                      theme.WARM_GRAY, tx, by + 22 - py)
            # Cena: z discountem pokazuje przekreslona oryginalna + nowa (Costco style)
            if discount < 1.0:
                orig = item.cost
                new_price = int(orig * discount)
                # Ikona monety + przekreslona oryginalna (szara)
                surf.blit(_coin_icon, (tx, by + 39 - py))
                pt_orig = render_text(pfont, f"{orig}", (160, 160, 160))
                blit_text(surf, pfont, f"{orig}", (160, 160, 160),
                          tx + 19, by + 38 - py)
                # Linia przekreslenia
                lx1, ly = tx + 19, by + 38 - py + pt_orig.get_height() // 2
                lx2 = tx + 19 + pt_orig.get_width()
                pygame.draw.line(surf, (200, 80, 80), (lx1, ly), (lx2, ly), 2)
                # Nowa cena (zolota, obok)
                blit_text(surf, pfont, f"{new_price}", (255, 215, 0),
                          tx + 19 + pt_orig.get_width() + 8, by + 38 - py)
            else:
                surf.blit(_coin_icon, (tx, by + 39 - py))
                blit_text(surf, pfont, f"{item.cost}", (255, 215, 0),
                          tx + 19, by + 38 - py)
            # Aktualizuj pozycje klikalna (wspolrzedne ekranu)
            item.x, item.y = bx, by
            item.width, item.height = panel_w - 24, 58
        # Naloz caly panel z przezroczystoscia
        if alpha < 255:
            surf.set_alpha(alpha)
        win.blit(surf, (px, py))
    
    