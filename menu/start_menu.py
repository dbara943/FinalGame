import pygame
import os

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
        self.win = pygame.display.set_mode((width, height), pygame.SCALED | pygame.FULLSCREEN)
        pygame.display.set_caption("Island Defenders")
        self.bg = pygame.transform.scale(bg, (width, height))
        # Dzwiek klikniecia w menu
        try:
            pygame.mixer.init()
            self.click_sound = pygame.mixer.Sound(os.path.join("sounds", "4.wav"))
        except:
            self.click_sound = None
        pygame.display.set_caption("Island Defenders")
        self.bg = pygame.transform.scale(bg, (width, height))
        self.title_font = pygame.font.SysFont("arial", 76, bold=True)
        self.btn_font = pygame.font.SysFont("arial", 30, bold=True)
        self.small_font = pygame.font.SysFont("arial", 22)
        self.diff_idx = 1  # domyslnie NORMAL
        self.sound = True
        self.show_help = False
        self.clock = pygame.time.Clock()

        bw, bh, gap = 360, 60, 14
        x = width // 2 - bw // 2
        y0 = 320
        self.buttons = {
            "start": pygame.Rect(x, y0, bw, bh),
            "diff": pygame.Rect(x, y0 + (bh + gap), bw, bh),
            "sound": pygame.Rect(x, y0 + 2 * (bh + gap), bw, bh),
            "help": pygame.Rect(x, y0 + 3 * (bh + gap), bw, bh),
            "quit": pygame.Rect(x, y0 + 4 * (bh + gap), bw, bh),
        }

    def draw_button(self, rect, text, hover):
        color = (46, 134, 193) if hover else (28, 90, 135)
        pygame.draw.rect(self.win, color, rect, border_radius=14)
        pygame.draw.rect(self.win, (255, 255, 255), rect, 2, border_radius=14)
        label = self.btn_font.render(text, True, (255, 255, 255))
        self.win.blit(label, (rect.centerx - label.get_width() // 2,
                              rect.centery - label.get_height() // 2))

    def draw(self, mouse):
        self.win.blit(self.bg, (0, 0))
        shade = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        shade.fill((5, 10, 25, 150))
        self.win.blit(shade, (0, 0))

        shadow = self.title_font.render("ISLAND DEFENDERS", True, (0, 0, 0))
        title = self.title_font.render("ISLAND DEFENDERS", True, (255, 210, 63))
        tx = self.width // 2 - title.get_width() // 2
        self.win.blit(shadow, (tx + 4, 104))
        self.win.blit(title, (tx, 100))
        sub = self.small_font.render("Defend Vancouver Island from the monster-pirates!",
                                      True, (220, 230, 240))
        self.win.blit(sub, (self.width // 2 - sub.get_width() // 2, 200))

        diff_name = DIFFICULTIES[self.diff_idx][0]
        labels = {
            "start": "START GAME",
            "diff": "DIFFICULTY: " + diff_name,
            "sound": "SOUND: " + ("ON" if self.sound else "OFF"),
            "help": "HOW TO PLAY",
            "quit": "QUIT",
        }
        for key, rect in self.buttons.items():
            self.draw_button(rect, labels[key], rect.collidepoint(mouse))

        if self.show_help:
            self.draw_help()
        pygame.display.update()

    def draw_help(self):
        panel = pygame.Rect(self.width // 2 - 360, self.height // 2 - 280, 720, 560)
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
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.click_sound and self.sound:
                        self.click_sound.play()
                    if self.show_help:
                        self.show_help = False
                        continue
                    pos = event.pos
                    if self.buttons["start"].collidepoint(pos):
                        pygame.mixer.music.stop()
                        name, lives, money = DIFFICULTIES[self.diff_idx]
                        return {"difficulty": name, "lives": lives,
                                "money": money, "sound": self.sound}
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
                    elif self.buttons["help"].collidepoint(pos):
                        self.show_help = True
                    elif self.buttons["quit"].collidepoint(pos):
                        pygame.mixer.music.stop()
                        return None
            self.draw(mouse)
