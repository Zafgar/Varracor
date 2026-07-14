import pygame
import random
import math
from settings import *
from sound_manager import sound_system

# Yritetään tuoda fontit UI Kitistä. Jos ui_kit puuttuu, käytetään oletusta.
try:
    from ui_kit import font_main, font_small
except ImportError:
    pygame.font.init()
    font_main = pygame.font.SysFont("Arial", 24)
    font_small = pygame.font.SysFont("Arial", 16)

# --- Apu-funktio Rectin hakuun (ChargAura tarvitsee) ---
def _as_rect(o):
    if o is None:
        return None
    if isinstance(o, pygame.Rect):
        return o
    return getattr(o, "rect", None)

# --- 1. BASE CLASSES ---

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_pos, speed, damage, owner, manager, image=None, duration=120, gravity=0):
        super().__init__()
        self.manager = manager
        self.owner = owner
        self.damage = damage
        self.speed = speed
        self.gravity = gravity
        self.timer = 0
        self.duration = duration
        
        # Calculate velocity
        dx = target_pos[0] - x
        dy = target_pos[1] - y
        dist = math.hypot(dx, dy) or 1
        
        self.vx = (dx / dist) * speed
        self.vy = (dy / dist) * speed
        self.angle = math.degrees(math.atan2(-dy, dx))
        
        self.pos_x = float(x)
        self.pos_y = float(y)
        
        if image:
            self.base_image = image
            self.image = pygame.transform.rotate(image, self.angle)
            self.rect = self.image.get_rect(center=(x, y))
        else:
            self.image = pygame.Surface((10, 10))
            self.image.fill((255, 255, 0))
            self.rect = self.image.get_rect(center=(x, y))

    def update(self, obstacles=None):
        self.timer += 1
        if self.timer >= self.duration:
            self.kill()
            return

        self.pos_x += self.vx
        self.pos_y += self.vy
        self.vy += self.gravity
        
        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)
        
        # Check obstacles (Walls)
        if obstacles:
            for obs in obstacles:
                r = getattr(obs, "rect", obs)
                if self.rect.colliderect(r):
                    blocks = getattr(obs, "blocks_projectiles", True)
                    t = getattr(obs, "type", None)
                    if t in ["water", "mud", "lava"]: blocks = False
                    
                    if blocks:
                        self.on_wall_hit()
                        return

        # Check unit collision
        # (Visuaalisilla ammuksilla ei ole manageria eika vahinkoa)
        if self.manager is None:
            return
        for unit in self.manager.all_units:
            if unit == self.owner or getattr(unit, "team_color", None) == getattr(self.owner, "team_color", None): continue
            if getattr(unit, "is_dead", False): continue
            
            # Osuu hurtboxiin
            if self.rect.colliderect(getattr(unit, "hurt_rect", unit.rect)):
                self.on_hit(unit)
                self.kill()
                return

    def on_hit(self, target):
        # Oletusvahinko
        if self.damage > 0 and hasattr(target, "take_damage"):
            target.take_damage(self.damage, "Physical", self.owner, self.manager)

    def on_wall_hit(self):
        # Oletus: Tuhoudu osuessa seinään
        self.kill()


class VFXSprite(pygame.sprite.Sprite):
    def __init__(self, x, y, duration):
        super().__init__()
        self.duration = duration
        self.timer = 0
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.image.set_alpha(0)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, obstacles=None):
        self.timer += 1
        if self.timer >= self.duration:
            self.kill()

