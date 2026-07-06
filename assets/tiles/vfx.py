import pygame
import random
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

class RainDrop:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(-SCREEN_HEIGHT, 0)
        self.speed = random.randint(25, 40) # Nopeampi
        self.len = random.randint(20, 40)   # Pidempi
        self.wind = -4 # Voimakkaampi tuuli

    def update(self):
        self.y += self.speed
        self.x += self.wind
        if self.y > SCREEN_HEIGHT:
            return True # Osui maahan
        return False

    def draw(self, screen):
        # Harmaa/sinertävä sade
        pygame.draw.line(screen, (150, 150, 180, 150), (self.x, self.y), (self.x + self.wind, self.y + self.len), 1)

class RainSplash:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = 0
        self.duration = 10

    def update(self):
        self.timer += 1
        return self.timer < self.duration

    def draw(self, screen, offset):
        # Pieni roiske maassa
        sx = self.x - offset[0]
        sy = self.y - offset[1]
        if 0 < sx < SCREEN_WIDTH and 0 < sy < SCREEN_HEIGHT:
            w = int(self.timer * 1.5)
            h = int(self.timer * 0.5)
            pygame.draw.ellipse(screen, (200, 200, 220, 100), (sx - w//2, sy - h//2, w, h), 1)

class ChimneySmoke:
    def __init__(self, map_w, map_h):
        self.x = random.randint(0, map_w)
        self.y = random.randint(0, map_h)
        self.radius = random.randint(5, 10)
        self.alpha = 150
        self.life = 100

    def update(self):
        self.y -= 1
        self.x += random.uniform(-0.5, 0.5)
        self.radius += 0.1
        self.alpha -= 1.5
        return self.alpha > 0

    def draw(self, screen, offset):
        sx = self.x - offset[0]
        sy = self.y - offset[1]
        if -50 < sx < SCREEN_WIDTH + 50 and -50 < sy < SCREEN_HEIGHT + 50:
            s = pygame.Surface((int(self.radius*2), int(self.radius*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (50, 50, 50, int(self.alpha)), (int(self.radius), int(self.radius)), int(self.radius))
            screen.blit(s, (sx - self.radius, sy - self.radius))

class MapVFX:
    def __init__(self):
        self.rain = [RainDrop() for _ in range(400)] # Enemmän pisaroita
        self.splashes = []
        self.smoke = []
        self.map_w = int(SCREEN_WIDTH * 3.0)
        self.map_h = int(SCREEN_HEIGHT * 3.0)

    def update(self, manager):
        # Rain update
        for r in self.rain:
            if r.update():
                # Osui maahan -> Roiske (jos ruudulla)
                # Koska sade on screen-space, roiskeen paikka on screen-space + camera
                cam_x = getattr(manager, "camera_x", 0)
                cam_y = getattr(manager, "camera_y", 0)
                
                # Luodaan roiske maailmakoordinaatteihin
                self.splashes.append(RainSplash(r.x + cam_x, SCREEN_HEIGHT + cam_y + random.randint(-20, 20)))
                
                # Resetoi pisara
                r.y = random.randint(-50, -10)
                r.x = random.randint(0, SCREEN_WIDTH + 100)
        
        self.splashes = [s for s in self.splashes if s.update()]

        if random.random() < 0.1:
            self.smoke.append(ChimneySmoke(self.map_w, self.map_h))
        self.smoke = [s for s in self.smoke if s.update()]

    def draw_floor(self, screen, offset):
        for s in self.splashes: s.draw(screen, offset)

    def draw_top(self, screen, offset):
        for s in self.smoke: s.draw(screen, offset)
        for r in self.rain: r.draw(screen)