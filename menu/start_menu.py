import pygame
import os
import json

import i18n
from i18n import t

DIFFICULTIES = [
    ("EASY", 30, 300),
    ("NORMAL", 20, 200),
    ("HARD", 12, 150),
]

# Co daje kazda trudnosc (wyswietlane pod przyciskami w menu glownym).
DIFFICULTY_DESC = {
    "EASY": "EASY: -20% prices, -20% enemy HP, slower enemies, +25% gold",
    "NORMAL": "NORMAL: standard prices, enemies and gold",
    "HARD": "HARD: +25% prices, +30% enemy HP, faster enemies, -15% gold",
}

class StartMenu:
    """Ekran startowy: tytul, wybor trudnosci, dzwiek, pomoc i start gry."""

    def __init__(self, width, height, bg):
        self.width = width
        self.height = height
        # FULLSCREEN w natywnej rozdzielczosci, BEZ SCALED (brak czarnych paskow)
        try:
            self.win = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        except pygame.error:
            self.win = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Island Defenders")
        self.rw, self.rh = self.win.get_size()
        # Tlo na caly ekran (cover - wypelnia, przycina nadmiar)
        self.bg = self._cover_scale(bg, self.rw, self.rh)
        # Dzwiek klikniecia w menu
        try:
            pygame.mixer.init()
            self.click_sound = pygame.mixer.Sound(os.path.join("sounds", "4.wav"))
        except:
            self.click_sound = None
        pygame.display.set_caption("Island Defenders")
        self.title_font = pygame.font.SysFont("arial", 76, bold=True)
        self.btn_font = pygame.font.SysFont("arial", 30, bold=True)
        self.btn_font_small = pygame.font.SysFont("arial", 22, bold=True)
        self.small_font = pygame.font.SysFont("arial", 22)
        self.diff_idx = 1  # domyslnie NORMAL
        self.sound = True
        self.show_help = False
        self.show_achievements = False
        self.show_resolution = False
        self.clock = pygame.time.Clock()
        # Rozdzielczosc (zapisywana)
        self.resolutions = [(1124, 720), (1280, 720), (1600, 900), (1920, 1080), ("Native", "Fullscreen")]
        self.res_idx = 4  # domyslnie natywny fullscreen
        self._load_resolution()

        bw, bh, gap = 360, 54, 10
        x = self.rw // 2 - bw // 2
        y0 = self.rh // 2 - 120  # wczesniej -80: QUIT byl 2px od dolu przy 720p (przycinanie)
        self.buttons = {
            "start": pygame.Rect(x, y0, bw, bh),
            "diff": pygame.Rect(x, y0 + (bh + gap), bw, bh),
            "sound": pygame.Rect(x, y0 + 2 * (bh + gap), bw, bh),
            "achievements": pygame.Rect(x, y0 + 3 * (bh + gap), bw, bh),
            "resolution": pygame.Rect(x, y0 + 4 * (bh + gap), bw, bh),
            "help": pygame.Rect(x, y0 + 5 * (bh + gap), bw, bh),
            "quit": pygame.Rect(x, y0 + 6 * (bh + gap), bw, bh),
        }
        # Wybor jezyka: rzad flag w prawym gornym rogu (male ikonki panstw)
        self._flag_imgs = {}
        for code, _name, flag in i18n.LANGUAGES:
            try:
                img = pygame.image.load(os.path.join("images", "flags", flag + ".png"))
                self._flag_imgs[code] = pygame.transform.smoothscale(img, (44, 30))
            except Exception:
                self._flag_imgs[code] = None
        fw, fh, fgap, fmargin = 44, 30, 8, 14
        total_fw = len(i18n.LANGUAGES) * fw + (len(i18n.LANGUAGES) - 1) * fgap
        fx0 = self.rw - fmargin - total_fw
        self._flag_rects = [(code, pygame.Rect(fx0 + i * (fw + fgap), fmargin, fw, fh))
                            for i, (code, _n, _f) in enumerate(i18n.LANGUAGES)]

    def _load_resolution(self):
        """Wczytuje zapisana rozdzielczosc."""
        try:
            if os.path.exists("resolution.json"):
                with open("resolution.json") as f:
                    self.res_idx = json.load(f).get("res_idx", 4)
        except:
            pass

    def _save_resolution(self):
        try:
            with open("resolution.json", "w") as f:
                json.dump({"res_idx": self.res_idx}, f)
        except:
            pass

    def _cover_scale(self, img, tw, th):
        """Skaluje obraz zeby pokryc caly ekran (jak CSS background-size: cover).
        Wypelnia bez czarnych paskow, nadmiar przycina ze srodka."""
        iw, ih = img.get_size()
        scale = max(tw / iw, th / ih)
        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
        scaled = pygame.transform.smoothscale(img, (nw, nh))
        x = (nw - tw) // 2
        y = (nh - th) // 2
        return scaled.subsurface((x, y, tw, th)).copy()

    def draw_button(self, rect, text, hover):
        color = (46, 134, 193) if hover else (28, 90, 135)
        pygame.draw.rect(self.win, color, rect, border_radius=14)
        pygame.draw.rect(self.win, (255, 255, 255), rect, 2, border_radius=14)
        # Dopasuj czcionke do szerokosci przycisku - kurcz do dopasowania (30/26/22/18)
        # (wczesniej tylko jeden fallback do 22, dlugie etykiety nadal mogly sie przycinas na Windows/Arial)
        label = None
        for size in (30, 26, 22, 18):
            font = pygame.font.SysFont("arial", size, bold=True)
            label = font.render(text, True, (255, 255, 255))
            if label.get_width() <= rect.w - 24 and label.get_height() <= rect.h - 10:
                break
        self.win.blit(label, (rect.centerx - label.get_width() // 2,
                              rect.centery - label.get_height() // 2))

    def draw_title_wave(self):
        """Animowany tytul jak w filmach: fala powiekszajaca literki przechodzi w kolko."""
        import math
        t = pygame.time.get_ticks() / 1000.0
        text = "ISLAND DEFENDERS"
        base_size = 76
        # Szerokosci liter przy bazowym rozmiarze (do wycentrowania)
        base_font = self._title_font(base_size)
        widths = [base_font.size(ch)[0] for ch in text]
        total_w = sum(widths)
        x = self.rw // 2 - total_w // 2
        y_base = self.rh // 2 - 260
        for i, ch in enumerate(text):
            if ch == " ":
                x += widths[i]
                continue
            # Fala: sinus z przesunieciem fazowym na literke, podrozuje w kolko
            phase = t * 2.2 - i * 0.4
            s = math.sin(phase)
            scale = 1.0 + 0.22 * s
            size = max(20, int(base_size * scale))
            font = self._title_font(size)
            # Lekkie unoszenie przy powiekszeniu
            lift = int(14 * max(0, s))
            surf = font.render(ch, True, (255, 210, 63))
            sh = font.render(ch, True, (0, 0, 0))
            lx = x + (widths[i] - surf.get_width()) // 2
            ly = y_base + (base_size - surf.get_height()) // 2 - lift
            self.win.blit(sh, (lx + 3, ly + 3))
            self.win.blit(surf, (lx, ly))
            x += widths[i]

    def _title_font(self, size):
        if not hasattr(self, "_title_font_cache"):
            self._title_font_cache = {}
        if size not in self._title_font_cache:
            self._title_font_cache[size] = pygame.font.SysFont("arial", size, bold=True)
        return self._title_font_cache[size]

    def draw(self, mouse):
        self.win.blit(self.bg, (0, 0))
        shade = pygame.Surface((self.rw, self.rh), pygame.SRCALPHA)
        shade.fill((5, 10, 25, 150))
        self.win.blit(shade, (0, 0))

        # Animowany tytul - fala jak w filmach
        self.draw_title_wave()
        sub = self.small_font.render(t("menu.subtitle"),
                                      True, (220, 230, 240))
        self.win.blit(sub, (self.rw // 2 - sub.get_width() // 2, self.rh // 2 - 160))

        diff_name = DIFFICULTIES[self.diff_idx][0]
        res = self.resolutions[self.res_idx]
        res_name = f"{res[0]}x{res[1]}" if isinstance(res[0], int) else t("menu.native")
        labels = {
            "start": t("menu.start"),
            "diff": t("menu.difficulty", name=t("diff." + diff_name.lower())),
            "sound": t("menu.sound", state=t("common.on") if self.sound else t("common.off")),
            "achievements": t("menu.achievements"),
            "resolution": t("menu.resolution", name=res_name),
            "help": t("menu.help"),
            "quit": t("menu.quit"),
        }
        for key, rect in self.buttons.items():
            self.draw_button(rect, labels[key], rect.collidepoint(mouse))

        # Rzad flag wyboru jezyka (prawy gorny rog) - nie gdy otwarty jest panel
        if not (self.show_help or self.show_achievements or self.show_resolution):
            self._draw_flags(mouse)

        # Opis wybranej trudnosci (stopka - co zmienia EASY / NORMAL / HARD)
        diff_desc = t("diff." + diff_name.lower() + ".desc")
        if diff_desc:
            dtxt = self.small_font.render(diff_desc, True, (170, 180, 190))
            self.win.blit(dtxt, (self.rw // 2 - dtxt.get_width() // 2, self.rh - 30))

        if self.show_help:
            self.draw_help()
        if self.show_achievements:
            self.draw_achievements()
        if self.show_resolution:
            self.draw_resolution()
        pygame.display.update()

    def _draw_flags(self, mouse):
        """Rzad flag w prawym gornym rogu: wybrany jezyk ma zlota ramke,
        pod najechana flaga pokazuje sie nazwa jezyka (autonim)."""
        if not self._flag_rects:
            return
        x0 = self._flag_rects[0][1].x
        x1 = self._flag_rects[-1][1].right
        y0 = self._flag_rects[0][1].y
        pill = pygame.Surface((x1 - x0 + 16, 30 + 12), pygame.SRCALPHA)
        pygame.draw.rect(pill, (5, 10, 25, 130), pill.get_rect(), border_radius=10)
        self.win.blit(pill, (x0 - 8, y0 - 6))
        hovered_name = None
        for code, rect in self._flag_rects:
            img = self._flag_imgs.get(code)
            if img:
                self.win.blit(img, rect.topleft)
            if code == i18n.current():
                pygame.draw.rect(self.win, (255, 215, 100), rect, 3, border_radius=3)
            elif rect.collidepoint(mouse):
                pygame.draw.rect(self.win, (255, 255, 255), rect, 2, border_radius=3)
                hovered_name = i18n.LANG_NAMES[code]
            else:
                pygame.draw.rect(self.win, (140, 150, 165), rect, 1, border_radius=3)
        if hovered_name:
            lbl = self.small_font.render(hovered_name, True, (255, 215, 100))
            lx = min(max(4, x1 - lbl.get_width()), self.rw - lbl.get_width() - 4)
            self.win.blit(lbl, (lx, y0 + 38))

    def draw_achievements(self):
        """Panel achievementow (50) - karty w stylu CS2, PIRACKI klimat."""
        from achievements import AchievementManager
        if not hasattr(self, "_ach_mgr"):
            self._ach_mgr = AchievementManager()
        if not hasattr(self, "_ach_scroll"):
            self._ach_scroll = 0
        # Tlo: ciemne drewno okretowe
        self.win.fill((28, 20, 14))
        # Deski (poziome linie)
        for y in range(0, self.rh, 60):
            pygame.draw.line(self.win, (20, 14, 10), (0, y), (self.rw, y), 2)
        # Lina dekoracyjna na gorze (falista)
        for i in range(0, self.rw, 30):
            pygame.draw.circle(self.win, (101, 80, 50), (i, 8), 4)
        # Tytul: jak na mapie skarbow
        title = self.btn_font.render(t("ach.title"), True, (255, 215, 100))
        self.win.blit(title, (self.rw // 2 - title.get_width() // 2, 25))
        unlocked = len(self._ach_mgr.unlocked)
        total_ach = len(self._ach_mgr.get_all())
        sub = self.small_font.render(t("ach.found", unlocked=unlocked, total=total_ach), True, (180, 150, 110))
        self.win.blit(sub, (self.rw // 2 - sub.get_width() // 2, 65))
        # Monety po bokach tytulu
        pygame.draw.circle(self.win, (255, 215, 100), (self.rw//2 - 220, 50), 12)
        pygame.draw.circle(self.win, (200, 160, 70), (self.rw//2 - 220, 50), 12, 2)
        pygame.draw.circle(self.win, (255, 215, 100), (self.rw//2 + 220, 50), 12)
        pygame.draw.circle(self.win, (200, 160, 70), (self.rw//2 + 220, 50), 12, 2)
        # Obszar listy
        list_y0 = 110
        list_h = self.rh - 165
        clip = pygame.Rect(0, list_y0, self.rw, list_h)
        self.win.set_clip(clip)
        all_ach = self._ach_mgr.get_all()
        # Dwie kolumny kart
        col_w = 480
        gap = 20
        total_w = col_w * 2 + gap
        sx = (self.rw - total_w) // 2
        row_h = 86
        y = list_y0 - self._ach_scroll
        for i in range(0, len(all_ach), 2):
            if y + row_h < list_y0 or y > list_y0 + list_h:
                y += row_h + 12
                continue
            for col in range(2):
                idx = i + col
                if idx >= len(all_ach):
                    break
                aid, name, desc, icon_cat, is_unlocked = all_ach[idx]
                cx = sx + col * (col_w + gap)
                # Karta: pergamin/skrzynia
                card = pygame.Rect(cx, y, col_w, row_h)
                if is_unlocked:
                    # Zlota skrzynia skarbow
                    pygame.draw.rect(self.win, (52, 38, 24), card, border_radius=10)
                    pygame.draw.rect(self.win, (255, 215, 100), card, 2, border_radius=10)
                    # Nity w rogach (jak skrzynia)
                    for nx, ny in [(cx+8, y+8), (cx+col_w-8, y+8), (cx+8, y+row_h-8), (cx+col_w-8, y+row_h-8)]:
                        pygame.draw.circle(self.win, (180, 150, 90), (nx, ny), 3)
                else:
                    # Zamknieta skrzynia
                    pygame.draw.rect(self.win, (38, 28, 18), card, border_radius=10)
                    pygame.draw.rect(self.win, (90, 70, 45), card, 1, border_radius=10)
                # Ikona
                icon = self._ach_mgr.icons.get(icon_cat)
                if icon:
                    ic = pygame.transform.smoothscale(icon, (64, 64))
                    if not is_unlocked:
                        gray = pygame.Surface((64, 64), pygame.SRCALPHA)
                        gray.fill((60, 60, 60, 170))
                        ic.blit(gray, (0, 0))
                    pygame.draw.rect(self.win, (20, 14, 10), (cx + 11, y + 11, 64, 64), border_radius=6)
                    self.win.blit(ic, (cx + 11, y + 11))
                # Tytul i opis
                tcol = (255, 230, 170) if is_unlocked else (120, 105, 85)
                nm = self.btn_font_small.render(name, True, tcol)
                self.win.blit(nm, (cx + 88, y + 14))
                dcol = (190, 165, 130) if is_unlocked else (95, 85, 70)
                # Wrap po szerokosci w pikselach - 38 znakow przy 22px wychodzilo poza karte
                max_desc_w = col_w - 88 - 12
                words = desc.split()
                lines, cur = [], ""
                for w in words:
                    test = (cur + " " + w).strip()
                    if cur and self.small_font.size(test)[0] > max_desc_w:
                        lines.append(cur)
                        cur = w
                    else:
                        cur = test
                if cur:
                    lines.append(cur)
                full_lines = lines
                truncated = len(full_lines) > 2
                # Hover-scroll: najedzona karta z dluzszym opisem przewija go
                # w dol w oknie 2 linii (0.5 s zwloki, 26 px/s), zeby dalo sie
                # przeczytac calosc w kazdym jezyku; po wyjechaniu myszy
                # wraca forma ucieta z "..."
                if not hasattr(self, "_ach_hover"):
                    self._ach_hover = {}
                _now = pygame.time.get_ticks() / 1000.0
                if card.collidepoint(pygame.mouse.get_pos()):
                    self._ach_hover.setdefault(aid, _now)
                    _hstart = self._ach_hover[aid]
                else:
                    self._ach_hover.pop(aid, None)
                    _hstart = None
                scroll_off = 0.0
                if truncated and _hstart is not None:
                    scroll_off = min((len(full_lines) - 2) * 20,
                                     max(0.0, (_now - _hstart - 0.5)) * 26.0)
                if truncated and scroll_off <= 0:
                    lines = full_lines[:2]
                    while len(lines) > 1 and self.small_font.size(lines[1] + "…")[0] > max_desc_w and len(lines[1]) > 1:
                        lines[1] = lines[1][:-1].rstrip()
                    lines[1] = lines[1] + "…"
                else:
                    lines = full_lines
                if scroll_off > 0:
                    _clip = pygame.Rect(cx + 88, y + 40, max_desc_w + 4, 40)
                    _prev_clip = self.win.get_clip()
                    self.win.set_clip(_clip)
                    for li, ln in enumerate(full_lines):
                        ly = y + 40 + li * 20 - int(scroll_off)
                        if ly + 20 < _clip.top or ly > _clip.bottom:
                            continue
                        self.win.blit(self.small_font.render(ln, True, dcol), (cx + 88, ly))
                    self.win.set_clip(_prev_clip)
                else:
                    if len(lines) >= 1:
                        d1 = self.small_font.render(lines[0], True, dcol)
                        self.win.blit(d1, (cx + 88, y + 40))
                    if len(lines) >= 2:
                        d2 = self.small_font.render(lines[1], True, dcol)
                        self.win.blit(d2, (cx + 88, y + 60))
            y += row_h + 12
        self.win.set_clip(None)
        # Scrollbar: lina
        total_h = (len(all_ach) // 2) * (row_h + 12)
        if total_h > list_h:
            bar_h = max(40, int(list_h * list_h / total_h))
            bar_y = list_y0 + int(self._ach_scroll * (list_h - bar_h) / max(1, total_h - list_h))
            pygame.draw.rect(self.win, (101, 80, 50), (self.rw - 18, bar_y, 8, bar_h), border_radius=4)
        # Dolny hint
        hint = self.small_font.render(t("ach.scroll"), True, (140, 120, 90))
        self.win.blit(hint, (self.rw // 2 - hint.get_width() // 2, self.rh - 55))
        # Przycisk zamkniecia (X)
        close_rect = pygame.Rect(self.rw - 60, 20, 40, 40)
        pygame.draw.rect(self.win, (120, 50, 50), close_rect, border_radius=8)
        x_lbl = self.btn_font_small.render("X", True, (255, 255, 255))
        self.win.blit(x_lbl, (close_rect.centerx - x_lbl.get_width()//2,
                              close_rect.centery - x_lbl.get_height()//2))
        self._ach_close_rect = close_rect
        self._ach_max_scroll = max(0, total_h - list_h)

    def draw_resolution(self):
        """Panel wyboru rozdzielczosci."""
        dim = pygame.Surface((self.rw, self.rh), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        self.win.blit(dim, (0, 0))
        pw, ph = 500, 400
        px, py = (self.rw - pw) // 2, (self.rh - ph) // 2
        pygame.draw.rect(self.win, (25, 30, 40), (px, py, pw, ph), border_radius=15)
        pygame.draw.rect(self.win, (100, 200, 255), (px, py, pw, ph), 2, border_radius=15)
        title = self.btn_font.render(t("res.title"), True, (100, 200, 255))
        self.win.blit(title, (px + (pw - title.get_width()) // 2, py + 20))
        # Opcje
        self._res_buttons = []
        for i, res in enumerate(self.resolutions):
            name = f"{res[0]}x{res[1]}" if isinstance(res[0], int) else t("res.native_full")
            bw, bh = 320, 44
            bx, by = px + (pw - bw) // 2, py + 80 + i * 56
            rect = pygame.Rect(bx, by, bw, bh)
            self._res_buttons.append((rect, i))
            col = (255, 215, 100) if i == self.res_idx else (80, 90, 100)
            pygame.draw.rect(self.win, col, rect, 3 if i == self.res_idx else 1, border_radius=8)
            lbl = self.btn_font_small.render(name, True, (255, 255, 255))
            self.win.blit(lbl, (bx + (bw - lbl.get_width()) // 2, by + 12))
        hint = self.small_font.render(t("res.applies"), True, (150, 150, 150))
        self.win.blit(hint, (px + (pw - hint.get_width()) // 2, py + ph - 35))

    def draw_help(self):
        # Panel: wysokosc DOKLADNIE na miare tresci (wczesniej stale 560,
        # a tresc potrzebuje 567 - ostatnia linia wystawala poza panel).
        _steps = {"title": 40, "header": 30, "dim": 30, "text": 26, "spacer": 12}
        _lines = [
            ("sm.help.title", "title"),
            ("", "spacer"),
            ("sm.help.l1", "text"),
            ("sm.help.l2", "text"),
            ("sm.help.l3", "text"),
            ("sm.help.l4", "text"),
            ("", "spacer"),
            ("sm.help.controls", "header"),
            ("sm.help.c1", "text"),
            ("sm.help.c2", "text"),
            ("sm.help.c3", "text"),
            ("sm.help.c4", "text"),
            ("sm.help.c5", "text"),
            ("sm.help.c6", "text"),
            ("sm.help.c7", "text"),
            ("sm.help.c8", "text"),
            ("", "spacer"),
            ("sm.help.tips", "header"),
            ("sm.help.t1", "text"),
            ("sm.help.t2", "text"),
            ("", "spacer"),
            ("sm.help.back", "dim"),
        ]
        _total = 25 + sum(_steps[s] for _, s in _lines) + 20
        panel = pygame.Rect(self.rw // 2 - 360, self.rh // 2 - _total // 2, 720, _total)
        pygame.draw.rect(self.win, (12, 24, 44), panel, border_radius=16)
        pygame.draw.rect(self.win, (255, 255, 255), panel, 2, border_radius=16)
        lines = _lines
        y = panel.y + 25
        for line, style in lines:
            if style == "spacer":
                y += 12
                continue
            if style == "title":
                f, c, step = self.btn_font, (255, 210, 63), 40
            elif style == "header":
                f, c, step = self.small_font, (255, 210, 63), 30
            elif style == "dim":
                f, c, step = self.small_font, (140, 150, 160), 30
            else:
                f, c, step = self.small_font, (225, 232, 240), 26
            t_surf = f.render(t(line), True, c)
            self.win.blit(t_surf, (panel.centerx - t_surf.get_width() // 2, y))
            y += step

    def run(self):
        """Petla menu. Zwraca slownik z ustawieniami albo None przy wyjsciu."""
        # Muzyka w menu (jesli dzwiek wlaczony)
        try:
            if self.sound:
                pygame.mixer.music.load(os.path.join("sounds", "music.wav"))
                pygame.mixer.music.play(loops=-1)
        except:
            pass
        running = True
        while running:
            self.clock.tick(60)
            mouse = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.mixer.music.stop()
                    return None
                # Scroll w achievementach
                if event.type == pygame.MOUSEWHEEL and self.show_achievements:
                    if hasattr(self, "_ach_max_scroll"):
                        self._ach_scroll = max(0, min(self._ach_max_scroll,
                                                      self._ach_scroll - event.y * 40))
                    continue
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Dzwiek klikniecia TYLKO gdy klik faktycznie w cos trafil
                    # (przycisk, zamkniecie panelu, opcja) - nie przy kliku
                    # w puste miejsce i nie przy scrollu (przyciski 4/5 kola).
                    clicked_something = False
                    # Achievements: zamknij tylko przez X (nie przez klik w panel)
                    if self.show_achievements:
                        if hasattr(self, "_ach_close_rect") and self._ach_close_rect.collidepoint(event.pos):
                            self.show_achievements = False
                            clicked_something = True
                    # Resolution: wybor opcji
                    elif self.show_resolution and hasattr(self, "_res_buttons"):
                        pos = event.pos
                        for rect, idx in self._res_buttons:
                            if rect.collidepoint(pos):
                                self.res_idx = idx
                                self._save_resolution()
                                clicked_something = True
                                break
                        else:
                            self.show_resolution = False
                            clicked_something = True
                    elif self.show_help or self.show_resolution:
                        self.show_help = False
                        self.show_resolution = False
                        clicked_something = True
                    else:
                        pos = event.pos
                        # Flagi jezyka (prawy gorny rog): przelaczaja od razu
                        _flag_hit = False
                        for _code, _frect in self._flag_rects:
                            if _frect.collidepoint(pos):
                                i18n.set_language(_code)
                                clicked_something = True
                                _flag_hit = True
                                break
                        if _flag_hit:
                            pass
                        elif self.buttons["start"].collidepoint(pos):
                            clicked_something = True
                            if clicked_something and self.click_sound and self.sound:
                                self.click_sound.play()
                            pygame.mixer.music.stop()
                            name, lives, money = DIFFICULTIES[self.diff_idx]
                            return {"difficulty": name, "lives": lives,
                                    "money": money, "sound": self.sound,
                                    "res_idx": self.res_idx}
                        elif self.buttons["diff"].collidepoint(pos):
                            self.diff_idx = (self.diff_idx + 1) % len(DIFFICULTIES)
                            clicked_something = True
                        elif self.buttons["sound"].collidepoint(pos):
                            self.sound = not self.sound
                            clicked_something = True
                            # Wlacz/wylacz muzyke w menu na biezaco
                            try:
                                if self.sound:
                                    pygame.mixer.music.play(loops=-1)
                                else:
                                    pygame.mixer.music.stop()
                            except:
                                pass
                        elif self.buttons["achievements"].collidepoint(pos):
                            self.show_achievements = True
                            clicked_something = True
                        elif self.buttons["resolution"].collidepoint(pos):
                            self.show_resolution = True
                            clicked_something = True
                        elif self.buttons["help"].collidepoint(pos):
                            self.show_help = True
                            clicked_something = True
                        elif self.buttons["quit"].collidepoint(pos):
                            clicked_something = True
                            if clicked_something and self.click_sound and self.sound:
                                self.click_sound.play()
                            pygame.mixer.music.stop()
                            return None
                    if clicked_something and self.click_sound and self.sound:
                        self.click_sound.play()
            self.draw(mouse)
