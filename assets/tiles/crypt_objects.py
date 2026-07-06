import pygame
import math
from assets.tiles.prop import Prop

class CryptGrass(Prop):
    """
    Ruohomätäs (Skaalattu: 140x80).
    Estää liikkumisen, mutta sallii ampumisen yli.
    """
    def __init__(self, x, y):
        w, h = 140, 80
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/crypt_objects/grass_patch.png",
            color=(60, 100, 60)
        )
        self.blocks_projectiles = False # Ammukset menevät läpi
        self.has_shadow = False

class CryptBigPillar(Prop):
    """
    Iso pylväs (Skaalattu: 120x260).
    Vain alin 1/4 estää liikkumisen.
    """
    def __init__(self, x, y):
        w, h = 120, 260
        # Törmäyslaatikko vain alhaalla
        coll_h = 60
        coll_y = y + (h - coll_h)
        coll_rect = pygame.Rect(x, coll_y, w, coll_h)
        
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/crypt_objects/big_pillar.png",
            collision_rect=coll_rect,
            color=(100, 100, 120)
        )

class CryptRock(Prop):
    """
    Iso kivi (Skaalattu: 200x140).
    Alin 4/5 estää liikkumisen.
    """
    def __init__(self, x, y):
        w, h = 200, 140
        # 4/5 korkeudesta on törmäystä
        coll_h = int(h * 0.8) 
        coll_y = y + (h - coll_h)
        coll_rect = pygame.Rect(x, coll_y, w, coll_h)
        
        super().__init__(x, y, w, h, img_path="assets/tiles/crypt_objects/big_rock.png", collision_rect=coll_rect, color=(80, 80, 80))

class BrokenPillar(Prop):
    """
    Rikkoutunut pylväs.
    """
    def __init__(self, x, y):
        w, h = 80, 150
        coll_h = 50
        coll_y = y + (h - coll_h)
        coll_rect = pygame.Rect(x, coll_y, w, coll_h)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/crypt_objects/broken_pillar.png",
            collision_rect=coll_rect,
            color=(90, 90, 100)
        )

class CryptCoffin(Prop):
    """
    Haudan arkku.
    """
    def __init__(self, x, y):
        w, h = 60, 100
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/crypt_objects/crypt_coffin.png",
            color=(80, 60, 40)
        )
        self.blocks_projectiles = True

class CryptTree(Prop):
    """
    Kuollut puu kryptassa.
    """
    def __init__(self, x, y):
        w, h = 100, 180
        coll_w = 30
        coll_h = 40
        coll_x = x + (w - coll_w) // 2
        coll_y = y + (h - coll_h)
        coll_rect = pygame.Rect(coll_x, coll_y, coll_w, coll_h)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/crypt_objects/crypt_tree.png",
            collision_rect=coll_rect,
            color=(70, 60, 50)
        )

class SpiritEssence(pygame.sprite.Sprite):
    """
    Kerättävä sielunpalanen. Käytetään valuuttana Ashen Ossuaryn kanssa.
    """
    def __init__(self, x, y):
        super().__init__()
        self.rect = pygame.Rect(x, y, 24, 24)
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        self.timer = 0
        self.duration = 1800 # 30 sekuntia aikaa kerätä
        self.type = "pickup"
        self.is_structure = True
        self.team_color = "Neutral"
        self.is_dead = False # GameManager yhteensopivuus

    def update(self, obstacles=None, manager=None):
        self.timer += 1
        if self.timer > self.duration:
            self.kill()
            return

        # Visuaalinen syke
        self.image.fill((0, 0, 0, 0))
        pulse = (math.sin(self.timer * 0.1) + 1) * 0.5 # 0..1
        
        # Necrotic Green Glow
        radius = 6 + pulse * 3
        # Outer aura (Dark/Blackish Green)
        pygame.draw.circle(self.image, (20, 40, 20, 100), (12, 12), radius + 2)
        # Inner glow (Bright Necro Green)
        alpha = 150 + int(pulse * 100)
        pygame.draw.circle(self.image, (50, 255, 50, alpha), (12, 12), radius)
        # Core (White/Green)
        pygame.draw.circle(self.image, (200, 255, 200), (12, 12), 3)

    def run_combat_ai(self, *args, **kwargs): pass
    def draw_health_bar(self, *args, **kwargs): pass
    def draw_on_screen(self, screen, offset):
        screen.blit(self.image, (self.rect.x - offset[0], self.rect.y - offset[1]))