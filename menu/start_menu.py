import pygame
import os
import json

DIFFICULTIES = [
    ("EASY", 30, 300),
    ("NORMAL", 20, 200),
    ("HARD", 12, 150),
]

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
        y0 = self.rh // 2 - 80
        self.buttons = {
            "start": pygame.Rect(x, y0, bw, bh),
            "diff": pygame.Rect(x, y0 + (bh + gap), bw, bh),
            "sound": pygame.Rect(x, y0 + 2 * (bh + gap), bw, bh),
            "achievements": pygame.Rect(x, y0 + 3 * (bh + gap), bw, bh),
            "resolution": pygame.Rect(x, y0 + 4 * (bh + gap), bw, bh),
            "help": pygame.Rect(x, y0 + 5 * (bh + gap), bw, bh),
            "quit": pygame.Rect(x, y0 + 6 * (bh + gap), bw, bh),
        }

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
        # Dopasuj czcionke do szerokosci przycisku (DIFFICULTY: NORMAL bylo za dlugie)
        font = self.btn_font
        label = font.render(text, True, (255, 255, 255))
        if label.get_width() > rect.w - 30:
            font = self.btn_font_small
            label = font.render(text, True, (255, 255, 255))
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
        sub = self.small_font.render("Defend Vancouver Island from the monster-pirates!",
                                      True, (220, 230, 240))
        self.win.blit(sub, (self.rw // 2 - sub.get_width() // 2, self.rh // 2 - 160))

        diff_name = DIFFICULTIES[self.diff_idx][0]
        res = self.resolutions[self.res_idx]
        res_name = f"{res[0]}x{res[1]}" if isinstance(res[0], int) else "NATIVE"
        labels = {
            "start": "START GAME",
            "diff": "DIFFICULTY: " + diff_name,
            "sound": "SOUND: " + ("ON" if self.sound else "OFF"),
            "achievements": "ACHIEVEMENTS",
            "resolution": "RESOLUTION: " + res_name,
            "help": "HOW TO PLAY",
            "quit": "QUIT",
        }
        for key, rect in self.buttons.items():
            self.draw_button(rect, labels[key], rect.collidepoint(mouse))

        if self.show_help:
            self.draw_help()
        if self.show_achievements:
            self.draw_achievements()
        if self.show_resolution:
            self.draw_resolution()
        pygame.display.update()

    def draw_achievements(self):
        """Panel achievementow (50) - scrollowana lista."""
        from achievements import AchievementManager
        if not hasattr(self, "_ach_mgr"):
            self._ach_mgr = AchievementManager()
        if not hasattr(self, "_ach_scroll"):
            self._ach_scroll = 0
        # Przyciemnienie
        dim = pygame.Surface((self.rw, self.rh), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        self.win.blit(dim, (0, 0))
        # Panel
        pw, ph = 700, 600
        px, py = (self.rw - pw) // 2, (self.rh - ph) // 2
        pygame.draw.rect(self.win, (25, 30, 40), (px, py, pw, ph), border_radius=15)
        pygame.draw.rect(self.win, (255, 215, 100), (px, py, pw, ph), 2, border_radius=15)
        title = self.btn_font.render("ACHIEVEMENTS", True, (255, 215, 100))
        self.win.blit(title, (px + (pw - title.get_width()) // 2, py + 15))
        unlocked = len(self._ach_mgr.unlocked)
        sub = self.small_font.render(f"{unlocked}/50 unlocked", True, (200, 200, 200))
        self.win.blit(sub, (px + (pw - sub.get_width()) // 2, py + 55))
        # Obszar listy (clip)
        list_y0 = py + 95
        list_h = ph - 140
        clip = pygame.Rect(px + 20, list_y0, pw - 40, list_h)
        self.win.set_clip(clip)
        all_ach = self._ach_mgr.get_all()
        row_h = 70
        y = list_y0 - self._ach_scroll
        for aid, name, desc, icon_cat, is_unlocked in all_ach:
            if y + row_h < list_y0 or y > list_y0 + list_h:
                y += row_h
                continue
            # Tlo wiersza
            bg_col = (35, 42, 55) if is_unlocked else (25, 28, 35)
            pygame.draw.rect(self.win, bg_col, (px + 25, y, pw - 50, row_h - 8), border_radius=8)
            if is_unlocked:
                pygame.draw.rect(self.win, (255, 215, 100, 80), (px + 25, y, pw - 50, row_h - 8), 1, border_radius=8)
            # Ikona
            icon = self._ach_mgr.icons.get(icon_cat)
            if icon:
                ic = pygame.transform.smoothscale(icon, (48, 48))
                if not is_unlocked:
                    gray = pygame.Surface((48, 48), pygame.SRCALPHA)
                    gray.fill((100, 100, 100, 160))
                    ic.blit(gray, (0, 0))
                self.win.blit(ic, (px + 35, y + 7))
            # Nazwa i opis
            ncol = (255, 255, 255) if is_unlocked else (130, 130, 130)
            nm = self.btn_font_small.render(name, True, ncol)
            self.win.blit(nm, (px + 95, y + 8))
            # Opis (mniejsza czcionka, zawijanie niepotrzebne - krotkie)
            ds = self.small_font.render(desc[:60], True, (150, 150, 150) if is_unlocked else (100, 100, 100))
            self.win.blit(ds, (px + 95, y + 32))
            y += row_h
        self.win.set_clip(None)
        # Scrollbar
        total_h = len(all_ach) * row_h
        if total_h > list_h:
            bar_h = max(40, int(list_h * list_h / total_h))
            bar_y = list_y0 + int(self._ach_scroll * (list_h - bar_h) / (total_h - list_h))
            pygame.draw.rect(self.win, (80, 90, 100), (px + pw - 18, bar_y, 8, bar_h), border_radius=4)
        # Hint
        hint = self.small_font.render("Scroll with mouse wheel - click outside to close", True, (150, 150, 150))
        self.win.blit(hint, (px + (pw - hint.get_width()) // 2, py + ph - 32))
        # Zapisz max scroll
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
        title = self.btn_font.render("RESOLUTION", True, (100, 200, 255))
        self.win.blit(title, (px + (pw - title.get_width()) // 2, py + 20))
        # Opcje
        self._res_buttons = []
        for i, res in enumerate(self.resolutions):
            name = f"{res[0]}x{res[1]}" if isinstance(res[0], int) else "NATIVE FULLSCREEN"
            bw, bh = 320, 44
            bx, by = px + (pw - bw) // 2, py + 80 + i * 56
            rect = pygame.Rect(bx, by, bw, bh)
            self._res_buttons.append((rect, i))
            col = (255, 215, 100) if i == self.res_idx else (80, 90, 100)
            pygame.draw.rect(self.win, col, rect, 3 if i == self.res_idx else 1, border_radius=8)
            lbl = self.btn_font_small.render(name, True, (255, 255, 255))
            self.win.blit(lbl, (bx + (bw - lbl.get_width()) // 2, by + 12))
        hint = self.small_font.render("Applies on next game start", True, (150, 150, 150))
        self.win.blit(hint, (px + (pw - hint.get_width()) // 2, py + ph - 35))

    def draw_help(self):
        panel = pygame.Rect(self.rw // 2 - 360, self.rh // 2 - 280, 720, 560)
        pygame.draw.rect(self.win, (12, 24, 44), panel, border_radius=16)
        pygame.draw.rect(self.win, (255, 255, 255), panel, 2, border_radius=16)
        lines = [
            ("HOW TO PLAY", "title"),
            ("", "spacer"),
            ("Build towers from the right panel, then click", "text"),
            ("on the map to place them.", "text"),
            ("Monster-pirates follow the dirt road.", "text"),
            ("Don't let them reach your base!", "text"),
            ("", "spacer"),
            ("CONTROLS", "header"),
            ("1-5  Buy tower      |  U  Upgrade tower", "text"),
            ("S  Sell tower      |  Q  Tower ability", "text"),
            ("T  Target priority |  R  Show all ranges", "text"),
            ("Space  Pause       |  F  Toggle 1x/3x speed", "text"),
            ("M  Mute            |  C  Filter towers by type", "text"),
            ("Shift+Click  Queue build / Quick sell", "text"),
            ("Ctrl+Z  Undo last build or upgrade", "text"),
            ("F5 / F9  Save / Load game", "text"),
            ("", "spacer"),
            ("TIPS", "header"),
            ("Same-type towers next to each other: +15% damage.", "text"),
            ("Gold elites give 5x gold. Watch for rain: +15% gold!", "text"),
            ("", "spacer"),
            ("Click anywhere to go back.", "dim"),
        ]
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
            t = f.render(line, True, c)
            self.win.blit(t, (panel.centerx - t.get_width() // 2, y))
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
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.click_sound and self.sound:
                        self.click_sound.play()
                    if self.show_resolution and hasattr(self, "_res_buttons"):
                        pos = event.pos
                        for rect, idx in self._res_buttons:
                            if rect.collidepoint(pos):
                                self.res_idx = idx
                                self._save_resolution()
                                break
                        else:
                            self.show_resolution = False
                        continue
                    if self.show_help or self.show_achievements or self.show_resolution:
                        self.show_help = False
                        self.show_achievements = False
                        self.show_resolution = False
                        continue
                    pos = event.pos
                    if self.buttons["start"].collidepoint(pos):
                        pygame.mixer.music.stop()
                        name, lives, money = DIFFICULTIES[self.diff_idx]
                        return {"difficulty": name, "lives": lives,
                                "money": money, "sound": self.sound,
                                "res_idx": self.res_idx}
                    elif self.buttons["diff"].collidepoint(pos):
                        self.diff_idx = (self.diff_idx + 1) % len(DIFFICULTIES)
                    elif self.buttons["sound"].collidepoint(pos):
                        self.sound = not self.sound
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
                    elif self.buttons["resolution"].collidepoint(pos):
                        self.show_resolution = True
                    elif self.buttons["help"].collidepoint(pos):
                        self.show_help = True
                    elif self.buttons["quit"].collidepoint(pos):
                        pygame.mixer.music.stop()
                        return None
            self.draw(mouse)
