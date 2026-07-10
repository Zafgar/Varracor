import pygame
import random
import math
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

class LifeDrainBeam(pygame.sprite.Sprite):
    def __init__(self, manager, caster, target):
        super().__init__()
        self.manager = manager
        self.caster = caster
        self.target = target
        
        # Piirretään koko ruudun kokoiselle pinnalle, jotta voimme piirtää viivan mistä mihin tahansa
        self.image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(0,0))
        
        self.timer = 0
        
        # Asetukset
        self.mana_cost_per_tick = 1  # Kuluttaa 1 manaa joka tick (tai säädä alempana)
        self.damage_interval = 10    # Vahinkoa joka 10. frame
        self.damage_amount = 5       # Vahinko per isku
        self.heal_amount = 5         # Parannus per isku
        
        # Partikkelit (visuaalinen virtaus kohteesta taikojaan)
        self.particles = []

    def update(self, obstacles=None):
        self.timer += 1
        
        # 1. Tarkistukset: Onko caster/target hengissä?
        if not self.caster or self.caster.is_dead or not self.target or self.target.is_dead:
            self.kill()
            if self.caster: self.caster.is_channeling = False
            return

        # 2. Manan kulutus (Joka 4. frame, eli n. 15 manaa sekunnissa)
        if self.timer % 4 == 0:
            if self.caster.current_mana >= 1:
                self.caster.current_mana -= 1
            else:
                # Mana loppui -> Loitsu katkeaa
                self.kill()
                self.caster.is_channeling = False
                return

        # 3. Lukitse taikoja (Channeling)
        self.caster.is_channeling = True
        self.caster.attack_cooldown = 20
        self.caster.is_sprinting = False
        if hasattr(self.caster, 'velocity'):
            self.caster.velocity.x = 0
            self.caster.velocity.y = 0

        # 4. Vahinko ja Parannus (Life Steal)
        if self.timer % self.damage_interval == 0:
            # Tee vahinkoa (Magic type)
            dmg = self.target.take_damage(self.damage_amount, "Magic", attacker=self.caster, manager=self.manager)
            
            # Jos vahinkoa tehtiin, paranna taikojaa
            if dmg > 0:
                self.caster.heal(self.heal_amount, self.manager)
                
                # Visuaalinen palaute (pieni vihreä välähdys taikojalla)
                if self.manager.vfx:
                    self.manager.vfx.create_heal_effect(self.caster.rect.centerx, self.caster.rect.centery)

        # 5. Piirrä säde
        self._draw_beam()

    def _draw_beam(self):
        self.image.fill((0,0,0,0))
        
        start = pygame.math.Vector2(self.caster.rect.center)
        end = pygame.math.Vector2(self.target.rect.center)
        
        dist = start.distance_to(end)
        if dist < 1: return

        # --- SÄDE (Necrotic: Vihreä/Musta/Purppura) ---
        
        # 1. Musta ydin (sykkii)
        width_pulse = 3 + math.sin(self.timer * 0.5) * 1
        pygame.draw.line(self.image, (20, 0, 20), start, end, int(width_pulse + 4))
        
        # 2. Vihreä/Purppura hehku
        pygame.draw.line(self.image, (100, 255, 100, 150), start, end, int(width_pulse))
        
        # 3. Virtaavat partikkelit (Kohteesta -> Taikojaan)
        # Lisää uusi partikkeli
        if self.timer % 2 == 0:
            self.particles.append({'progress': 0.0, 'offset': random.uniform(-5, 5)})
            
        # Päivitä ja piirrä partikkelit
        for p in self.particles[:]:
            p['progress'] += 0.04 # Nopeus
            
            if p['progress'] >= 1.0:
                self.particles.remove(p)
                continue
            
            # Lerp: 0.0 on Target, 1.0 on Caster (koska imemme elämää)
            # Huom: start=caster, end=target. Joten 0=caster, 1=target.
            # Haluamme liikkua end -> start. Joten lerp(end, start, progress)
            
            pos = end.lerp(start, p['progress'])
            
            # Sivuttaisliike (Spiraali)
            perp = pygame.math.Vector2(-(end.y-start.y), end.x-start.x).normalize()
            wave = math.sin(p['progress'] * 10) * 10
            pos += perp * wave
            
            pygame.draw.circle(self.image, (50, 255, 50), (int(pos.x), int(pos.y)), 3)
            pygame.draw.circle(self.image, (150, 50, 255), (int(pos.x), int(pos.y)), 2)
