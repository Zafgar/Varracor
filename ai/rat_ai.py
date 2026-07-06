import pygame
import math
import random

# --- TEKOÄLYN TILAT ---
STATE_CHASE = 0   # Juokse kohti
STATE_RETREAT = 1 # Peruuta (hit-and-run)
STATE_FLANK = 2   # Kierrä sivulle (jos ruuhkaa)
STATE_TAUNT = 3   # Bossin erikoinen: vetäydy ja naura
STATE_SPIT = 4    # Bossin erikoinen: etähyökkäys

class RatAI:
    def __init__(self, unit):
        self.unit = unit
        self.current_target = None
        self.attack_range = getattr(unit, "attack_range", 40)
        
        # Tilamuuttujat
        self.state = STATE_CHASE
        self.state_timer = 0
        self.reaction_timer = random.randint(0, 10)
        
        # Yksilöllinen "rohkeus" (vaikuttaa perääntymisherkkyyteen)
        self.bravery = random.random() 

    def execute_ai(self, all_units, obstacles, manager=None):
        if self.unit.is_dead:
            return

        # --- RAT RIDER LOGIC ---
        if hasattr(self.unit, "charge_phase"):
            # 1. Handle Charge Sequence
            if self.unit.charge_phase == 1: # Windup
                self.unit.charge_timer -= 1
                if self.unit.charge_timer <= 0:
                    self.unit.charge_phase = 2 # Dash
                    self.unit.charge_timer = 80 # Dash duration (AI timeout)
                    
                    # Launch Dash
                    if self.current_target:
                        dx = self.current_target.rect.centerx - self.unit.rect.centerx
                        dy = self.current_target.rect.centery - self.unit.rect.centery
                        self.unit.facing_right = (dx > 0)
                        self.unit.perform_dash(dx, dy)
                        # Override dash speed for charge
                        self.unit.dash_speed_mult = 5.0 
                        self.unit.dash_timer = 80 # Override default 15 frames (Long charge)
                return

            if self.unit.charge_phase == 2: # Dashing
                # Check impact
                hits = pygame.sprite.spritecollide(self.unit, all_units, False)
                for h in hits:
                    if h != self.unit and h.team_color != self.unit.team_color and not h.is_dead:
                        # Impact!
                        self.unit.charge_phase = 3
                        self.unit.charge_timer = 20
                        self.unit.is_dashing = False
                        
                        # AoE
                        if manager:
                            manager.vfx.create_explosion(self.unit.rect.centerx, self.unit.rect.centery)
                            # Damage nearby
                            for u in all_units:
                                if u.team_color != self.unit.team_color and not u.is_dead:
                                    d = math.hypot(u.rect.centerx - self.unit.rect.centerx, u.rect.centery - self.unit.rect.centery)
                                    if d < 60:
                                        u.take_damage(20, "Physical", self.unit, manager)
                                        u.apply_status("Stun", 30)
                        break
                
                if not self.unit.is_dashing: # Stopped
                    if self.unit.charge_phase == 2: self.unit.charge_phase = 0
                return

            if self.unit.charge_phase == 3: # Impact recovery
                self.unit.charge_timer -= 1
                if self.unit.charge_timer <= 0:
                    self.unit.charge_phase = 0
                    self.state = STATE_RETREAT
                    self.state_timer = 45
                return

        # 1. Päivitä kohde ja ajastimet
        self.reaction_timer -= 1
        self.state_timer -= 1
        
        # Etsi uusi kohde jos vanha kuoli tai ajastin nollassa
        if self.reaction_timer <= 0 or not self._is_valid_target(self.current_target):
            self.current_target = self.find_nearest_enemy(all_units)
            self.reaction_timer = 15

        target = self.current_target
        if not target:
            return

        dist = math.hypot(target.rect.centerx - self.unit.rect.centerx, 
                          target.rect.centery - self.unit.rect.centery)

        # --- RIDER DECISIONS ---
        if hasattr(self.unit, "charge_phase"):
             # Charge
             if self.unit.charge_cooldown <= 0 and 250 < dist < 800:
                 self.unit.start_charge()
                 return
             # Throw
             if self.unit.throw_cooldown <= 0 and 150 < dist < 450:
                 if self.unit.perform_throw(target, manager):
                     self.state = STATE_RETREAT
                     self.state_timer = 40
                     return

        # --- UUSI: SPIT-HYÖKKÄYS (Vain Rat King) ---
        is_king = "Rat King" in self.unit.name
        spit_range = 250
        # Vain jos ei olla jo tekemässä jotain erikoista
        if is_king and self.state_timer <= 0 and dist > 80 and dist < spit_range:
            # Pieni todennäköisyys per frame päättää sylkeä
            if random.random() < 0.01: 
                self.state = STATE_SPIT
                self.state_timer = 70 # Animaation kesto
                if hasattr(self.unit, "perform_spit_attack"):
                    # Kutsu uutta hyökkäysmetodia
                    self.unit.perform_spit_attack(target, manager)
                return # Älä tee muuta tällä framella

        # 2. HYÖKKÄYS (Jos ollaan perillä)
        if dist <= self.attack_range:
            # Käänny kohti kohdetta
            dx = target.rect.centerx - self.unit.rect.centerx
            self.unit.facing_right = (dx > 0)

            if self.unit.attack_cooldown <= 0:
                self.unit.perform_attack(target, manager)
                # Iskun jälkeen päätös: peräännytäänkö?
                self._decide_after_attack_behavior()
            return # Ei liikuta lyönnin aikana

        # 3. TILAKONEEN LOGIIKKA (Liikkuminen)

        # -- SPIT (Vain Rat King) --
        if self.state == STATE_SPIT:
            # Pysyy paikallaan sylkemisen ajan
            if self.state_timer <= 0:
                self.state = STATE_CHASE
            return

        # -- TAUNT (Vain Rat King) --
        if self.state == STATE_TAUNT and "Rat King" in self.unit.name:
            self.move_away_from(target, all_units, obstacles)
            
            # Jos aika loppuu tai ollaan turvassa, lopeta taunt
            if self.state_timer <= 0 or dist > 350:
                if hasattr(self.unit, "do_taunt_action"):
                    self.unit.do_taunt_action() # Kutsuu naurun/summonin
                self.state = STATE_CHASE
            return

        # -- RETREAT (Hit-and-Run) --
        if self.state == STATE_RETREAT:
            self.move_away_from(target, all_units, obstacles)
            if self.state_timer <= 0:
                self.state = STATE_CHASE
            return

        # -- FLANK (Kiertäminen) --
        if self.state == STATE_FLANK:
            self.move_perpendicular(target, all_units, obstacles)
            if self.state_timer <= 0:
                self.state = STATE_CHASE
            return

        # -- CHASE (Oletus) --
        # Tarkista onko edessä ruuhkaa (liikaa kavereita)
        friends_near = self._count_friends_near(all_units, 45)
        
        # Jos ruuhkaa, vaihda FLANK-tilaan (kierrä)
        if friends_near > 2 and self.state_timer <= 0:
            self.state = STATE_FLANK
            self.state_timer = 40 # Kierrä n. 0.7 sekuntia
            
        # Rat King: Pieni mahdollisuus vetäytyä "nauramaan" (TAUNT)
        if "Rat King" in self.unit.name and self.state_timer <= 0:
            if random.random() < 0.005: # 0.5% per frame
                self.state = STATE_TAUNT
                self.state_timer = 120 # 2 sekuntia
                print("Rat King retreats to gloat!")

        # Oletusliike: Kohti pelaajaa
        self.move_towards(target, all_units, obstacles)

    # --- APUFUNKTIOT ---

    def _decide_after_attack_behavior(self):
        """Päätä peräännytäänkö iskun jälkeen"""
        # Tavalliset rotat perääntyvät usein (60%), Rat King harvoin (10%)
        chance = 0.6 if self.unit.name != "The Rat King" else 0.1
        
        if random.random() < chance:
            self.state = STATE_RETREAT
            self.state_timer = random.randint(20, 50) # Lyhyt pyrähdys taakse

    def _is_valid_target(self, target):
        return target and not getattr(target, "is_dead", True) and not getattr(target, "is_structure", False)

    def _count_friends_near(self, all_units, radius):
        """Laskee montako omaa tiimiläistä on 'radius'-etäisyydellä"""
        count = 0
        mx, my = self.unit.rect.center
        for u in all_units:
            if u == self.unit or u.is_dead: continue
            if u.team_color == self.unit.team_color:
                d = math.hypot(u.rect.centerx - mx, u.rect.centery - my)
                if d < radius:
                    count += 1
        return count

    def find_nearest_enemy(self, all_units):
        best_target = None
        min_dist = 99999
        my_team = self.unit.team_color
        my_pos = self.unit.rect.center

        for u in all_units:
            if u == self.unit or u.is_dead: continue
            if getattr(u, "is_structure", False): continue # Älä hyökkää seiniin
            if u.team_color == my_team: continue 

            d = math.hypot(u.rect.centerx - my_pos[0], u.rect.centery - my_pos[1])
            if d < min_dist:
                min_dist = d
                best_target = u
        return best_target

    # --- LIIKKUMINEN ---

    def move_towards(self, target, all_units, obstacles):
        self._generic_move(target, all_units, obstacles, mode="CHASE")

    def move_away_from(self, target, all_units, obstacles):
        self._generic_move(target, all_units, obstacles, mode="RETREAT")

    def move_perpendicular(self, target, all_units, obstacles):
        self._generic_move(target, all_units, obstacles, mode="FLANK")

    def _generic_move(self, target, all_units, obstacles, mode="CHASE"):
        tx, ty = target.rect.center
        mx, my = self.unit.rect.center
        
        # Suunta kohteeseen
        dx = tx - mx
        dy = ty - my
        dist = math.hypot(dx, dy) or 1
        dx /= dist
        dy /= dist

        # Muokkaa suuntaa tilan mukaan
        if mode == "RETREAT":
            dx = -dx
            dy = -dy
        elif mode == "FLANK":
            # Käännä 90 astetta. Parilliset ID:t oikealle, parittomat vasemmalle.
            if id(self.unit) % 2 == 0:
                old = dx
                dx = -dy
                dy = old
            else:
                old = dx
                dx = dy
                dy = -old

        # --- SEPARATION (Väistetään kavereita) ---
        sep_x, sep_y = 0, 0
        for u in all_units:
            if u == self.unit or u.is_dead: continue
            if u.team_color == self.unit.team_color:
                d_friend = math.hypot(u.rect.centerx - mx, u.rect.centery - my)
                
                # Jos liian lähellä kaveria, työnnä poispäin
                if d_friend < 25: 
                    push = (30 - d_friend) / 10
                    sep_x += (mx - u.rect.centerx) * push
                    sep_y += (my - u.rect.centery) * push
        
        # Yhdistä: Suunta + Erottelu
        final_dx = dx * 1.0 + sep_x * 0.8
        final_dy = dy * 1.0 + sep_y * 0.8
        
        l = math.hypot(final_dx, final_dy) or 1
        speed = self.unit.speed
        
        # Perääntyessä ollaan hieman hitaampia
        if mode == "RETREAT": speed *= 0.8
        
        # Varmistetaan ettei nopeus kasva liian suureksi (estää warppimisen)
        speed = min(speed, 6.0)

        move_x = (final_dx / l) * speed
        move_y = (final_dy / l) * speed

        self.unit.check_wall_collision(move_x, move_y, obstacles)
        
        if abs(move_x) > 0.1:
            self.unit.facing_right = (move_x > 0)