import pygame

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
        self.win = pygame.display.set_mode((width, height))
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
        panel = pygame.Rect(self.width // 2 - 330, self.height // 2 - 220, 660, 440)
        pygame.draw.rect(self.win, (12, 24, 44), panel, border_radius=16)
        pygame.draw.rect(self.win, (255, 255, 255), panel, 2, border_radius=16)
        lines = [
            "HOW TO PLAY",
            "",
            "- Click a tower in the right panel, then click",
            "  on the map to build it.",
            "- Monster-pirates follow the dirt road.",
            "  Don't let them reach your base!",
            "- Click a built tower to upgrade it (max level 3).",
            "- You earn money for every defeated enemy.",
            "- Survive all 12 waves to win.",
            "",
            "Click anywhere to go back.",
        ]
        y = panel.y + 30
        for i, line in enumerate(lines):
            f = self.btn_font if i == 0 else self.small_font
            c = (255, 210, 63) if i == 0 else (225, 232, 240)
            t = f.render(line, True, c)
            self.win.blit(t, (panel.centerx - t.get_width() // 2, y))
            y += 40 if i == 0 else 30

    def run(self):
        """Petla menu. Zwraca slownik z ustawieniami albo None przy wyjsciu."""
        running = True
        while running:
            self.clock.tick(60)
            mouse = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.show_help:
                        self.show_help = False
                        continue
                    pos = event.pos
                    if self.buttons["start"].collidepoint(pos):
                        name, lives, money = DIFFICULTIES[self.diff_idx]
                        return {"difficulty": name, "lives": lives,
                                "money": money, "sound": self.sound}
                    elif self.buttons["diff"].collidepoint(pos):
                        self.diff_idx = (self.diff_idx + 1) % len(DIFFICULTIES)
                    elif self.buttons["sound"].collidepoint(pos):
                        self.sound = not self.sound
                    elif self.buttons["help"].collidepoint(pos):
                        self.show_help = True
                    elif self.buttons["quit"].collidepoint(pos):
                        return None
            self.draw(mouse)
