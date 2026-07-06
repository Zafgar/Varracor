import pygame
import random
import math
from sound_manager import sound_system

class CryptFlies:
    """
    Luo pieniä mustia/harmaita hiukkasia (kärpäsiä/pölyä), jotka pörräävät alueella.
    """
    def __init__(self, area_w, area_h, count=30):
        self.area_w = area_w
        self.area_h = area_h
        self.flies = []
        for _ in range(count):
            self.flies.append(self._create_fly())

    def _create_fly(self):
        return {
            'x': random.randint(0, self.area_w),
            'y': random.randint(0, self.area_h),
            'vx': random.uniform(-2, 2),
            'vy': random.uniform(-2, 2),
            'timer': random.randint(0, 60),
            'size': random.randint(1, 2)
        }

    def update(self):
        for f in self.flies:
            f['x'] += f['vx']
            f['y'] += f['vy']
            f['timer'] += 1
            
            # Vaihda suuntaa satunnaisesti
            if f['timer'] % 40 == 0:
                f['vx'] += random.uniform(-1, 1)
                f['vy'] += random.uniform(-1, 1)
                # Rajoita nopeutta
                f['vx'] = max(-3, min(3, f['vx']))
                f['vy'] = max(-3, min(3, f['vy']))

            # Pysy alueella (wrap around)
            if f['x'] < 0: f['x'] = self.area_w
            if f['x'] > self.area_w: f['x'] = 0
            if f['y'] < 0: f['y'] = self.area_h
            if f['y'] > self.area_h: f['y'] = 0

    def draw(self, screen, offset):
        for f in self.flies:
            dx = f['x'] - offset[0]
            dy = f['y'] - offset[1]
            # Piirretään vain jos ruudulla
            if -10 < dx < 2000 and -10 < dy < 1200:
                pygame.draw.rect(screen, (10, 10, 15), (dx, dy, f['size'], f['size']))

class VortexPortal(pygame.sprite.Sprite):
    """
    Pyörivä portaali maassa, josta viholliset spawnaavat.
    """
    def __init__(self, x, y, duration=180):
        super().__init__()
        self.x = x
        self.y = y
        self.duration = duration
        self.timer = 0
        self.angle = 0
        self.max_size = 80
        
        # Luodaan staattinen pohjakuva (spiraali)
        self.base_image = pygame.Surface((self.max_size*2, self.max_size*2), pygame.SRCALPHA)
        cx, cy = self.max_size, self.max_size
        
        # Ulkokehä (tumma violetti hehku)
        pygame.draw.circle(self.base_image, (50, 0, 80, 100), (cx, cy), self.max_size)
        # Sisäosa (musta aukko)
        pygame.draw.circle(self.base_image, (20, 0, 30, 200), (cx, cy), int(self.max_size * 0.7))
        
        # Spiraaliviivat
        for i in range(6):
            start_a = i * (math.pi / 3)
            points = []
            for r in range(10, int(self.max_size * 0.9), 5):
                a = start_a + (r * 0.1)
                px = cx + math.cos(a) * r
                py = cy + math.sin(a) * r
                points.append((px, py))
            if len(points) > 1:
                pygame.draw.lines(self.base_image, (150, 50, 200), False, points, 3)

        self.image = self.base_image
        self.rect = self.image.get_rect(center=(x, y))
        
        # Audio
        sound_system.play_sound("vortex_spawn")
        self.loop_channel = sound_system.play_sound("vortex_loop", loops=-1)

    def update(self):
        self.timer += 1
        if self.timer >= self.duration:
            self.kill()
            return
            
        self.angle -= 5 # Pyöritys
        
        # Skaalaus (kasvaa alussa, kutistuu lopussa)
        scale = 1.0
        if self.timer < 30:
            scale = self.timer / 30.0
        elif self.timer > self.duration - 30:
            scale = (self.duration - self.timer) / 30.0
            
        if scale < 0.1: scale = 0.1
        
        # Pyöritetään ja skaalataan
        size = int(self.max_size * 2 * scale)
        scaled = pygame.transform.scale(self.base_image, (size, size))
        self.image = pygame.transform.rotate(scaled, self.angle)
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def kill(self):
        if hasattr(self, "loop_channel") and self.loop_channel:
            self.loop_channel.stop()
            sound_system.play_sound("vortex_end")
        super().kill()
