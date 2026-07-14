import pygame
import random
import math
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

# TUODAAN NYT OIKEA TILEMAP
from systems.map_system import TileMap

class RatKingLair:
    def __init__(self):
        self.name = "Rat Sewer"
        
        # 1. ALUSTA TILEMAP
        self.tilemap = TileMap()
        
        # Lasketaan ruudukon koko (64px tileillä)
        # +2 varmistaa että menee vähän yli reunojen ettei jää mustaa
        cols = (SCREEN_WIDTH // 64) + 2
        rows = (SCREEN_HEIGHT // 64) + 2
        
        # 2. GENERDOI HUONE (Lataa PNG-kuvat)
        self.tilemap.generate_room(cols, rows, type="dungeon")
        
        # 3. HAE SEINÄT TÖRMÄYSTÄ VARTEN
        # Nyt Gladiator ei voi kävellä kuvien läpi
        self.obstacles = self.tilemap.get_obstacles()
        
        # --- SPAWN LOCATIONS ---
        self.spawn_points = [
            (150, 280),               # Vasen putki
            (SCREEN_WIDTH // 2, 220), # Keskiylä
            (SCREEN_WIDTH - 150, 280) # Oikea putki
        ]
        
        # --- VFX (Kuplat jne.) ---
        self.bubbles = []
        for _ in range(15):
            self.bubbles.append([
                random.randint(0, SCREEN_WIDTH), 
                random.randint(SCREEN_HEIGHT - 100, SCREEN_HEIGHT),
                random.randint(2, 5), 
                random.uniform(0.5, 1.5)
            ])
            
        self.debris = [] 
        for _ in range(6):
            self.debris.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'w': random.randint(20, 60),
                'offset': random.uniform(0, 6.28) 
            })

        self.drips = [] 

        self.darkness_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.darkness_overlay.fill((0,0,0,0)) 
        pygame.draw.rect(self.darkness_overlay, (0,0,0, 150), (0,0, SCREEN_WIDTH, 120)) 
        pygame.draw.rect(self.darkness_overlay, (0,0,0, 120), (0, SCREEN_HEIGHT-80, SCREEN_WIDTH, 80)) 

    def get_random_spawn_point(self):
        """Palauttaa satunnaisen spawn-pisteen (x, y)"""
        return random.choice(self.spawn_points)

    def update(self, all_units):
        # Päivitä map
        self.tilemap.update()
        
        # Kuplat
        for b in self.bubbles:
            b[1] -= b[3] 
            if b[1] < SCREEN_HEIGHT - 110: 
                b[1] = SCREEN_HEIGHT
                b[0] = random.randint(0, SCREEN_WIDTH)
        
        # Lima
        if random.random() < 0.08: 
            px, py = random.choice([self.spawn_points[0], self.spawn_points[2]])
            self.drips.append([px, py + 40, random.uniform(4, 7)]) 

        # Pisarat
        for d in self.drips:
            d[1] += d[2] 
        self.drips = [d for d in self.drips if d[1] < SCREEN_HEIGHT - 100]

    def draw_background(self, screen):
        # --- TÄMÄ PIIRTÄÄ NYT NE PNG-KUVAT ---
        self.tilemap.draw(screen)

        # Piirrä Rat Kingin omat koristeet (Putket yms) kartan päälle
        for i, (sx, sy) in enumerate(self.spawn_points):
            if i == 1: 
                mx, my = sx, sy
                pygame.draw.rect(screen, (5, 5, 5), (mx - 60, my - 40, 120, 80))
                for k in range(0, 120, 20): 
                    pygame.draw.line(screen, (50, 40, 40), (mx - 60 + k, my - 40), (mx - 60 + k, my + 40), 4)
                pygame.draw.rect(screen, (60, 50, 50), (mx - 60, my - 40, 120, 80), 4)
            else: 
                pygame.draw.circle(screen, (50, 50, 55), (sx, sy), 54)
                pygame.draw.circle(screen, (0, 0, 0), (sx, sy), 44) 
                pygame.draw.arc(screen, (20, 20, 20), (sx-44, sy-44, 88, 88), 0, 3.14, 4)

        for dx, dy, _ in self.drips:
            pygame.draw.circle(screen, (100, 255, 100), (int(dx), int(dy)), 5)
            pygame.draw.line(screen, (50, 200, 50), (dx, dy), (dx, dy-10), 3)

        water_level = SCREEN_HEIGHT - 100
        time = pygame.time.get_ticks() * 0.002
        points = [(0, SCREEN_HEIGHT), (0, water_level)]
        for x in range(0, SCREEN_WIDTH + 20, 20):
            y_offset = math.sin(time + x * 0.015) * 6 + math.sin(time * 2 + x * 0.03) * 3
            points.append((x, water_level + y_offset))
        points.append((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.draw.polygon(screen, (20, 60, 20), points) 
        pygame.draw.lines(screen, (80, 160, 80), False, points[1:-1], 3) 

        for deb in self.debris:
            debris_y = water_level + math.sin(time + deb['offset']) * 8
            pygame.draw.rect(screen, (50, 30, 10), (deb['x'], debris_y + 10, deb['w'], 6))

        for bx, by, size, _ in self.bubbles:
            if by > water_level + 10:
                pygame.draw.circle(screen, (100, 220, 100), (int(bx), int(by)), size)

    def draw_foreground(self, screen):
        screen.blit(self.darkness_overlay, (0,0))
        pulse = 40 + math.sin(pygame.time.get_ticks() * 0.0008) * 30
        fog_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        fog_surf.fill((60, 100, 20, int(30 + pulse)))
        screen.blit(fog_surf, (0, 0))