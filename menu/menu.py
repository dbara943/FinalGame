import pygame
import math
import os
pygame.font.init()

import i18n
from i18n import t as _t

money_img = pygame.transform.scale(pygame.image.load(os.path.join("images", "coin.png")), (20, 20))
_coin_icon = pygame.transform.scale(money_img, (15, 15))  # mala moneta przy cenach (zamiast $)

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
        self.font = pygame.font.SysFont("segoe ui, calibri, arial", 30)
        self.small_font = pygame.font.SysFont("segoe ui, calibri, arial", 20)
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
        # Panel rect (razem z paskiem TOWER.EXE nad panelem) - klik w panel
        # (nie tylko w przyciski) zjada klik, nie otwiera budynku/namiotu spod menu.
        self.panel_rect = pygame.Rect(px, py - 10, panel_w, panel_h + 10)
        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (16, 26, 40, 235), bg.get_rect(), border_radius=8)
        pygame.draw.rect(bg, (*bright, 255), bg.get_rect(), 2, border_radius=8)
        c = 12
        for cx, cy in [(0, 0), (panel_w, 0), (0, panel_h), (panel_w, panel_h)]:
            dx = -1 if cx == 0 else 1
            dy = -1 if cy == 0 else 1
            pygame.draw.line(bg, (*bright, 255), (cx, cy), (cx + dx*c, cy), 3)
            pygame.draw.line(bg, (*bright, 255), (cx, cy), (cx, cy + dy*c), 3)
        win.blit(bg, (px, py))
        tag_font = pygame.font.SysFont("consolas, monospace", 11)
        tag = tag_font.render("TOWER.EXE", True, bright)
        pygame.draw.rect(win, (8, 14, 22), (px + 8, py - 10, tag.get_width() + 8, 14))
        win.blit(tag, (px + 12, py - 8))
        name_font = pygame.font.SysFont("consolas, monospace", 15, bold=True)
        # Nazwa wyswietlana w biezacym jezyku (Wood Tower / Gold Tower...)
        name_text = i18n.tower_name(tname, getattr(tw, 'display_name', None)
                                    or (tw.name if hasattr(tw, 'name') else tname))
        label = name_font.render(f"> {name_text.upper()}", True, bright)
        win.blit(label, (px + 14, py + 14))
        lvl, maxlvl = tw.level, tw.max_level
        bar_x, bar_y, bar_w, bar_h = px + 14, py + 36, panel_w - 28, 8
        pygame.draw.rect(win, (50, 62, 80), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        fill_w = int(bar_w * lvl / maxlvl)
        pygame.draw.rect(win, bright, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
        lvl_txt = tag_font.render(f"LV.{lvl}/{maxlvl}", True, bright)
        win.blit(lvl_txt, (px + panel_w - lvl_txt.get_width() - 14, py + 32))
        stat_font = pygame.font.SysFont("consolas, monospace", 12)
        # Statystyki EFEKTYWNE (na zywo, nie bazowe): Honor Banner +10% (ceil,
        # min +1), synergia +15%, deszcz -10% zasiegu, predkosc strzelania.
        # Wczesniej pokazywano surowe damage/range - upgrade'y budynkow
        # niby dzialaly, ale menu tego nie pokazywalo.
        if tname == "SpikeCluster":
            # Kolce: damage TO juz DPS (obrazenia na sekunde), bez strzalow
            slabel = stat_font.render(_t("tm.spike_stats", dmg=f"{tw.damage:.0f}", rng=tw.range), True, bright)
            win.blit(slabel, (px + 14, py + 52))
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
            slabel = stat_font.render(_t("tm.stats1", dmg=eff_dmg, rng=eff_rng), True, bright)
            win.blit(slabel, (px + 14, py + 52))
            dlabel = stat_font.render(_t("tm.stats2", dps=f"{dps:.1f}"), True, bright)
            win.blit(dlabel, (px + 14, py + 68))
            klabel = stat_font.render(_t("tm.kills", n=tw.kills), True, bright)
            win.blit(klabel, (px + 122, py + 68))
        if tname == "SpikeCluster":
            klabel = stat_font.render(_t("tm.kills", n=tw.kills), True, bright)
            win.blit(klabel, (px + 14, py + 68))
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
            link_font = pygame.font.SysFont("consolas, monospace", 11, bold=True)
            ltxt = link_font.render(_t(f"link.{_link}"), True, (255, 215, 100))
            win.blit(ltxt, (px + (panel_w - ltxt.get_width()) // 2, py + 152))
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
        # Zywsze przyciski: mocniejsze wypelnienie, grubsza ramka, jasniejszy tekst
        br = tuple(min(255, int(c * 1.4 + 45)) for c in color)
        btn = pygame.Surface((w, h), pygame.SRCALPHA)
        r, g, b = br[0], br[1], br[2]
        if disabled:
            pygame.draw.rect(btn, (50, 58, 70, 200), btn.get_rect(), border_radius=6)
            pygame.draw.rect(btn, (110, 120, 135, 160), btn.get_rect(), 1, border_radius=6)
        else:
            pygame.draw.rect(btn, (r, g, b, 120), btn.get_rect(), border_radius=6)
            pygame.draw.rect(btn, (r, g, b, 255), btn.get_rect(), 3, border_radius=6)
        win.blit(btn, (x, y))
        tfont = pygame.font.SysFont("consolas, monospace", 13, bold=True)
        sfont = pygame.font.SysFont("consolas, monospace", 12)
        tcol = (155, 165, 175) if disabled else (r, g, b)
        t = tfont.render(title, True, tcol)
        win.blit(t, (x + w//2 - t.get_width()//2, y + 8))
        if sub:
            scol = sub_color if sub_color else tcol
            s = sfont.render(str(sub), True, scol)
            # Cena w zlocie: ikona monety + kwota jako wycentrowana grupa
            _price_like = str(sub)[0].isdigit() or str(sub)[0] == "+"
            _gw = s.get_width() + (19 if _price_like else 0)
            _gx = x + w // 2 - _gw // 2
            if _price_like:
                win.blit(_coin_icon, (_gx, y + 27))
            win.blit(s, (_gx + (19 if _price_like else 0), y + 28))

    def _draw_holo_btn_sale(self, win, x, y, w, h, title, orig_price, sale_price, color, disabled):
        """Przycisk z przekreslona cena (Costco style)."""
        br = tuple(min(255, int(c * 1.4 + 45)) for c in color)
        btn = pygame.Surface((w, h), pygame.SRCALPHA)
        r, g, b = br[0], br[1], br[2]
        if disabled:
            pygame.draw.rect(btn, (50, 58, 70, 200), btn.get_rect(), border_radius=6)
        else:
            pygame.draw.rect(btn, (r, g, b, 120), btn.get_rect(), border_radius=6)
            pygame.draw.rect(btn, (r, g, b, 255), btn.get_rect(), 3, border_radius=6)
        win.blit(btn, (x, y))
        tfont = pygame.font.SysFont("consolas, monospace", 13, bold=True)
        sfont = pygame.font.SysFont("consolas, monospace", 11)
        tcol = (155, 165, 175) if disabled else (r, g, b)
        t = tfont.render(title, True, tcol)
        win.blit(t, (x + w//2 - t.get_width()//2, y + 6))
        # Przekreslona oryginalna (z ikona monety)
        o = sfont.render(f"{orig_price}", True, (150, 150, 150))
        _gw = o.get_width() + 17
        ox = x + w//2 - _gw//2
        oy = y + 24
        win.blit(_coin_icon, (ox, oy - 2))
        win.blit(o, (ox + 17, oy))
        pygame.draw.line(win, (200, 80, 80), (ox, oy + 6), (ox + _gw, oy + 6), 2)
        # Nowa cena (z ikona monety)
        s = sfont.render(f"{sale_price}", True, (255, 215, 0))
        _gw2 = s.get_width() + 17
        _sx = x + w//2 - _gw2//2
        win.blit(_coin_icon, (_sx, y + 34))
        win.blit(s, (_sx + 17, y + 36))

            
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
        self.font = pygame.font.SysFont("segoe ui, calibri, arial", 25)

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

    def get_rect(self):
        """Prostokat panelu sklepu (do przecigania i hover)."""
        panel_w = 184
        panel_h = len(self.buttons) * 66 + 46
        return pygame.Rect(self.x - panel_w // 2, self.y - 140, panel_w, panel_h)

    def draw(self, win, mouse_pos=None, discount=1.0):
        """Rysuje sklep. discount: mnoznik ceny (Supply Lines: 0.85) - pokazuje przekreslenie."""
        # Nowoczesny sklep: ciemny panel, wyrownane ceny, bez niebieskiego tła
        # mouse_pos w wspolrzednych gry (po przeskalowaniu) - do hovera
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()
        panel_w = 184
        panel_h = len(self.buttons) * 66 + 46
        px = self.x - panel_w // 2
        py = self.y - 140

        # Przezroczystosc gdy mysz nie jest nad panelem
        mx, my = mouse_pos
        hovered_panel = self.get_rect().collidepoint(mx, my)
        alpha = 255 if hovered_panel else 110

        # Rysuj wszystko na osobnej powierzchni, potem naloz z alfa
        surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (10, 16, 28, 240), bg.get_rect(), border_radius=16)
        pygame.draw.rect(bg, (80, 120, 180, 100), bg.get_rect(), 2, border_radius=16)
        surf.blit(bg, (0, 0))

        # Naglowek sklepu
        hfont = pygame.font.SysFont("segoe ui, calibri, arial", 18, bold=True)
        ht = hfont.render(_t("shop.title"), True, (200, 220, 240))
        surf.blit(ht, (panel_w//2 - ht.get_width()//2, 10))
        
        for idx, item in enumerate(self.buttons):
            bx = px + 12
            by = py + 38 + idx * 66
            # Tlo przycisku
            btn_bg = pygame.Surface((panel_w - 24, 58), pygame.SRCALPHA)
            # Hover efekt
            hovering = bx <= mx <= bx + panel_w - 24 and by <= my <= by + 58
            if hovering:
                pygame.draw.rect(btn_bg, (35, 50, 75, 255), btn_bg.get_rect(), border_radius=10)
            else:
                pygame.draw.rect(btn_bg, (22, 32, 50, 255), btn_bg.get_rect(), border_radius=10)
            surf.blit(btn_bg, (bx - px, by - py))
            # Ikona: grafika wiezy z pociskiem (kompozyt 46x46, bez skalowania)
            surf.blit(item.img, (bx + 6 - px, by + 6 - py))
            # Schludny layout: nazwa / obrazenia / cena - wszystko wyrownane
            nfont = pygame.font.SysFont("segoe ui, calibri, arial", 14, bold=True)
            dfont = pygame.font.SysFont("segoe ui, calibri, arial", 12)
            pfont = pygame.font.SysFont("segoe ui, calibri, arial", 14, bold=True)
            names = [_t("tower.wood"), _t("tower.metal"), _t("tower.gold"),
                     _t("tower.fire"), _t("tower.blaze"), _t("tower.ice")]
            tx = bx + 58 - px  # wspolna lewa krawedz tekstu
            nm = nfont.render(names[idx] if idx < len(names) else item.name, True, (230, 235, 240))
            surf.blit(nm, (tx, by + 4 - py))
            dm = dfont.render(_t("shop.dmg", dmg=item.damage), True, (170, 180, 190))
            surf.blit(dm, (tx, by + 22 - py))
            # Cena: z discountem pokazuje przekreslona oryginalna + nowa (Costco style)
            if discount < 1.0:
                orig = item.cost
                new_price = int(orig * discount)
                # Ikona monety + przekreslona oryginalna (szara)
                surf.blit(_coin_icon, (tx, by + 39 - py))
                pt_orig = pfont.render(f"{orig}", True, (120, 120, 120))
                surf.blit(pt_orig, (tx + 19, by + 38 - py))
                # Linia przekreslenia
                lx1, ly = tx + 19, by + 38 - py + pt_orig.get_height() // 2
                lx2 = tx + 19 + pt_orig.get_width()
                pygame.draw.line(surf, (200, 80, 80), (lx1, ly), (lx2, ly), 2)
                # Nowa cena (zolota, obok)
                pt_new = pfont.render(f"{new_price}", True, (255, 215, 0))
                surf.blit(pt_new, (tx + 19 + pt_orig.get_width() + 8, by + 38 - py))
            else:
                surf.blit(_coin_icon, (tx, by + 39 - py))
                pt = pfont.render(f"{item.cost}", True, (255, 215, 0))
                surf.blit(pt, (tx + 19, by + 38 - py))
            # Aktualizuj pozycje klikalna (wspolrzedne ekranu)
            item.x, item.y = bx, by
            item.width, item.height = panel_w - 24, 58
        # Naloz caly panel z przezroczystoscia
        if alpha < 255:
            surf.set_alpha(alpha)
        win.blit(surf, (px, py))
    
    