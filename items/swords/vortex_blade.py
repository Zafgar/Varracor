import pygame
import os
import math
import random
from items.base_item import Weapon
from sound_manager import sound_system
from vfx import VortexSlashProjectile

class VortexBlade(Weapon):
    def __init__(self):
        super().__init__()
        self.name = "Vortex Blade"
        self.rarity = "Artifact"
        self.cost = 99999
        self.description = "A blade forged from the fabric of the Abyss itself. Reality bends around it."
        
        self.type = "melee"
        self.slot_type = "main_hand"
        self.weapon_group = "sword"
        self.level_required = 30
        
        # GOD STATS
        self.damage = 150
        self.attack_range = 120 # Valtava range
        self.speed_bonus = 0.5 # Erittäin nopea
        self.scaling = {"STR": 1.5, "DEX": 1.0, "INT": 1.0}
        
        self.passive_bonuses = {
            "str": 100, "dex": 100, "int": 100,
            "hp": 500, "mana": 500, "mana_regen": 5.0
        }
        
        self.charge_time = 0
        self.max_charge = 40 # Nopea lataus
        self.charge_enabled = True
        self.last_charge_tick = 0
        self.charge_sound_channel = None # Äänikanava lataukselle
        self.special_cooldown = 0 # UUSI: Sisäinen cooldown erikoishyökkäykselle
        
        self.image = None
        self._load_image()

    def _load_image(self):
        path = "assets/gear/swords/vortex_blade_artifact.png"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (24, 64)) # Iso miekka
                self.big_image = img
            except Exception: 
                self.image = None

    def draw_card_icon(self, surface, x, y, size):
        img = getattr(self, "big_image", self.image)
        if img:
            ratio = img.get_width() / img.get_height()
            new_h = size
            new_w = int(new_h * ratio)
            scaled = pygame.transform.smoothscale(img, (new_w, new_h))
            surface.blit(scaled, (x + (size - new_w) // 2, y))
        else:
            # Fallback: Hehkuva miekka
            pygame.draw.line(surface, (50, 255, 200), (x + size*0.2, y + size*0.8), (x + size*0.8, y + size*0.2), 6)
            pygame.draw.circle(surface, (200, 255, 255), (x + size*0.5, y + size*0.5), size*0.3, 2)

    def on_update(self, owner, all_units, manager):
        """Päivittää aseen sisäistä tilaa (cooldown)."""
        if self.special_cooldown > 0:
            self.special_cooldown -= 1

    def update_charge(self, owner, manager):
        # Estä lataus jos SPECIAL cooldown on päällä (ei normaali attack cooldown)
        if self.special_cooldown > 0:
            return

        # --- UUSI: Peruuta blockaus kun ladataan ---
        if owner.is_blocking:
            owner.is_blocking = False

        now = pygame.time.get_ticks()
        if now - self.last_charge_tick > 100:
            self.charge_time = 0
        self.last_charge_tick = now
        
        # Aloita latausääni (loop) jos ei jo soi
        if self.charge_time == 1:
            if not self.charge_sound_channel or not self.charge_sound_channel.get_busy():
                self.charge_sound_channel = sound_system.play_sound("vortex_wave_load", loops=-1)

        owner.temp_speed_mult = 0.8 # Ei hidasta paljoa
        owner.is_charging = True
        if self.charge_time < self.max_charge:
            self.charge_time += 1
            
        # VFX: Lataus imee partikkeleita (Implosion)
        if manager:
            # Luo partikkeleita ympärille, jotka liikkuvat kohti keskustaa
            cx, cy = owner.rect.centerx, owner.rect.centery
            for _ in range(2):
                manager.vfx.create_void_particles(cx + random.randint(-30, 30), cy + random.randint(-30, 30))
            
            # Tärinä kasvaa latauksen myötä
            if self.charge_time > 20:
                shake = (self.charge_time - 20) / 10.0
                owner.rect.x += random.uniform(-shake, shake)
                owner.rect.y += random.uniform(-shake, shake)

    def release_charge(self, owner, manager, target_pos):
        # Pysäytä latausääni
        if self.charge_sound_channel:
            self.charge_sound_channel.stop()
            self.charge_sound_channel = None

        if self.charge_time > 20:
            # VORTEX SLASH (Projectile)
            dmg = self.calculate_damage({"str": owner.strength, "dex": owner.dexterity, "int": owner.intelligence})
            final_dmg = int(dmg * 4.5) # 4.5x damage projectile
            
            # Luodaan ammus suoraan tässä, jotta voimme säätää nopeutta ja kestoa
            # Speed 30 * Duration 40 = 1200px kantama (yli ruudun leveyden usein)
            proj = VortexSlashProjectile(
                owner.rect.centerx, owner.rect.centery, 
                target_pos, 
                speed=30, # Todella nopea
                damage=final_dmg, 
                owner=owner, 
                manager=manager
            )
            proj.duration = 40 
            manager.vfx.add_projectile(proj)
            
            sound_system.play_sound("vortex_wave_release")
            if manager: manager.trigger_screen_shake(10) # Kova tärähdys
            self.special_cooldown = 360 # 6 sekuntia (60fps)
            owner.attack_cooldown = 30 # Lyhyt animaatiolukko hahmolle
        else:
            # Normal Attack (Cleave)
            owner.perform_attack(None, manager, damage_mult=1.0, target_pos=target_pos)
        self.charge_time = 0

    def get_swing_rect(self, unit_rect, facing_right, attack_timer, total_cooldown, attack_vector=None):
        # MASSIVE CLEAVE
        swing_w = 120
        swing_h = 100
        
        if attack_vector:
            dx, dy = attack_vector
            dist = math.hypot(dx, dy) or 1
            offset = 60
            swing_x = unit_rect.centerx + (dx/dist) * offset - swing_w//2
            swing_y = unit_rect.centery + (dy/dist) * offset - swing_h//2
        else:
            swing_x = unit_rect.centerx if facing_right else unit_rect.centerx - swing_w
            swing_y = unit_rect.centery - 40

        return pygame.Rect(swing_x, swing_y, swing_w, swing_h)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown, total_cooldown=60, attack_vector=None):
        hand_x = unit_rect.centerx + (16 if facing_right else -16)
        hand_y = unit_rect.centery
        
        # Aina hehkuva aura (Vortex)
        time = pygame.time.get_ticks()
        glow_size = 40 + int(math.sin(time * 0.005) * 10)
        s = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
        # Pyörivä spiraali
        pygame.draw.circle(s, (20, 0, 40, 100), (glow_size, glow_size), glow_size) # Tumma tausta
        pygame.draw.circle(s, (50, 255, 200, 50), (glow_size, glow_size), glow_size - 10, 5) # Rengas
        surface.blit(s, (hand_x - glow_size, hand_y - glow_size))

        if not self.image: return
        
        angle = -20 if facing_right else 20
        scale = 1.0
        
        # Hyökkäysanimaatio (Massiivinen kaari)
        prog = 1.0 - (attack_cooldown / total_cooldown) if total_cooldown > 0 else 0
        anim_duration = 0.5 # Hieman hitaampi, painavampi isku
        
        if attack_cooldown > 0 and attack_vector and prog < anim_duration:
            anim_prog = prog / anim_duration
            dx, dy = attack_vector
            
            # Laske peruskulma kohti kohdetta
            base_angle = math.degrees(math.atan2(-dy, dx)) - 90
            
            swing_arc = 160 # Laaja kaari
            
            # Etäisyys hahmosta (irtonainen swing)
            # Käytetään attack_range:a skaalaamaan etäisyyttä
            reach_dist = self.attack_range * 0.6 
            
            if anim_prog < 0.6:
                # SWING VAIHE
                swing_pct = anim_prog / 0.6
                
                # Kulma muuttuu kaarella
                angle = base_angle + (swing_arc / 2) - (swing_arc * swing_pct)
                scale = 1.2 + (0.3 * math.sin(swing_pct * 3.14)) # Kasvaa
                
                # Laske sijainti: Siirretään miekkaa poispäin hahmosta sen osoittamaan suuntaan
                # Sprite osoittaa ylös (0 deg), joten +90 deg on matematiikan 0-kulma (oikealle)
                rad = math.radians(angle + 90)
                
                # Työnnetään miekkaa ulospäin, jotta se "pyyhkäisee" kauempaa
                # Lisätään pieni "syöksy" eteenpäin swingin keskellä
                thrust = math.sin(swing_pct * 3.14) * 20
                current_dist = reach_dist + thrust
                
                off_x = math.cos(rad) * current_dist
                off_y = -math.sin(rad) * current_dist # Screen Y inverted
                
                hand_x += off_x
                hand_y += off_y
                
                # Jälkikuva (Trail)
                trail_surf = pygame.transform.rotate(self.image, angle + (10 if facing_right else -10))
                trail_surf.set_alpha(100)
                trail_rect = trail_surf.get_rect(center=(hand_x, hand_y))
                surface.blit(trail_surf, trail_rect)
                
            else:
                # PALUU VAIHE (Return to idle)
                ret_pct = (anim_prog - 0.6) / 0.4
                
                # Interpoloi kulma ja sijainti takaisin
                target_angle = -20 if facing_right else 20
                start_angle = base_angle - (swing_arc / 2)
                
                angle = start_angle + (target_angle - start_angle) * ret_pct
                
                # Sijainti palaa nollaan (hand_x, hand_y alkuperäinen)
                # Interpoloidaan edellisestä sijainnista nollaan
                # Lasketaan missä oltiin swingin lopussa
                rad_end = math.radians(start_angle + 90)
                off_x_end = math.cos(rad_end) * reach_dist
                off_y_end = -math.sin(rad_end) * reach_dist
                
                hand_x += off_x_end * (1.0 - ret_pct)
                hand_y += off_y_end * (1.0 - ret_pct)

        img = self.image
        is_animating = (attack_cooldown > 0 and prog < anim_duration)
        
        if not facing_right and not is_animating: 
            img = pygame.transform.flip(img, True, False)
        
        if scale != 1.0:
            w = int(img.get_width() * scale)
            h = int(img.get_height() * scale)
            img = pygame.transform.scale(img, (w, h))
            
        rotated = pygame.transform.rotate(img, angle)
        surface.blit(rotated, rotated.get_rect(center=(hand_x, hand_y)))

    def on_attack_start(self, attacker, target, manager):
        sound_system.play_sound(random.choice(['vortex_blade_attack_1', 'vortex_blade_attack_2', 'vortex_blade_attack_3', 'vortex_blade_attack_4']))