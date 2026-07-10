import pygame
import math
import random
from ai.base_ai import BaseAI

# Tilat
STATE_HOVER = 0   # Etsii kohdetta ilmassa
STATE_DIVE = 1    # Syöksyy kohteeseen
STATE_ATTACK = 2  # Maassa hyökkäämässä
STATE_RETREAT = 3 # Lentää pois (korkealle ja kauas)

class BirdAI(BaseAI):
    def __init__(self, unit):
        super().__init__(unit)
        self.state = STATE_HOVER
        self.state_timer = 0
        self.target_height = 110 # Nostettu lentokorkeutta (oli 80)
        
        # Liikkeen pehmennys
        self.wander_angle = random.random() * 6.28
        self.orbit_angle = random.random() * 6.28 # Kaartelua varten
        
        # Off-screen pako
        self.retreat_pos = None

    def execute_ai(self, all_units, obstacles, manager=None):
        if self.unit.is_dead: return

        # 0. Korkeuden hallinta (Visuaalinen Z-akseli)
        # Jos ollaan ilmassa, jump_height on suuri -> varjo jää maahan, sprite nousee
        current_h = getattr(self.unit, "jump_height", 0)
        # Lisätään "kellunta" (bobbing) ilmassa ollessa
        bobbing = math.sin(pygame.time.get_ticks() * 0.005 + id(self.unit)) * 15
        
        if self.state in [STATE_HOVER, STATE_RETREAT]:
            # Nouse ilmaan
            target_h = self.target_height + bobbing
            self.unit.jump_height += (target_h - current_h) * 0.05
        elif self.state == STATE_DIVE:
            # Laskeudu syöksyssä
            if current_h > 10:
                self.unit.jump_height = max(10, current_h - 6)
        elif self.state == STATE_ATTACK:
            # Pysy maassa
            if current_h > 0:
                self.unit.jump_height = max(0, current_h - 8)

        # 1. Tilakone
        self.state_timer -= 1

        # --- STATE: HOVER (Etsi ranged-kohdetta) ---
        if self.state == STATE_HOVER:
            self.unit.animation_state = "fly"
            
            # Etsi paras kohde (Ranged/Mage prioriteetti)
            target = self._find_ranged_target(all_units)
            
            if target:
                self.current_target = target
                # Jos ollaan tarpeeksi lähellä, syöksy
                dist = math.hypot(target.rect.centerx - self.unit.rect.centerx, 
                                  target.rect.centery - self.unit.rect.centery)
                
                # Jos ollaan lähellä, kaarretaan (Orbit)
                if dist < 350:
                    self._circle_target(target)
                    # Satunnainen syöksy
                    if self.state_timer <= 0 and random.random() < 0.02:
                        self.state = STATE_DIVE
                        self.state_timer = 60
                else:
                    # Lennä nopeasti kohti (ilman esteitä)
                    self._fly_towards(target.rect.centerx, target.rect.centery, obstacles)
            else:
                # Ei kohdetta, kiertele ilmassa
                self._wander_in_air(obstacles)

        # --- STATE: DIVE (Syöksy) ---
        elif self.state == STATE_DIVE:
            self.unit.animation_state = "fly"
            target = self.current_target
            
            if target and not target.is_dead:
                dist = math.hypot(target.rect.centerx - self.unit.rect.centerx,
                                  target.rect.centery - self.unit.rect.centery)

                # Liiku erittäin nopeasti
                self._fly_towards(target.rect.centerx, target.rect.centery, obstacles, speed_mult=1.5)

                if dist < 50:
                    self.state = STATE_ATTACK
                    self.state_timer = 120 # Hyökkää 2 sekuntia
            else:
                # Kohde kuoli tai katosi kesken syöksyn -> takaisin ilmaan
                self.state = STATE_HOVER
                self.state_timer = 60

            # Jos syöksy kestää liian kauan (esim. kohde juoksee karkuun), nouse takaisin
            # (BUGIKORJAUS: aiempi else-haara palautti HOVERiin joka frame,
            #  jolloin syöksy keskeytyi heti eikä varis koskaan hyökännyt)
            if self.state == STATE_DIVE and self.state_timer <= 0:
                self.state = STATE_RETREAT
                self.state_timer = 60

        # --- STATE: ATTACK (Maassa) ---
        elif self.state == STATE_ATTACK:
            target = self.current_target
            
            # Yritä kiljua (Silence) heti kun maassa
            if self.unit.scream_cooldown <= 0:
                self.unit.perform_scream(manager)
            
            if target and not target.is_dead:
                dist = math.hypot(target.rect.centerx - self.unit.rect.centerx, 
                                  target.rect.centery - self.unit.rect.centery)
                
                if dist <= self.unit.attack_range:
                    self.unit.perform_attack(target, manager)
                else:
                    # Juokse/Hypi maassa kohti
                    self._move_towards(target.rect.centerx - self.unit.rect.centerx,
                                       target.rect.centery - self.unit.rect.centery,
                                       dist, obstacles, all_units)
            
            # Jos aika loppuu, pakene
            if self.state_timer <= 0:
                self.state = STATE_RETREAT
                self.state_timer = 180 # 3 sekuntia pakoa
                # Valitse satunnainen suunta kauas (jopa ruudun ulkopuolelle)
                angle = random.random() * 6.28
                dist = 1000
                self.retreat_pos = (self.unit.rect.centerx + math.cos(angle)*dist,
                                    self.unit.rect.centery + math.sin(angle)*dist)

        # --- STATE: RETREAT (Palaa taivaalle) ---
        elif self.state == STATE_RETREAT:
            self.unit.animation_state = "fly"
            
            if self.retreat_pos:
                self._fly_towards(self.retreat_pos[0], self.retreat_pos[1], obstacles, speed_mult=1.3)
            
            if self.state_timer <= 0:
                self.state = STATE_HOVER
                self.state_timer = 60

    def _find_ranged_target(self, all_units):
        """Etsii ensisijaisesti jousimiehiä tai maageja."""
        best = None
        best_score = -1000
        
        my_team = self.unit.team_color
        mx, my = self.unit.rect.center
        
        for u in all_units:
            if u.is_dead or u == self.unit or u.team_color == my_team: continue
            if getattr(u, "is_structure", False): continue
            
            score = 0
            dist = math.hypot(u.rect.centerx - mx, u.rect.centery - my)
            score -= dist * 0.1 # Lähempänä parempi
            
            # Ranged bonus
            if getattr(u, "weapon_type", "") == "ranged":
                score += 500
            # Mage bonus
            if getattr(u, "max_spell_tier", 0) > 0:
                score += 600
            # Silence bonus (älä hyökkää jos jo hiljennetty)
            if hasattr(u, "has_status") and u.has_status("Silence"):
                score -= 300
                
            if score > best_score:
                best_score = score
                best = u
        return best

    def _fly_towards(self, tx, ty, obstacles, speed_mult=1.0):
        """Lentäminen jättää huomiotta seinät (obstacles)."""
        dx = tx - self.unit.rect.centerx
        dy = ty - self.unit.rect.centery
        dist = math.hypot(dx, dy) or 1
        
        # Kaartelu: Lisätään sivuttaisliikettä siniaallolla
        time_factor = pygame.time.get_ticks() * 0.002 + (id(self.unit) % 100)
        curve_amount = math.sin(time_factor) * 0.8 # Kaartelun voimakkuus
        
        # Perusvektori
        dir_x = dx / dist
        dir_y = dy / dist
        
        # Sivuttaisvektori (-y, x)
        perp_x = -dir_y
        perp_y = dir_x
        
        # Yhdistetään
        final_dx = dir_x + (perp_x * curve_amount)
        final_dy = dir_y + (perp_y * curve_amount)
        l = math.hypot(final_dx, final_dy) or 1
        
        speed = self.unit.speed * speed_mult
        
        move_x = (final_dx / l) * speed
        move_y = (final_dy / l) * speed
        
        self.unit.check_wall_collision(move_x, move_y, obstacles)
        
        if abs(move_x) > 0.1:
            self.unit.facing_right = (move_x > 0)

    def _circle_target(self, target, obstacles=None):
        """Kiertää kohdetta ilmassa."""
        self.orbit_angle += 0.05 # Pyörimisnopeus
        radius = 150
        
        # Laske haluttu sijainti kohteen ympärillä
        dest_x = target.rect.centerx + math.cos(self.orbit_angle) * radius
        dest_y = target.rect.centery + math.sin(self.orbit_angle) * radius
        
        # Lennä sinne pehmeästi
        # Huom: obstacles voi olla None, jos kutsutaan ilman kontekstia, mutta tässä se tulee execute_ai:sta
        obs = obstacles if obstacles is not None else []
        self._fly_towards(dest_x, dest_y, obs, speed_mult=0.8)

    def _wander_in_air(self, obstacles):
        self.wander_angle += random.uniform(-0.1, 0.1)
        dx = math.cos(self.wander_angle) * 100
        dy = math.sin(self.wander_angle) * 100
        # Lennä ympyrää/haahuile
        move_x = dx * 0.05
        move_y = dy * 0.05
        self.unit.check_wall_collision(move_x, move_y, obstacles)
        self.unit.facing_right = (dx > 0)
