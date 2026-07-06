import pygame
import random
import math
from settings import SCREEN_HEIGHT

class SunRayBeam(pygame.sprite.Sprite):
    def __init__(self, manager, caster, target_unit, duration=300):
        super().__init__()
        self.manager = manager
        self.caster = caster
        self.target_unit = target_unit
        self.duration = duration
        self.timer = 0
        
        # Alkusijainti
        start_x = target_unit.rect.centerx if target_unit else caster.rect.centerx
        start_y = target_unit.rect.centery if target_unit else caster.rect.centery
        
        self.current_x = float(start_x)
        self.current_y = float(start_y)
        
        # Säteen ominaisuudet
        self.beam_width = 100
        self.damage_per_tick = 12  # Hieman pienempi per tick koska kestää kauemmin
        self.damage_interval = 10
        self.tracking_speed = 1.5  # Kuinka nopeasti säde seuraa kohdetta
        
        # Visuaalit
        self.image = pygame.Surface((self.beam_width + 60, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.rect = self.image.get_rect(midbottom=(int(self.current_x), int(self.current_y) + 20))
        # Säde tulee taivaalta, joten rectin yläreuna on 0 tai ylempänä
        
        # Partikkelit säteen sisällä
        self.particles = []

        # Magma spawn ajastin
        self.magma_timer = 0

    def update(self):
        self.timer += 1
        
        # 1. LUKITSE MAAGI (Channeling)
        if self.caster and not self.caster.is_dead:
            self.caster.attack_cooldown = 20 # Estä AI:ta tekemästä päätöksiä
            self.caster.is_sprinting = False
            self.caster.is_dashing = False
            self.caster.is_channeling = True # Pysäyttää Gladiator.run_combat_ai:n
            # Pysäytä liike täysin
            if hasattr(self.caster, 'velocity'):
                self.caster.velocity.x = 0.0
                self.caster.velocity.y = 0.0
            # Pakota idle-animaatio (valinnainen, riippuu rendereristä)
        else:
            # Jos taikoja kuolee, säde katkeaa
            self.kill()
            return

        # 2. VAHINKO (Damage Tick)
        # Päivitä sijainti (Tracking)
        if self.target_unit and not self.target_unit.is_dead:
            tx, ty = self.target_unit.rect.centerx, self.target_unit.rect.centery
            
            # Liiku kohti kohdetta
            dx = tx - self.current_x
            dy = ty - self.current_y
            dist = math.hypot(dx, dy)
            
            if dist > 1.0:
                move_dist = min(dist, self.tracking_speed)
                self.current_x += (dx / dist) * move_dist
                self.current_y += (dy / dist) * move_dist
        
        # Päivitä rect vastaamaan uutta sijaintia
        self.rect.midbottom = (int(self.current_x), int(self.current_y) + 20)

        # Deal Damage
        if self.timer % self.damage_interval == 0:
            self._deal_damage()
            # Tärähdys efekti
            if self.manager.vfx:
                self.manager.vfx.create_impact_sparks(int(self.current_x), int(self.current_y), color=(255, 220, 100), count=2)

        # 3. MAGMA LÄTÄKÖT
        self.magma_timer += 1
        if self.magma_timer > 25: # Joka ~0.4 sekuntia uutta magmaa
            self.magma_timer = 0
            # Hieman satunnainen sijainti säteen juuressa
            mx = int(self.current_x) + random.randint(-20, 20)
            my = int(self.current_y) + random.randint(-10, 10)
            puddle = MagmaPuddle(mx, my, self.manager, caster=self.caster)
            self.manager.vfx.floor_particles.add(puddle)

        # 4. PIIRRÄ SÄDE
        self._draw_beam()

        # 5. LOPETUS
        if self.timer >= self.duration:
            self.kill()

    def _deal_damage(self):
        # Osuu kaikkiin vihollisiin säteen alueella (rect)
        hit_rect = self.rect.inflate(-20, 0) # Hieman kapeampi osuma-alue kuin visuaali
        
        for unit in self.manager.all_units:
            if unit == self.caster or unit.is_dead: continue
            if unit.team_color == self.caster.team_color: continue # Ei friendly fire
            
            if hit_rect.colliderect(unit.rect):
                unit.take_damage(self.damage_per_tick, "Fire", attacker=self.caster, manager=self.manager)

    def _draw_beam(self):
        self.image.fill((0,0,0,0))
        
        # Pulssi
        pulse = math.sin(self.timer * 0.3) * 15
        w = self.beam_width + pulse
        center_x = self.image.get_width() // 2
        
        # --- PARTIKKELIT ---
        # Lisää uusia
        if random.random() < 0.4:
            self.particles.append({
                'x': center_x + random.randint(-int(w//3), int(w//3)),
                'y': self.rect.height,
                'speed': random.randint(10, 25),
                'size': random.randint(2, 5)
            })
        
        # Päivitä ja piirrä partikkelit
        for p in self.particles[:]:
            p['y'] -= p['speed']
            pygame.draw.circle(self.image, (255, 255, 200), (p['x'], int(p['y'])), p['size'])
            if p['y'] < 0:
                self.particles.remove(p)

        # --- SÄDE ---
        
        # Outer Glow (Oranssi/Punainen) - Levein, läpinäkyvin
        glow_w = int(w * 1.8)
        glow_rect = pygame.Rect(center_x - glow_w//2, 0, glow_w, self.rect.height)
        # Pygame ei tue gradientteja helposti, simuloidaan kerroksilla
        pygame.draw.rect(self.image, (255, 100, 0, 40), glow_rect)
        
        # Inner Glow (Keltainen)
        mid_w = int(w * 1.2)
        mid_rect = pygame.Rect(center_x - mid_w//2, 0, mid_w, self.rect.height)
        pygame.draw.rect(self.image, (255, 200, 50, 80), mid_rect)

        # Ydin (Valkoinen/Keltainen)
        core_w = int(w * 0.6)
        core_rect = pygame.Rect(center_x - core_w//2, 0, core_w, self.rect.height)
        pygame.draw.rect(self.image, (255, 255, 220, 200), core_rect)
        
        # Kirkas keskiviiva
        pygame.draw.line(self.image, (255, 255, 255), (center_x, 0), (center_x, self.rect.height), 4)


class MagmaPuddle(pygame.sprite.Sprite):
    def __init__(self, x, y, manager, caster=None, duration=300):
        super().__init__()
        self.manager = manager
        self.caster = caster
        self.duration = duration
        self.timer = 0
        self.damage = 2
        
        self.radius = random.randint(25, 40)
        self.image = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        
        self._draw_puddle()

    def update(self):
        self.timer += 1
        
        # Vahinko (joka 20. frame)
        if self.timer % 20 == 0:
            for unit in self.manager.all_units:
                if unit.is_dead: continue
                
                # Ei vahingoiteta omia (jos caster tiedossa)
                if self.caster and getattr(unit, "team_color", None) == getattr(self.caster, "team_color", None):
                    continue

                d = math.hypot(unit.rect.centerx - self.rect.centerx, unit.rect.centery - self.rect.centery)
                if d < self.radius:
                    unit.take_damage(self.damage, "Fire", attacker=self.caster, manager=self.manager)

        # Animaatio (kupliminen)
        if self.timer % 10 == 0:
            self._draw_puddle()

        # Fade out
        if self.timer >= self.duration:
            self.kill()
        elif self.timer > self.duration - 60:
            self.image.set_alpha(int(255 * (self.duration - self.timer) / 60))

    def _draw_puddle(self):
        self.image.fill((0,0,0,0))
        cx, cy = self.radius, self.radius
        
        # Pohja
        pygame.draw.circle(self.image, (180, 40, 0, 200), (cx, cy), self.radius)
        pygame.draw.circle(self.image, (255, 80, 0, 150), (cx, cy), int(self.radius * 0.8))
        
        # Kuplat
        for _ in range(3):
            bx = random.randint(5, self.radius*2 - 5)
            by = random.randint(5, self.radius*2 - 5)
            if math.hypot(bx-cx, by-cy) < self.radius - 5:
                pygame.draw.circle(self.image, (255, 200, 100), (bx, by), random.randint(2, 5))