class SpeechBubble(VFXSprite):
    """Staattinen puhekupla, joka seuraa hahmoa."""
    def __init__(self, unit, text, duration=120):
        # Alustetaan hahmon yläpuolelle
        super().__init__(unit.rect.centerx, unit.rect.top - 20, duration)
        self.unit = unit
        self.text = text
        
        # Renderöidään teksti
        # Tummanruskea teksti (ei täysin musta)
        text_surf = font_small.render(text, True, (30, 20, 10))
        padding = 8
        w = text_surf.get_width() + padding * 2
        h = text_surf.get_height() + padding * 2
        
        self.image = pygame.Surface((w, h + 6), pygame.SRCALPHA)
        
        # Kupla (Harmaanruskea tausta, tumma reuna)
        bubble_color = (230, 225, 215) # "Parchment" style
        border_color = (60, 50, 40)
        
        rect = pygame.Rect(0, 0, w, h)
        pygame.draw.rect(self.image, bubble_color, rect, border_radius=6)
        pygame.draw.rect(self.image, border_color, rect, 1, border_radius=6)
        
        # Pieni nuoli alaspäin
        pygame.draw.polygon(self.image, bubble_color, [(w//2 - 4, h-1), (w//2 + 4, h-1), (w//2, h + 5)])
        pygame.draw.line(self.image, border_color, (w//2 - 4, h), (w//2, h + 5))
        pygame.draw.line(self.image, border_color, (w//2, h + 5), (w//2 + 4, h))
        
        self.image.blit(text_surf, (padding, padding))
        self.rect = self.image.get_rect(midbottom=(unit.rect.centerx, unit.rect.top - 15))

    def update(self, obstacles=None):
        # Seuraa hahmoa
        if self.unit:
            # Bobbing effect (Elävä tunne: kupla kelluu hieman)
            bob = math.sin(pygame.time.get_ticks() * 0.005) * 2
            self.rect.midbottom = (self.unit.rect.centerx, self.unit.rect.top - 15 + bob)
        super().update(obstacles)

# --- ABYSSAL WEAVE VFX (Commander Magic) ---

class WarpSeam(VFXSprite):
    """
    Abyssal Weave: 'Seams'.
    Piirtää ohuen, hehkuvan viivan (ompelulanka) lähtöpisteen ja loppupisteen välille.
    Viiva värisee ja kiristyy ennen katoamista.
    """
    def __init__(self, start_pos, end_pos, color=(100, 255, 200), duration=25):
        super().__init__(start_pos[0], start_pos[1], duration)
        self.start = start_pos
        self.end = end_pos
        self.color = color
        
        # Luodaan pinta joka kattaa koko alueen
        min_x = min(start_pos[0], end_pos[0]) - 10
        min_y = min(start_pos[1], end_pos[1]) - 10
        w = abs(start_pos[0] - end_pos[0]) + 20
        h = abs(start_pos[1] - end_pos[1]) + 20
        
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(min_x, min_y))
        self.local_start = (start_pos[0] - min_x, start_pos[1] - min_y)
        self.local_end = (end_pos[0] - min_x, end_pos[1] - min_y)

    def update(self, obstacles=None):
        self.image.fill((0, 0, 0, 0))
        
        # Progress 0.0 -> 1.0
        t = self.timer / self.duration
        alpha = int(255 * (1.0 - t))
        
        # Piirrä useampi säie (Thread)
        for i in range(3):
            # Värinä (Abyssal instability) - kasvaa loppua kohden (kiristyy)
            jitter = (1.0 - t) * 4.0
            
            s_jit_x = random.uniform(-jitter, jitter)
            s_jit_y = random.uniform(-jitter, jitter)
            e_jit_x = random.uniform(-jitter, jitter)
            e_jit_y = random.uniform(-jitter, jitter)
            
            start = (self.local_start[0] + s_jit_x, self.local_start[1] + s_jit_y)
            end = (self.local_end[0] + e_jit_x, self.local_end[1] + e_jit_y)
            
            # Väri (pääväri + valkoinen ydin)
            col = (*self.color, alpha)
            if i == 1: col = (255, 255, 255, alpha) # Ydin
            
            width = 2 if i == 1 else 1
            pygame.draw.line(self.image, col, start, end, width)
            
            # "Solmut" matkan varrella
            if i == 0 and random.random() < 0.3:
                mid_x = (start[0] + end[0]) / 2
                mid_y = (start[1] + end[1]) / 2
                pygame.draw.circle(self.image, col, (int(mid_x), int(mid_y)), 2)
        
        super().update(obstacles)

class WarpRift(VFXSprite):
    """
    Abyssal Weave: 'Rift'.
    Musta/Vihreä repeämä, joka ilmestyy ja katoaa nopeasti.
    """
    def __init__(self, x, y, color=(50, 255, 200), duration=20):
        super().__init__(x, y, duration)
        self.color = color
        self.max_size = 20
        self.image = pygame.Surface((self.max_size*2, self.max_size*2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, obstacles=None):
        self.image.fill((0, 0, 0, 0))
        
        # Animaatio: Kasvaa nopeasti, sitten kutistuu
        t = self.timer / self.duration
        if t < 0.2: scale = t / 0.2
        else: scale = 1.0 - ((t - 0.2) / 0.8)
        
        size = int(self.max_size * scale)
        if size > 0:
            cx, cy = self.max_size, self.max_size
            # Musta ydin
            pygame.draw.circle(self.image, (0, 0, 0), (cx, cy), size)
            # Värillinen reuna (epätasainen)
            pygame.draw.circle(self.image, self.color, (cx, cy), size + 2, 2)
            
            # Säteet
            for _ in range(3):
                ang = random.uniform(0, 6.28)
                dist = size + random.randint(2, 8)
                ex = cx + math.cos(ang) * dist
                ey = cy + math.sin(ang) * dist
                pygame.draw.line(self.image, self.color, (cx, cy), (ex, ey), 1)

        super().update(obstacles)

class AfterImage(VFXSprite):
    """
    Abyssal Weave: 'Echo'.
    Jättää hahmon kuvan paikalleen, joka haalistuu nopeasti.
    """
    def __init__(self, unit, duration=30, color_tint=(100, 255, 200)):
        x, y = unit.rect.center
        super().__init__(x, y, duration)
        
        # Kopioi hahmon nykyinen kuva
        if unit.image:
            self.image = unit.image.copy()
            # Värjää haamumaiseksi
            self.image.fill((*color_tint, 100), special_flags=pygame.BLEND_RGBA_MULT)
        else:
            self.image = pygame.Surface((32, 48), pygame.SRCALPHA)
            self.image.fill((*color_tint, 100))
            
        self.rect = self.image.get_rect(center=(x, y))
        self.start_alpha = 180
        self.color_tint = color_tint

    def update(self, obstacles=None):
        t = self.timer / self.duration
        alpha = int(self.start_alpha * (1.0 - t))
        self.image.set_alpha(alpha)
        
        # Glitch effect (satunnainen siirtymä)
        if random.random() < 0.2:
            off_x = random.randint(-2, 2)
            self.rect.x += off_x
            
        super().update(obstacles)

    # --- SPAWN METHODS ---
    
    def create_warp_seam(self, start, end):
        self.particles.add(WarpSeam(start, end))
        # Lisää riftit päihin
        self.particles.add(WarpRift(start[0], start[1]))
        self.particles.add(WarpRift(end[0], end[1]))
        
    def create_after_image(self, unit):
        self.particles.add(AfterImage(unit))

class SeamCutEffect(VFXSprite):
    """
    Abyssal Weave: 'Seam Cut'.
    Pystysuora, terävä viilto, joka välähtää ja katoaa.
    """
    def __init__(self, x, y, color=(100, 255, 220), duration=20):
        super().__init__(x, y, duration)
        self.color = color
        self.length = 80
        self.width = 4
        
        # Luodaan pinta
        self.image = pygame.Surface((40, self.length + 20), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.angle = random.uniform(-15, 15) # Pieni kallistus

    def update(self, obstacles=None):
        self.image.fill((0, 0, 0, 0))
        
        # Animaatio: Laajenee nopeasti, sitten ohenee
        t = self.timer / self.duration
        if t < 0.2: 
            w = self.width * (t / 0.2)
            alpha = 255
        else:
            w = self.width * (1.0 - (t - 0.2) / 0.8)
            alpha = int(255 * (1.0 - t))
            
        if w < 1: w = 1
        
        # Piirrä viilto
        cx = self.image.get_width() // 2
        cy = self.image.get_height() // 2
        
        # Ydin (Valkoinen)
        pygame.draw.line(self.image, (255, 255, 255, alpha), (cx, 10), (cx, self.length), int(w))
        # Hehku (Väri)
        pygame.draw.line(self.image, (*self.color, int(alpha * 0.5)), (cx, 5), (cx, self.length + 5), int(w * 4))
        
        super().update(obstacles)

class VortexSlashProjectile(Projectile):
    """
    Vortex Blade: 'Vortex Slash'.
    Massiivinen, pyörivä energiakaari, joka lävistää kaiken.
    """
    def __init__(self, x, y, target_pos, speed, damage, owner, manager):
        # ARTIFACT LEVEL: Massiivinen koko (240x240)
        size = 240
        img = pygame.Surface((size, size), pygame.SRCALPHA)
        super().__init__(x, y, target_pos, speed, damage, owner, manager, image=img, duration=180)
        
        self.angle_rot = 0
        self.base_image = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Piirrä kaari (puolikuu)
        rect = pygame.Rect(0, 0, size, size)
        # 1. Void Aura (Musta/Violetti savu)
        pygame.draw.arc(self.base_image, (20, 0, 40), rect, -0.8, 3.9, 30)
        # 2. Energy Body (Kirkas Turkoosi)
        pygame.draw.arc(self.base_image, (40, 220, 180), rect.inflate(-40, -40), -0.7, 3.8, 18)
        # 3. Plasma Core (Valkoinen)
        pygame.draw.arc(self.base_image, (200, 255, 255), rect.inflate(-90, -90), -0.6, 3.7, 8)
        
        # Käännä oikeaan suuntaan
        self.base_image = pygame.transform.rotate(self.base_image, self.angle - 90)
        
        # Soita lentoääni
        self.fly_sound = sound_system.play_sound("vortex_wave_fly", loops=0)

    def update(self, obstacles=None):
        # Liiku
        self.pos_x += self.vx
        self.pos_y += self.vy
        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)
        
        self.timer += 1
        if self.timer >= self.duration:
            if self.fly_sound: self.fly_sound.stop()
            self.kill()
            return
            
        # Värinä ja skaalaus (sykkii)
        pulse = 1.0 + math.sin(self.timer * 0.2) * 0.1
        if pulse != 1.0:
            w = int(240 * pulse)
            h = int(240 * pulse)
            self.image = pygame.transform.scale(self.base_image, (w, h))
            self.rect = self.image.get_rect(center=(self.pos_x, self.pos_y))
        else:
            self.image = self.base_image
        
        # Trail (Vana) - Paljon partikkeleita
        for _ in range(5):
            col = random.choice([(50, 255, 200), (20, 0, 40), (255, 255, 255)])
            self.manager.vfx.create_void_particles(self.rect.centerx, self.rect.centery)

        # Osuma (Lävistää kaiken!)
        for unit in self.manager.all_units:
            if unit == self.owner or getattr(unit, "team_color", None) == getattr(self.owner, "team_color", None): continue
            if getattr(unit, "is_dead", False): continue
            
            if self.rect.colliderect(getattr(unit, "hurt_rect", unit.rect)):
                # Ei tuhoudu, vaan tekee vahinkoa ja jatkaa matkaa (tick damage cooldown?)
                # Yksinkertaistus: Osuu joka frame (erittäin tappava) tai käytetään listaa
                # Tässä: Osuu kerran per yksikkö per projectile instance? Ei, annetaan osua.
                # Mutta estetään "insta-kill" 60x sekunnissa.
                # Koska Projectile-luokka ei tue "pierce"-listaa oletuksena, tehdään se tässä.
                if not hasattr(self, "hit_list"): self.hit_list = []
                if unit not in self.hit_list:
                    unit.take_damage(self.damage, "Magic", self.owner, self.manager)
                    sound_system.play_sound("vortex_wave_impact")
                    self.manager.vfx.create_impact_sparks(unit.rect.centerx, unit.rect.centery, color=(100, 255, 255), count=10)
                    
                    # GAME FEEL: Hit Stop!
                    self.manager.trigger_hit_stop(5) 
                    
                    self.hit_list.append(unit)

    def on_wall_hit(self):
        # Lävistää myös seinät! (Artifact power)
        pass
        
    def kill(self):
        if hasattr(self, "fly_sound") and self.fly_sound:
            self.fly_sound.stop()
        super().kill()

# --- 2. EFFECT CLASSES ---

class DamageText(VFXSprite):
    def __init__(self, x, y, text, color, is_crit=False):
        super().__init__(x, y, duration=60)

        font = font_main if is_crit else font_small
        if is_crit:
            text = f"{text}!"

        self.image = font.render(str(text), True, color)
        self.bg_image = font.render(str(text), True, (0, 0, 0))

        self.rect = self.image.get_rect(center=(x, y))
        self.vy = -1.5

    def update(self, obstacles=None):
        self.rect.y += self.vy
        super().update(obstacles)

    def draw_custom(self, screen):
        screen.blit(self.bg_image, (self.rect.x + 1, self.rect.y + 1))
        screen.blit(self.image, self.rect)


class Particle(VFXSprite):
    def __init__(self, x, y, color, size, speed, duration):
        super().__init__(x, y, duration)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = random.uniform(-speed, speed)
        self.vy = random.uniform(-speed, speed)

    def update(self, obstacles=None):
        self.rect.x += self.vx
        self.rect.y += self.vy
        super().update(obstacles)


class ArrowProjectile(Projectile):
    def __init__(self, x, y, target_pos, speed, damage, owner, manager, is_bolt=False, max_range=1000):
        # Luo nuolen kuva
        img = pygame.Surface((30, 10), pygame.SRCALPHA)
        if is_bolt:
            # Lyhyempi ja paksumpi varsijousen nuoli
            pygame.draw.line(img, (100, 80, 50), (5, 5), (25, 5), 3)
            pygame.draw.polygon(img, (180, 180, 180), [(25, 2), (30, 5), (25, 8)])
            pygame.draw.line(img, (200, 200, 200), (5, 3), (0, 5), 2)
            pygame.draw.line(img, (200, 200, 200), (5, 7), (0, 5), 2)
        else:
            # Pitkä jousen nuoli
            pygame.draw.line(img, (139, 69, 19), (0, 5), (25, 5), 2)
            pygame.draw.polygon(img, (150, 150, 150), [(25, 2), (30, 5), (25, 8)])
            pygame.draw.line(img, (200, 200, 200), (0, 5), (5, 2), 1)
            pygame.draw.line(img, (200, 200, 200), (0, 5), (5, 8), 1)
            
        # Asetetaan pitkä kesto, jotta nuoli ehtii lentää max_rangeen asti
        super().__init__(x, y, target_pos, speed, damage, owner, manager, image=img, duration=600)
        self.is_bolt = is_bolt
        self.max_range = max_range
        self.start_pos = pygame.math.Vector2(x, y)
        self.stuck = False
        self.stuck_timer = 0
        self.stuck_duration = 300 # 5 sekuntia (60fps)

    def update(self, obstacles=None):
        # Jos nuoli on jumissa, se ei liiku, mutta vanhenee
        if self.stuck:
            self.stuck_timer += 1
            if self.stuck_timer >= self.stuck_duration:
                self.kill()
            # Häivytys lopussa
            elif self.stuck_timer > self.stuck_duration - 60:
                alpha = int(255 * (1.0 - (self.stuck_timer - (self.stuck_duration - 60)) / 60.0))
                self.image.set_alpha(alpha)
            return

        # Tarkista maksimikantama
        current_pos = pygame.math.Vector2(self.pos_x, self.pos_y)
        if self.start_pos.distance_to(current_pos) >= self.max_range:
            self.stuck = True
            # Varmistetaan että pysähtyy tasan max_rangeen (visuaalinen hienosäätö)
            # Mutta yksinkertaisuuden vuoksi pysähtyminen nykyiseen kohtaan on ok.
            return

        super().update(obstacles)
        # Huom: super().update() hoitaa osumisen yksiköihin (jolloin nuoli tuhoutuu/kill())

    def on_wall_hit(self):
        # Nuoli jää kiinni seinään eikä tuhoudu
        self.stuck = True

class MagicProjectile(Projectile):
    def __init__(self, x, y, target_pos, speed, damage, owner, manager, color=(100, 150, 255), size=10):
        img = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        pygame.draw.circle(img, color, (size, size), size)
        pygame.draw.circle(img, (255, 255, 255), (size, size), size//2)
        
        super().__init__(x, y, target_pos, speed, damage, owner, manager, image=img, duration=80)
        self.color = color

    def on_hit(self, target):
        target.take_damage(self.damage, "Magic", self.owner, self.manager)
        # Pöllähdys
        self.manager.vfx.create_impact_sparks(self.rect.centerx, self.rect.centery, color=self.color, count=5)

    def on_wall_hit(self):
        # Taika osuu seinään -> Pöllähdys ja tuho
        self.manager.vfx.create_impact_sparks(self.rect.centerx, self.rect.centery, color=self.color, count=3)
        self.kill()

class PowerArrowProjectile(VFXSprite):
    """
    Paksumpi, "power shot" -nuoli.
    """
    def __init__(self, start_pos, target_pos):
        super().__init__(start_pos[0], start_pos[1], duration=38)

        self.start_pos = pygame.math.Vector2(start_pos)
        self.target_pos = pygame.math.Vector2(target_pos)
        self.pos = pygame.math.Vector2(start_pos)

        direction = self.target_pos - self.start_pos
        distance = direction.length()

        if distance > 0:
            flight_frames = 18
            self.velocity = direction.normalize() * (distance / flight_frames)
            self.angle = math.degrees(math.atan2(-direction.y, direction.x))
        else:
            self.velocity = pygame.math.Vector2(0, 0)
            self.angle = 0

        # isompi sprite
        self.image = pygame.Surface((52, 18), pygame.SRCALPHA)

        # runko (kultainen)
        pygame.draw.line(self.image, (220, 180, 60), (0, 9), (40, 9), 4)
        pygame.draw.line(self.image, (255, 240, 170), (2, 8), (38, 8), 2)

        # kärki (valkoinen/kulta)
        pygame.draw.polygon(self.image, (255, 255, 255), [(40, 4), (52, 9), (40, 14)])
        pygame.draw.polygon(self.image, (255, 220, 120), [(40, 5), (50, 9), (40, 13)])

        # sulat
        pygame.draw.line(self.image, (255, 255, 255), (0, 9), (10, 4), 2)
        pygame.draw.line(self.image, (255, 255, 255), (0, 9), (10, 14), 2)

        self.image = pygame.transform.rotate(self.image, self.angle)
        self.rect = self.image.get_rect(center=self.pos)

        self.impact_frame = 18

    def update(self, obstacles=None):
        self.pos += self.velocity
        self.rect.center = self.pos
        
        if obstacles:
            for obs in obstacles:
                r = getattr(obs, "rect", obs)
                if self.rect.colliderect(getattr(obs, "hurt_rect", r)):
                    blocks = getattr(obs, "blocks_projectiles", True)
                    t = getattr(obs, "type", None)
                    if t in ["water", "mud", "lava"]: blocks = False
                    if blocks:
                        self.kill()
                        return
        super().update(obstacles)

        if self.timer >= self.impact_frame:
            self.kill()

class ShockwaveRing(VFXSprite):
    def __init__(self, x, y, color=(255, 140, 40), max_radius=45, duration=18, width=3):
        super().__init__(x, y, duration=duration)
        self.color = color
        self.max_radius = max_radius
        self.width = width

        size = max_radius * 2 + 12
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, obstacles=None):
        self.image.fill((0, 0, 0, 0))

        p = self.timer / max(1, self.duration - 1)  # 0..1
        radius = int(2 + p * self.max_radius)
        alpha = int(220 * (1.0 - p))
        col = (self.color[0], self.color[1], self.color[2], alpha)

        pygame.draw.circle(
            self.image,
            col,
            (self.image.get_width() // 2, self.image.get_height() // 2),
            radius,
            max(1, int(self.width * (1.0 - p) + 1))
        )

        super().update(obstacles)

class ReverseShockwaveRing(VFXSprite):
    """Shokkiaalto joka imeytyy sisäänpäin (Impulssi)."""
    def __init__(self, x, y, color=(255, 140, 40), max_radius=45, duration=18, width=3):
        super().__init__(x, y, duration=duration)
        self.color = color
        self.max_radius = max_radius
        self.width = width

        size = max_radius * 2 + 12
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, obstacles=None):
        self.image.fill((0, 0, 0, 0))

        p = self.timer / max(1, self.duration - 1)  # 0..1
        # Reverse: starts at max, goes to 0
        radius = int(self.max_radius * (1.0 - p))
        if radius < 1: radius = 1
        
        # Alpha kasvaa tiivistyessä
        alpha = int(100 + 155 * p)
        col = (self.color[0], self.color[1], self.color[2], alpha)

        pygame.draw.circle(
            self.image,
            col,
            (self.image.get_width() // 2, self.image.get_height() // 2),
            radius,
            self.width
        )

        super().update(obstacles)

class AcidGlob(VFXSprite):
    """Vihreä limapallo joka lentää parabolisessa kaaressa kohteeseen ja
    kutsuu osumassa on_impact-callbackin. Sovitettu käyttäjän
    bosses/rat_king/rat_vfx.py -paketin AcidProjectilesta (pelitesti 22)."""

    def __init__(self, start_pos, target_pos, on_impact=None):
        start = pygame.math.Vector2(start_pos)
        target = pygame.math.Vector2(target_pos)
        dist = (target - start).length()
        frames = max(30, int(dist / 8))
        super().__init__(start.x, start.y, duration=frames + 2)
        self.start = start
        self.target = target
        self.frames_total = frames
        self.on_impact = on_impact
        self.image = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (30, 120, 30), (11, 11), 10)
        pygame.draw.circle(self.image, (60, 230, 60), (11, 11), 8)
        pygame.draw.circle(self.image, (200, 255, 200), (8, 8), 3)
        self.rect = self.image.get_rect(center=start)

    def update(self, obstacles=None):
        super().update(obstacles)
        t = min(1.0, self.timer / max(1, self.frames_total))
        pos = self.start.lerp(self.target, t)
        # Parabolinen kaari: 4 * korkeus * t * (1 - t)
        height = 150 * 4 * t * (1 - t)
        self.rect.center = (int(pos.x), int(pos.y - height))
        if t >= 1.0:
            if self.on_impact:
                cb, self.on_impact = self.on_impact, None
                try:
                    cb()
                except Exception:
                    pass
            self.kill()


class FireballProjectile(VFXSprite):
    """
    Pieni mutta hieno fireball:
    - hehku + flicker
    - trail kipinät
    - osumassa kutsuu on_impact callbackin
    """
    def __init__(self, start_pos, target_pos, on_impact=None):
        super().__init__(start_pos[0], start_pos[1], duration=80)

        self.start_pos = pygame.math.Vector2(start_pos)
        self.target_pos = pygame.math.Vector2(target_pos)
        self.pos = pygame.math.Vector2(start_pos)

        direction = self.target_pos - self.start_pos
        distance = direction.length()

        flight_frames = max(14, min(26, int(distance / 12) if distance > 0 else 18))
        self.impact_frame = flight_frames

        if distance > 0:
            self.velocity = direction.normalize() * (distance / flight_frames)
        else:
            self.velocity = pygame.math.Vector2(0, 0)

        self.on_impact = on_impact
        self.trail = []

        self.canvas_size = 70
        self.image = pygame.Surface((self.canvas_size, self.canvas_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, obstacles=None):
        # liike
        self.pos += self.velocity
        self.rect.center = self.pos
        
        if obstacles:
            for obs in obstacles:
                r = getattr(obs, "rect", obs)
                if self.rect.colliderect(getattr(obs, "hurt_rect", r)):
                    blocks = getattr(obs, "blocks_projectiles", True)
                    t = getattr(obs, "type", None)
                    if t in ["water", "mud", "lava"]: blocks = False
                    if blocks:
                        self.kill()
                        return

        # trail spawn
        if random.random() < 0.95:
            jitter = pygame.math.Vector2(random.uniform(-2, 2), random.uniform(-2, 2))
            self.trail.append([self.pos + jitter, random.randint(10, 18)])

        # trail life
        for t in self.trail:
            t[1] -= 1
        self.trail = [t for t in self.trail if t[1] > 0]

        # piirrä oma surface uusiksi
        self.image.fill((0, 0, 0, 0))
        cx = self.canvas_size // 2
        cy = self.canvas_size // 2

        # trail draw
        for tp, life in self.trail:
            rel = tp - self.pos
            x = int(cx + rel.x)
            y = int(cy + rel.y)
            p = life / 18.0
            r = max(1, int(3 * p))

            pygame.draw.circle(self.image, (255, 110, 30, int(110 * p)), (x, y), r + 5)
            pygame.draw.circle(self.image, (255, 220, 140, int(160 * p)), (x, y), r + 1)

        # fireball core
        flick = random.randint(-1, 1)
        core_r = 5 + flick
        pygame.draw.circle(self.image, (255, 90, 20, 170), (cx, cy), core_r + 9)
        pygame.draw.circle(self.image, (255, 150, 40, 220), (cx, cy), core_r + 4)
        pygame.draw.circle(self.image, (255, 235, 160, 255), (cx, cy), core_r)

        super().update(obstacles)

        # osuma
        if self.timer >= self.impact_frame:
            if self.on_impact:
                self.on_impact()
            self.kill()


class LightningArc(VFXSprite):
    def __init__(self, start_pos, end_pos):
        super().__init__(start_pos[0], start_pos[1], duration=15)

        min_x = min(start_pos[0], end_pos[0]) - 50
        min_y = min(start_pos[1], end_pos[1]) - 50
        w = abs(start_pos[0] - end_pos[0]) + 100
        h = abs(start_pos[1] - end_pos[1]) + 100

        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(min_x, min_y))

        local_start = (start_pos[0] - min_x, start_pos[1] - min_y)
        local_end = (end_pos[0] - min_x, end_pos[1] - min_y)

        points = [local_start, local_end]
        for _ in range(4):
            new_points = []
            for i in range(len(points) - 1):
                p1 = points[i]
                p2 = points[i + 1]
                mid_x = (p1[0] + p2[0]) / 2
                mid_y = (p1[1] + p2[1]) / 2
                new_points.append(p1)
                new_points.append((mid_x + random.randint(-15, 15), mid_y + random.randint(-15, 15)))
            new_points.append(points[-1])
            points = new_points

        if len(points) > 1:
            # Sähkökaaren piirto
            pygame.draw.lines(self.image, (50, 100, 255), False, points, 5) # Varjo
            pygame.draw.lines(self.image, (200, 255, 255), False, points, 2) # Ydin

class FirebombProjectile(VFXSprite):
    def __init__(self, start, end, manager):
        super().__init__(start[0], start[1], duration=40)
        self.start = pygame.math.Vector2(start)
        self.end = pygame.math.Vector2(end)
        self.manager = manager
        self.t = 0
        
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (50, 20, 0), (6, 6), 6) # Bomb
        pygame.draw.circle(self.image, (255, 100, 0), (6, 6), 3) # Fuse
        self.rect = self.image.get_rect(center=start)

    def update(self, obstacles=None):
        self.t += 0.025
        if self.t >= 1.0:
            self.kill()
            # Explosion
            self.manager.vfx.create_fireburst(self.rect.centerx, self.rect.centery)
            # Fire Patch
            self.manager.vfx.floor_particles.add(FirePatch(self.rect.centerx, self.rect.centery))
            # AoE Damage
            for u in self.manager.all_units:
                d = math.hypot(u.rect.centerx - self.rect.centerx, u.rect.centery - self.rect.centery)
                if d < 60:
                    u.take_damage(10, "Fire", None, self.manager)
                    u.apply_status("Burn", 180, 2) # 3s burn
            return

        # Arc
        pos = self.start.lerp(self.end, self.t)
        h = 100 * 4 * self.t * (1 - self.t)
        self.rect.centerx = pos.x
        self.rect.centery = pos.y - h
        super().update(obstacles)

class FirePatch(VFXSprite):
    def __init__(self, x, y):
        super().__init__(x, y, duration=180) # 3s
        self.image = pygame.Surface((80, 80), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
    
    def update(self, obstacles=None):
        self.image.fill((0,0,0,0))
        # Draw fire
        for _ in range(5):
            ox = random.randint(0, 80)
            oy = random.randint(0, 80)
            dist = math.hypot(ox-40, oy-40)
            if dist < 35:
                r = random.randint(4, 10)
                col = random.choice([(255, 100, 0), (255, 200, 0), (200, 50, 0)])
                pygame.draw.circle(self.image, col, (ox, oy), r)
        super().update(obstacles)

class MudBubble(VFXSprite):
    """Ruskea mutakupla, joka kasvaa ja puhkeaa."""
    def __init__(self, x, y):
        super().__init__(x, y, duration=100)
        self.size = 0
        self.target_size = random.uniform(3, 8)
        self.pop_time = random.randint(30, 70)
        self.popped = False
        self.pop_timer = 0
        
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, obstacles=None):
        self.image.fill((0, 0, 0, 0))
        cx, cy = 12, 12
        
        if not self.popped:
            self.timer += 1
            if self.size < self.target_size: self.size += 0.1
            
            pygame.draw.circle(self.image, (60, 45, 30), (cx, cy), int(self.size))
            pygame.draw.circle(self.image, (90, 70, 50), (cx - 2, cy - 2), int(max(0, self.size - 2)))
            pygame.draw.circle(self.image, (30, 20, 10), (cx, cy), int(self.size), 1)
            
            if self.timer >= self.pop_time: self.popped = True
        else:
            self.pop_timer += 1
            r = self.size + (self.pop_timer * 0.5)
            if r < 12: pygame.draw.circle(self.image, (90, 70, 50), (cx, cy), int(r), 1)
            if self.pop_timer > 10: self.kill()

class FlyParticle(VFXSprite):
    """Pieni musta kärpänen joka pörrää."""
    def __init__(self, x, y):
        super().__init__(x, y, duration=60)
        self.center_x = x
        self.center_y = y
        self.image = pygame.Surface((2, 2))
        self.image.fill((20, 20, 20))
        self.rect = self.image.get_rect(center=(x, y))
        self.offset_x = random.uniform(-10, 10)
        self.offset_y = random.uniform(-10, 10)

    def update(self, obstacles=None):
        self.timer += 1
        # Pörrää satunnaisesti
        self.offset_x += random.uniform(-2, 2)
        self.offset_y += random.uniform(-2, 2)
        
        # Pysy lähellä keskustaa
        if self.offset_x > 15: self.offset_x -= 1
        if self.offset_x < -15: self.offset_x += 1
        if self.offset_y > 15: self.offset_y -= 1
        if self.offset_y < -15: self.offset_y += 1
        
        self.rect.centerx = self.center_x + self.offset_x
        self.rect.centery = self.center_y + self.offset_y
        
        if self.timer >= self.duration:
            self.kill()

class RatParticle(VFXSprite):
    """Pieni rotta joka juoksee lattialla."""
    def __init__(self, x, y):
        super().__init__(x, y, duration=120)
        self.image = pygame.Surface((12, 6), pygame.SRCALPHA)
        # Ruskea/harmaa rotta
        col = random.choice([(60, 50, 40), (80, 70, 60), (40, 40, 40)])
        pygame.draw.ellipse(self.image, col, (0, 0, 12, 6))
        # Häntä
        pygame.draw.line(self.image, (100, 80, 70), (0, 3), (-6, 3), 1)
        
        self.rect = self.image.get_rect(center=(x, y))
        angle = random.uniform(0, 6.28)
        speed = random.uniform(2, 4)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        
        # Käännä kuva menosuuntaan
        deg = -math.degrees(angle)
        self.image = pygame.transform.rotate(self.image, deg)

    def update(self, obstacles=None):
        self.rect.x += self.vx
        self.rect.y += self.vy
        super().update(obstacles)

class TavernDust(VFXSprite):
    """Hidas, leijuva pöly/savu tavernaan."""
    def __init__(self, x, y):
        super().__init__(x, y, duration=random.randint(300, 600))
        size = random.randint(2, 6)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        alpha = random.randint(20, 60) # Hyvin haalea
        color = (255, 240, 200, alpha) # Lämmin pöly
        pygame.draw.circle(self.image, color, (size//2, size//2), size//2)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = random.uniform(-0.2, 0.2)
        self.vy = random.uniform(-0.1, 0.1)

    def update(self, obstacles=None):
        self.rect.x += self.vx
        self.rect.y += self.vy
        super().update(obstacles)

class SteamParticle(VFXSprite):
    """Nouseva höyry."""
    def __init__(self, x, y):
        super().__init__(x, y, duration=120)
        self.image = pygame.Surface((6, 6), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.vy = -0.5

    def update(self, obstacles=None):
        self.timer += 1
        self.rect.y += self.vy
        alpha = max(0, 150 - int(self.timer * 1.5))
        pygame.draw.circle(self.image, (200, 200, 200, alpha), (3, 3), 3)
        if self.timer >= self.duration: self.kill()

class MilkIndicator(VFXSprite):
    """Valkoinen pisara lehmän pään päällä."""
    def __init__(self, unit):
        super().__init__(unit.rect.centerx, unit.rect.top - 10, duration=2) # Lyhyt kesto, luodaan jatkuvasti
        self.unit = unit
        self.image = pygame.Surface((10, 14), pygame.SRCALPHA)
        # Piirrä pisara
        pygame.draw.circle(self.image, (255, 255, 255), (5, 10), 4)
        pygame.draw.polygon(self.image, (255, 255, 255), [(1, 8), (9, 8), (5, 0)])
        # Reuna
        pygame.draw.circle(self.image, (200, 200, 255), (5, 10), 4, 1)
        
        self.rect = self.image.get_rect(midbottom=(unit.rect.centerx, unit.rect.top - 5))

    def update(self, obstacles=None):
        if self.unit:
            # Kelluva liike
            bob = math.sin(pygame.time.get_ticks() * 0.01) * 3
            self.rect.midbottom = (self.unit.rect.centerx, self.unit.rect.top - 10 + bob)
        super().update(obstacles)

# -------------------------
# Bard VFX
# -------------------------
class MusicalNote(VFXSprite):
    def __init__(self, x, y):
        super().__init__(x, y, duration=90)
        self.image = font_small.render("♪", True, (255, 215, 0)) # Kultainen nuotti
        if random.random() < 0.5:
            self.image = font_small.render("♫", True, (200, 200, 255)) # Tai tuplanuotti
            
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = -1.0 # Nousee ylös
        self.wobble = random.uniform(0, 6.28)

    def update(self, obstacles=None):
        self.wobble += 0.1
        self.rect.y += self.vy
        self.rect.x += math.sin(self.wobble) * 0.5 + self.vx
        
        # Fade out
        if self.timer > 60:
            self.image.set_alpha(int(255 * (1 - (self.timer - 60)/30)))
        super().update(obstacles)

class FireplaceEmber(VFXSprite):
    """Nouseva hehkuva hiukkanen tulisijaan."""
    def __init__(self, x, y):
        super().__init__(x, y, duration=random.randint(40, 80))
        self.image = pygame.Surface((4, 4), pygame.SRCALPHA)
        self.color = random.choice([(255, 100, 0), (255, 200, 50), (255, 50, 0)])
        pygame.draw.circle(self.image, self.color, (2, 2), 2)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-1.5, -0.5) # Nousee ylös

    def update(self, obstacles=None):
        self.rect.x += self.vx
        self.rect.y += self.vy
        self.image.set_alpha(int(255 * (self.timer / self.duration)))
        super().update(obstacles)

# -------------------------
# Power Shot - VFX (Siirretty tänne, koska olivat pyynnössä)
# -------------------------

class ChargeAura(VFXSprite):
    """
    Seuraa owneria ja piirtää pulssiringin + pientä kipinää latauksen ajan.
    """
    def __init__(self, owner, duration=90, color=(120, 180, 255)):
        r = _as_rect(owner)
        x, y = (0, 0)
        if r:
            x, y = r.centerx, r.centery
        super().__init__(x, y, duration=duration)

        self.owner = owner
        self.color = color
        self.max_radius = 28

        size = self.max_radius * 2 + 30
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.start_time = pygame.time.get_ticks()

    def update(self, obstacles=None):
        r = _as_rect(self.owner)
        if not r:
            self.kill()
            return

        # seuraa owneria
        self.rect.center = r.center

        # pulssi
        self.image.fill((0, 0, 0, 0))
        
        # Pysyvämmän näköinen ajastus
        time_elapsed = pygame.time.get_ticks() - self.start_time
        
        # Pulssi perustuu aikaan, jotta se on tasaista
        p_sin = (math.sin(time_elapsed * 0.005) * 0.5 + 0.5)  # 0..1 per 628ms
        
        # Häivytys (fade out)
        alpha_fade = 1.0 - (self.timer / max(1, self.duration)) 
        
        radius = int(10 + p_sin * self.max_radius)
        alpha = int(120 + 110 * alpha_fade)
        col = (self.color[0], self.color[1], self.color[2], alpha)

        cx = self.image.get_width() // 2
        cy = self.image.get_height() // 2

        # glow + ring
        pygame.draw.circle(self.image, (col[0], col[1], col[2], int(alpha * 0.35)), (cx, cy), radius + 10)
        pygame.draw.circle(self.image, col, (cx, cy), radius, 3)

        # kipinää
        if random.random() < 0.25:
            for _ in range(2):
                ang = random.random() * math.tau
                rr = radius + random.randint(0, 10)
                px = int(cx + math.cos(ang) * rr)
                py = int(cy + math.sin(ang) * rr)
                pygame.draw.circle(self.image, (255, 255, 255, 170), (px, py), 2)

        super().update(obstacles)

class AcidPuddle(VFXSprite):
    """
    Iso myrkkylammikko, joka on tarkoitettu piirrettäväksi hahmojen alle (floor layer).
    """
    def __init__(self, x, y, duration=240, team=None): # Kestää 4 sekuntia
        super().__init__(x, y, duration)
        self.team = team
        self.radius = 50 # Iso koko (halkaisija 100px)
        size = self.radius * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        
        cx, cy = self.radius, self.radius
        
        # Piirretään lammikko
        # 1. Pohja (tumma vihreä, läpinäkyvä)
        pygame.draw.circle(self.image, (40, 160, 40, 180), (cx, cy), self.radius)
        # 2. Reuna
        pygame.draw.circle(self.image, (30, 100, 30, 100), (cx, cy), self.radius, 4)
        # 3. Sisäosa (kirkkaampi)
        pygame.draw.circle(self.image, (80, 200, 80, 150), (cx, cy), int(self.radius * 0.7))
        
        # 4. Kuplia
        for _ in range(6):
            r = random.randint(4, 8)
            dist = random.randint(0, int(self.radius * 0.6))
            ang = random.uniform(0, 6.28)
            bx = int(cx + math.cos(ang) * dist)
            by = int(cy + math.sin(ang) * dist)
            pygame.draw.circle(self.image, (150, 255, 150, 200), (bx, by), r)

    def update(self, obstacles=None):
        super().update(obstacles)
        # Fade out lopussa
        if self.timer > self.duration - 60:
            alpha = int(255 * ((self.duration - self.timer) / 60.0))
            self.image.set_alpha(alpha)

# --- 3. MANAGER CLASS ---

class VFXManager:
    def __init__(self):
        self.particles = pygame.sprite.Group()
        self.floor_particles = pygame.sprite.Group() # UUSI: Lattia-tason efektit
        self.texts = pygame.sprite.Group()

    def add_effect(self, effect):
        """Ottaa vastaan ulkoisen Sprite-efektin ja lisää sen piirrettäviin"""
        if effect:
            self.particles.add(effect)

    def update(self, obstacles=None):
        self.particles.update(obstacles=obstacles)
        self.floor_particles.update()
        self.texts.update()
        
        # --- ESTÄ PUHEKUPLIEN PÄÄLLEKKÄISYYS ---
        bubbles = [t for t in self.texts if isinstance(t, SpeechBubble)]
        if len(bubbles) > 1:
            # Järjestä alhaalta ylös (Y-koordinaatin mukaan laskeva)
            bubbles.sort(key=lambda b: b.rect.bottom, reverse=True)
            
            for i in range(len(bubbles)):
                lower = bubbles[i]
                for j in range(i + 1, len(bubbles)):
                    upper = bubbles[j]
                    
                    if lower.rect.colliderect(upper.rect):
                        # Työnnä ylempää ylöspäin
                        target_bottom = lower.rect.top - 2
                        if upper.rect.bottom > target_bottom:
                            upper.rect.bottom = target_bottom

    def draw_floor(self, screen, offset=(0, 0)):
        """Piirretään ENNEN hahmoja"""
        sw, sh = screen.get_size()
        ox, oy = offset
        for p in self.floor_particles:
            # Piirrä vain jos ruudulla (pieni marginaali -100)
            if -100 < p.rect.x - ox < sw + 100 and -100 < p.rect.y - oy < sh + 100:
                screen.blit(p.image, (p.rect.x - ox, p.rect.y - oy))

    def draw_top(self, screen, offset=(0, 0)):
        """Piirretään hahmojen JÄLKEEN"""
        sw, sh = screen.get_size()
        ox, oy = offset
        for p in self.particles:
            if -100 < p.rect.x - ox < sw + 100 and -100 < p.rect.y - oy < sh + 100:
                screen.blit(p.image, (p.rect.x - ox, p.rect.y - oy))
            
        for text in self.texts:
            # Tekstitkin voi jättää piirtämättä jos kaukana
            if not (-100 < text.rect.x - ox < sw + 100 and -100 < text.rect.y - oy < sh + 100):
                continue

            if hasattr(text, "draw_custom"):
                # DamageText tarvitsee offsetin
                orig_rect = text.rect.copy()
                text.rect.x -= offset[0]
                text.rect.y -= offset[1]
                text.draw_custom(screen)
                text.rect = orig_rect # Palautetaan
            else:
                screen.blit(text.image, (text.rect.x - offset[0], text.rect.y - offset[1]))

    def draw(self, screen):
        # Fallback, jos kutsutaan vanhaa draw-metodia
        self.draw_floor(screen)
        self.draw_top(screen)

    # --- SPAWN METHODS ---

    def create_arrow(self, start, end):
        # Visuaalinen nuoli - vahinko hoidetaan perform_attackissa suoraan.
        # (BUGIKORJAUS: vanha kutsu ArrowProjectile(start, end) kaatui
        #  TypeErroriin, jolloin legacy-jouset eivat tehneet mitaan.)
        self.particles.add(ArrowProjectile(start[0], start[1], end, 22, 0, None, None))

    def create_warp_seam(self, start, end):
        self.particles.add(WarpSeam(start, end))
        # Lisää riftit päihin (mustat aukot)
        self.particles.add(WarpRift(start[0], start[1]))
        self.particles.add(WarpRift(end[0], end[1]))
        
    def create_after_image(self, unit):
        self.particles.add(AfterImage(unit))

    def create_seam_cut(self, x, y):
        self.particles.add(SeamCutEffect(x, y))

    def create_vortex_slash(self, x, y, target_pos, damage, owner, game_manager):
        proj = VortexSlashProjectile(x, y, target_pos, 25, damage, owner, game_manager)
        self.particles.add(proj)
        
    def create_void_particles(self, x, y):
        # Mustia/Violetteja hiukkasia (Void Iron)
        for _ in range(2):
            col = random.choice([(20, 0, 40), (100, 0, 200), (50, 255, 200)])
            p = Particle(x, y, col, size=random.randint(2, 5), speed=0.5, duration=45)
            p.vy = random.uniform(-1.0, 1.0)
            self.particles.add(p)

    def add_projectile(self, proj):
        """Lisää pelilogiikkaa sisältävän ammuksen (Projectile)."""
        # Huom: Projectile tarvitsee managerin toimiakseen, joten se lisätään 
        # yleensä suoraan manager.vfx.particles ryhmään kutsujan toimesta.
        self.particles.add(proj)

    def create_power_arrow(self, start, end):
        self.particles.add(PowerArrowProjectile(start, end))

    def create_lightning(self, start, end):
        self.particles.add(LightningArc(start, end))

    def create_explosion(self, x, y, color=(255, 100, 50)):
        for _ in range(20):
            p = Particle(x, y, color, size=random.randint(4, 8), speed=5, duration=30)
            self.particles.add(p)
            
    def create_impact_sparks(self, x, y, color=(255, 200, 50), count=6):
        # Yleinen kipinäefekti
        for _ in range(count):
            p = Particle(x, y, color, size=random.randint(3, 5), speed=random.uniform(2, 5), duration=15)
            self.particles.add(p)

    def create_blood(self, x, y):
        # Käytetään ImpactSparksia, mutta punaisena
        self.create_impact_sparks(x, y, color=(180, 0, 0), count=8)


    def create_heal_effect(self, x, y):
        for _ in range(12):
            p = Particle(x, y, (50, 255, 100), size=5, speed=2, duration=45)
            p.vy = random.uniform(-3, -0.5)
            self.particles.add(p)

    def create_fireball(self, start, end, on_impact=None):
        self.particles.add(FireballProjectile(start, end, on_impact=on_impact))

    def create_firebomb(self, start, end, owner, game_manager):
        self.particles.add(FirebombProjectile(start, end, game_manager))

    def create_fireburst(self, x, y):
        # shockwave rengas
        self.particles.add(ShockwaveRing(x, y, color=(255, 140, 40), max_radius=45, duration=18, width=3))

        # kuumat kipinät ja savu
        for _ in range(26):
            col = random.choice([(255, 120, 30), (255, 170, 60), (255, 220, 140)])
            p = Particle(x, y, col, size=random.randint(3, 7), speed=6, duration=28)
            self.particles.add(p)
        for _ in range(10):
            p = Particle(x, y, (60, 40, 30), size=random.randint(4, 9), speed=3, duration=34)
            self.particles.add(p)

    def create_shockwave(self, x, y, color=(255, 140, 40), max_radius=46, width=3):
        self.particles.add(ShockwaveRing(x, y, color=color, max_radius=max_radius, width=width))

    def create_charge_aura(self, owner, duration=90, color=(120, 180, 255)):
        self.particles.add(ChargeAura(owner, duration=duration, color=color))

    def create_power_shot_impact(self, x, y):
        # isompi shockwave + kipinää
        self.particles.add(ShockwaveRing(x, y, color=(255, 220, 120), max_radius=60, duration=20, width=4))
        self.create_impact_sparks(x, y, color=(255, 230, 160), count=18)
        
    def show_damage(self, x, y, amount, is_crit=False, type="damage", color=None):
        if color is None:
            color = (255, 255, 255)
            if type == "heal":
                color = (50, 255, 50)
                amount = f"+{amount}"
            elif is_crit:
                color = (255, 255, 0)
            elif type == "magic":
                color = (100, 150, 255)

        self.texts.add(DamageText(x, y, amount, color, is_crit))

    def create_acid_puddle(self, x, y, team=None):
        self.floor_particles.add(AcidPuddle(x, y, team=team))

    def create_acid_glob(self, start, end, on_impact=None):
        """Rat Kingin sylky: vihreä limapallo joka lentää kaaressa
        (pelitesti 22 - käyttäjän bosses/-paketin AcidProjectile-idea)."""
        self.particles.add(AcidGlob(start, end, on_impact=on_impact))
        
    def create_speech_bubble(self, unit, text, duration=120):
        self.texts.add(SpeechBubble(unit, text, duration))

    def create_mud_bubble(self, x, y):
        self.floor_particles.add(MudBubble(x, y))

    def create_flies(self, x, y):
        self.particles.add(FlyParticle(x, y))

    def create_rat(self, x, y):
        self.floor_particles.add(RatParticle(x, y))

    def create_tavern_dust(self, x, y):
        self.particles.add(TavernDust(x, y))

    def create_steam(self, x, y):
        self.particles.add(SteamParticle(x, y))

    def create_smoke(self, x, y):
        self.particles.add(SteamParticle(x, y)) # Käytetään samaa höyryä savuna toistaiseksi

    def create_milk_indicator(self, unit):
        self.particles.add(MilkIndicator(unit))

    def create_musical_note(self, x, y):
        self.particles.add(MusicalNote(x, y))
        
    def create_fireplace_ember(self, x, y):
        self.particles.add(FireplaceEmber(x, y))

    def create_spawn_fog(self, x, y):
        # Luo pöllähdyksen viemärikaasua
        for _ in range(15):
            # Tummanvihreitä/harmaita hiukkasia
            color = random.choice([(40, 60, 40, 150), (50, 70, 50, 150), (30, 50, 30, 150)])
            p = Particle(x, y, color, size=random.randint(10, 20), speed=1.5, duration=90)
            p.vy = random.uniform(-1, -0.2) # Nousee hitaasti ylös
            self.particles.add(p)

    def create_spores(self, x, y):
        # Vihreitä leijuvia hiukkasia (Nightcap Fungus)
        for _ in range(2):
            p = Particle(x, y, (100, 255, 150, 150), size=random.randint(2, 4), speed=0.5, duration=60)
            p.vy = random.uniform(-0.5, -1.5) # Nousee
            self.particles.add(p)


    def create_dust_cloud(self, x, y):
        # Ruskeaa pölyä (Scrap Pile)
        for _ in range(8):
            p = Particle(x, y, (120, 100, 80), size=random.randint(4, 8), speed=1.0, duration=40)
            self.particles.add(p)

    def create_spores(self, x, y):
        # Vihreitä leijuvia hiukkasia (Nightcap Fungus)
        for _ in range(2):
            p = Particle(x, y, (100, 255, 150, 150), size=random.randint(2, 4), speed=0.5, duration=60)
            p.vy = random.uniform(-0.5, -1.5) # Nousee
            self.particles.add(p)

    def create_void_particles(self, x, y):
        # Mustia/Violetteja hiukkasia (Void Iron)
        for _ in range(2):
            col = random.choice([(20, 0, 40), (100, 0, 200)])
            p = Particle(x, y, col, size=random.randint(2, 5), speed=0.3, duration=45)
            p.vy = random.uniform(-0.5, 0.5)
            self.particles.add(p)

    def create_dust_cloud(self, x, y):
        # Ruskeaa pölyä (Scrap Pile)
        for _ in range(8):
            p = Particle(x, y, (120, 100, 80), size=random.randint(4, 8), speed=1.0, duration=40)
            self.particles.add(p)

    def create_falling_leaves(self, x, y):
        # Putoavia lehtiä (Swamp Tree)
        for _ in range(5):
            color = random.choice([(40, 60, 30), (60, 80, 40), (80, 100, 50)])
            p = Particle(x + random.randint(-20, 20), y - random.randint(30, 80), color, size=random.randint(3, 5), speed=1.0, duration=80)
            p.vx = random.uniform(-1.5, 1.5)
            p.vy = random.uniform(1.0, 2.5) # Putoaa alas
            self.particles.add(p)

    def create_spore_burst(self, x, y):
        # Iso pöllähdys itiöitä (Nightcap Fungus harvest)
        for _ in range(10):
            self.create_spores(x, y)

    def create_ore_glimmer(self, x, y):
        # Pieni välke malmin päällä (huomioarvo)
        for _ in range(2):
            p = Particle(x + random.randint(-10, 10), y + random.randint(-10, 10), (255, 255, 200), size=2, speed=0.2, duration=40)
            p.vy = -0.5
            self.particles.add(p)

    def create_suction_particles(self, x, y):
        # Luo hiukkasia jotka lentävät kohti keskustaa (x, y)
        for _ in range(12): # Enemmän partikkeleita
            angle = random.uniform(0, 6.28)
            dist = random.randint(100, 600) # Laajempi alue
            px = x + math.cos(angle) * dist
            py = y + math.sin(angle) * dist
            
            speed = random.uniform(10, 18) # Nopeampia
            vx = -math.cos(angle) * speed
            vy = -math.sin(angle) * speed
            
            col = random.choice([(180, 50, 255), (100, 0, 200), (255, 255, 255)])
            p = Particle(px, py, col, size=random.randint(2, 6), speed=0, duration=int(dist/speed))
            p.vx = vx
            p.vy = vy
            self.particles.add(p)

    def create_reverse_shockwave(self, x, y, color=(255, 140, 40), max_radius=46, duration=20, width=3):
        self.particles.add(ReverseShockwaveRing(x, y, color=color, max_radius=max_radius, duration=duration, width=width))

class VortexPortal(VFXSprite):
    """
    Pyörivä portaali/repeämä, joka toimii triggerinä.
    Visuaalisesti näyttävä "reality break" -efekti.
    """
    def __init__(self, x, y, duration=1200):
        super().__init__(x, y, duration)
        self.base_size = 400 # Vielä isompi koko (oli 360)
        self.image = pygame.Surface((self.base_size, self.base_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.angle = 0
        self.particles = [] # (angle, dist, speed, color)

    def update(self, obstacles=None):
        self.angle = (self.angle + 2.0) % 360
        self.image.fill((0, 0, 0, 0))
        
        cx, cy = self.base_size // 2, self.base_size // 2
        time = pygame.time.get_ticks()
        
        # --- 1. NEBULA GLOW (Tausta) ---
        # Piirretään isoja, pehmeitä kehiä
        for i in range(3):
            pulse = math.sin(time * 0.001 + i) * 20
            radius = 120 + i * 30 + pulse
            alpha = 30 + int(math.sin(time * 0.002 + i) * 10)
            
            # Käytetään surfacea alpha-blendaukseen
            s = pygame.Surface((self.base_size, self.base_size), pygame.SRCALPHA)
            color = (50, 0, 100, alpha) if i % 2 == 0 else (0, 50, 100, alpha)
            pygame.draw.circle(s, color, (cx, cy), int(radius))
            self.image.blit(s, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # --- 2. ACCRETION DISK (Spiraalit) ---
        # Piirretään spiraalimuodossa
        num_arms = 5
        points_per_arm = 30
        
        for i in range(num_arms):
            arm_offset = (i / num_arms) * 6.28
            current_rot = math.radians(self.angle)
            
            prev_pos = None
            for j in range(points_per_arm):
                # Logaritminen spiraali
                t = j / points_per_arm
                angle = arm_offset + current_rot + (t * 4.0) # Kiertyy 4 radiaania
                dist = 40 + (t * 140) # 40px ytimestä ulos
                
                px = cx + math.cos(angle) * dist
                py = cy + math.sin(angle) * dist
                
                # Väri muuttuu etäisyyden mukaan (Valkoinen ydin -> Syaani -> Violetti)
                if t < 0.2: col = (255, 255, 255)
                elif t < 0.6: col = (100, 255, 255)
                else: col = (150, 50, 255)
                
                # Piirrä hehkuva viiva
                if prev_pos:
                    pygame.draw.line(self.image, col, prev_pos, (px, py), max(1, int(4 * (1-t))))
                
                prev_pos = (px, py)

        # --- 3. EVENT HORIZON (Musta aukko) ---
        core_pulse = math.sin(time * 0.005) * 5
        core_r = int(40 + core_pulse)
        
        # Kirkas reuna (Photon ring)
        pygame.draw.circle(self.image, (200, 255, 255), (cx, cy), core_r + 4, 2)
        pygame.draw.circle(self.image, (100, 200, 255), (cx, cy), core_r + 8, 1)
        
        # Musta ydin
        pygame.draw.circle(self.image, (0, 0, 0), (cx, cy), core_r)

        # --- 4. PARTICLE SYSTEM (Imu) ---
        # Lisää uusia
        if len(self.particles) < 60:
            angle = random.uniform(0, 6.28)
            dist = random.randint(100, 180)
            self.particles.append({
                'angle': angle,
                'dist': dist,
                'speed': random.uniform(1.0, 3.0),
                'color': random.choice([(100, 255, 255), (255, 100, 255), (255, 255, 255)])
            })
            
        # Päivitä ja piirrä
        for p in self.particles[:]:
            p['dist'] -= p['speed']
            p['angle'] += 0.05 # Kiertää lähestyessään
            p['speed'] *= 1.05 # Kiihtyy
            
            if p['dist'] < core_r:
                self.particles.remove(p)
                continue
                
            px = cx + math.cos(p['angle']) * p['dist']
            py = cy + math.sin(p['angle']) * p['dist']
            
            # Venytä vauhdin suuntaan (Motion blur)
            tail_x = cx + math.cos(p['angle'] - 0.1) * (p['dist'] + p['speed']*2)
            tail_y = cy + math.sin(p['angle'] - 0.1) * (p['dist'] + p['speed']*2)
            
            pygame.draw.line(self.image, p['color'], (px, py), (tail_x, tail_y), 2)

        # --- 5. REALITY GLITCH (Satunnaiset viivat) ---
        if random.random() < 0.3:
            y_off = random.randint(-100, 100)
            w = random.randint(80, 200)
            h = random.randint(1, 3)
            lx = cx - w // 2 + random.randint(-30, 30)
            ly = cy + y_off
            col = (100, 255, 255, 150) if random.random() < 0.5 else (255, 50, 200, 150)
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            s.fill(col)
            self.image.blit(s, (lx, ly), special_flags=pygame.BLEND_RGBA_ADD)
            
        super().update(obstacles)

class VortexMissile(Projectile):
    """
    Hakeutuva ohjus, joka lentää ensin ylös ja sitten syöksyy kohteeseen.
    """
    def __init__(self, x, y, target_unit, damage, owner, manager):
        # Alustetaan satunnaisella nopeudella ylöspäin/sivuille
        target_pos = (x + random.randint(-100, 100), y - random.randint(100, 200))
        
        # Luodaan visuaalinen pallo
        img = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(img, (100, 0, 200), (10, 10), 8)
        pygame.draw.circle(img, (200, 100, 255), (10, 10), 4)
        
        # Aloitetaan hitaasti (speed=1.5)
        super().__init__(x, y, target_pos, speed=1.5, damage=damage, owner=owner, manager=manager, image=img, duration=900)
        
        self.target = target_unit
        self.current_speed = 1.5
        self.sound_channel = sound_system.play_sound('vortex_missile_loop', loops=-1)

    def update(self, obstacles=None):
        self.timer += 1
        
        # 1. Hakeutuminen (Homing)
        if self.target and not self.target.is_dead:
            # Vektori kohteeseen
            dx = self.target.rect.centerx - self.pos_x
            dy = self.target.rect.centery - self.pos_y
            dist = math.hypot(dx, dy) or 1
            
            # Haluttu suunta
            desired_vx = (dx / dist) * self.current_speed
            desired_vy = (dy / dist) * self.current_speed
            
            # Käännä nykyistä nopeutta kohti haluttua (Steering)
            # Alussa (timer < 30) kääntyy hitaammin, jotta lentää kaaressa
            # Mitä kovempi vauhti, sitä vaikeampi kääntää (turn_speed pienenee)
            base_turn = 0.08 if self.timer > 40 else 0.02 # Paljon pienempi kääntyminen
            turn_speed = base_turn / (self.current_speed * 0.2) 
            turn_speed = max(0.01, min(0.1, turn_speed)) # Katto 0.1 (oli 0.3)
            
            self.vx += (desired_vx - self.vx) * turn_speed
            self.vy += (desired_vy - self.vy) * turn_speed
            
            # Kiihdytys (pikkuhiljaa)
            self.current_speed = min(7.0, self.current_speed + 0.04)

        # Päivitä sijainti (Projectile-luokka hoitaa tämän vx/vy perusteella)
        super().update(obstacles)
        
        # Trail effect
        if self.timer % 3 == 0:
            self.manager.vfx.create_impact_sparks(self.rect.centerx, self.rect.centery, color=(150, 50, 255), count=1)

    def kill(self):
        if self.sound_channel:
            self.sound_channel.stop()
        
        # Räjähdys
        sound_system.play_sound('vortex_explosion')
        self.manager.vfx.create_shockwave(self.rect.centerx, self.rect.centery, color=(100, 0, 200), max_radius=80)
        self.manager.vfx.create_impact_sparks(self.rect.centerx, self.rect.centery, color=(200, 100, 255), count=10)
        
        super().kill()