import pygame
import os

class Game:
    def __init__(self):
        self.width = 1024
        self.height = 720
        self.window = pygame.display.set_mode((self.width, self.height))
        self.enemies = []
        self.towers = []
        self.progress = 0
        self.money = 1000
        self.bg = pygame.image.load(os.path.join("images", "bg.png"))
        self.bg = pygame.transform.scale(self.bg, (self.width, self.height))
        self.clicks = [] #remove afterwards 
        
    def run(self):
        run = True
        clock = pygame.time.Clock()
        
        while run:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    
                pos = pygame.mouse.get_pos()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.clicks.append(pos)
                    print(self.clicks)
            self.draw()
        pygame.quit
        
    def draw(self):
        self.window.blit(self.bg, (0,0))
        for p in self.clicks:
            pygame.draw.circle(self.window, (255,0,0), (p[0], p[1]), 5, 0)
        pygame.display.update()
        
g = Game()
g.run()