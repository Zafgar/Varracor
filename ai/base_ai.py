import pygame
import math
import random

class BaseAI:
    def __init__(self, unit):
        self.unit = unit
        self.current_target = None
        self.reaction_timer = 0
        self.rethink_timer = 0
        self.state = "idle"
        self.charge_timer = 0 # UUSI: Latausaika jousille/sauvoille
        self.target_last_pos = {} # UUSI: Vihollisten viimeisimpien sijaintien muisti
        
        # Stuck detection
        self.last_pos = (0, 0)
        self.stuck_counter = 0
        self.stuck_direction = pygame.math.Vector2(0, 0) # Suunta johon yritetään paeta
        self.escape_timer = 0
        self.escape_direction = pygame.math.Vector2(0, 0)
        
        # Pathfinding
        self.current_path = [] # Lista pisteitä [(x,y), (x,y)...]
        self.path_timer = 0 # Kuinka usein reitti lasketaan uudelleen

    def execute_ai(self, all_units, obstacles=None, manager=None):
        if self.unit.is_dead: return
        
        # Jos stunnattu, ei tehdä mitään (Gladiator hoitaa liikkumattomuuden)
        if getattr(self.unit, "stun_timer", 0) > 0:
            # Nollataan lataus ja tila, jotta AI ei "fumblee" iskua heti herättyään
            self.charge_timer = 0
            self.state = "stunned"
            return

        # Nollataan lataus jos ei hyökätä
        if self.state not in ["charging", "attack", "reloading"]:
            self.charge_timer = 0

        # 0. RESET STATES (Oletuksena ei blokata/juosta, ellei logiikka toisin päätä)
        self.unit.set_sprinting(False)
        self.unit.set_blocking(False)

        # 1. TARGETING LOGIC
        self.rethink_timer -= 1
        if self.rethink_timer <= 0 or not self._is_valid_target(self.current_target):
            self.current_target = self.find_best_target(all_units, manager)
            self.rethink_timer = 30 
            # Nollataan ennustus kun kohde vaihtuu
            self.target_last_pos.clear()

        target = self.current_target
        
        # 1.5 RETREAT LOGIC (Low HP) - Pakeneminen menee kaiken edelle
        # Jos HP < 20% ja staminaa on, yritä paeta hetkeksi
        if self.unit.current_hp < self.unit.max_hp * 0.20 and self.unit.current_stamina > 40:
            if target and not getattr(target, "is_dead", True):
                dist_sq = (target.rect.centerx - self.unit.rect.centerx)**2 + (target.rect.centery - self.unit.rect.centery)**2
                if dist_sq < 25000: # Alle 150px
                    # Juokse poispäin
                    dx = self.unit.rect.centerx - target.rect.centerx
                    dy = self.unit.rect.centery - target.rect.centery
                    
                    self.unit.set_sprinting(True)
                    self.state = "retreat"
                    # Käytetään move_towards ilman pathfindingia pakenemiseen
                    self._move_towards(dx, dy, math.hypot(dx, dy), obstacles, all_units, manager)
                    return

        # 2. SELF PRESERVATION (AoE & Kiting) - High Priority
        # Vaatii staminaa (Dash cost = 30)
        if manager and self.unit.current_stamina > 35:
            # A) AoE Dodge (Väistetään maassa olevia efektejä)
            if hasattr(manager, "vfx") and hasattr(manager.vfx, "floor_particles"):
                hits = pygame.sprite.spritecollide(self.unit, manager.vfx.floor_particles, False)
                
                dangerous_hazard = None
                for h in hits:
                    h_team = getattr(h, "team", None)
                    my_team = getattr(self.unit, "team_color", None)
                    # Jos efektillä ei ole tiimiä (neutraali) tai se on eri tiimin -> vaarallinen
                    if h_team is None or h_team != my_team:
                        dangerous_hazard = h
                        break

                if dangerous_hazard:
                    # Dash away from the center of the hazard
                    hazard = dangerous_hazard
                    h_dx = self.unit.rect.centerx - hazard.rect.centerx
                    h_dy = self.unit.rect.centery - hazard.rect.centery
                    # Jos ollaan ihan keskellä, arvotaan suunta
                    if h_dx == 0 and h_dy == 0: 
                        h_dx, h_dy = random.choice([-1, 1]), random.choice([-1, 1])
                    
                    if self.unit.perform_dash(h_dx, h_dy):
                        return # Dashing takes control

            # B) Ranged Kiting (Jos vihollinen liian lähellä)
            if target and not getattr(target, "is_dead", True):
                is_ranged = (self.unit.weapon_type == "ranged" or self.unit.max_spell_tier > 0)
                t_dx = target.rect.centerx - self.unit.rect.centerx
                t_dy = target.rect.centery - self.unit.rect.centery
                t_dist = math.hypot(t_dx, t_dy)
                
                if is_ranged and t_dist < 80:
                    if self.unit.perform_dash(-t_dx, -t_dy):
                        return

        if not target:
            self.state = "idle"
            return
        
        # --- UUSI: PREDICTION LOGIC ---
        target_vx, target_vy = 0, 0
        if target in self.target_last_pos:
            last_x, last_y = self.target_last_pos[target]
            target_vx = target.rect.centerx - last_x
            target_vy = target.rect.centery - last_y
        # Päivitä viimeisin sijainti
        self.target_last_pos[target] = target.rect.center
        # -----------------------------

        # 2. GEOMETRY
        dx = target.rect.centerx - self.unit.rect.centerx
        dy = target.rect.centery - self.unit.rect.centery
        dist = math.hypot(dx, dy)
        
        # Päivitä attack_vector visuaaleja varten
        self.unit.attack_vector = (dx, dy)
        
        attack_range = getattr(self.unit, "attack_range", 40)
        
        # 3. ACTION
        
        # Spell casting
        if hasattr(self.unit, "try_cast_spells"):
            if self.unit.try_cast_spells(target, all_units, manager):
                self.reaction_timer = 20
                self.state = "cast"
                if dx > 0: self.unit.facing_right = True
                else: self.unit.facing_right = False
                return

        # --- ASEKOHTAINEN LOGIIKKA ---
        weapon = self.unit.equipment.get("main_hand")
        weapon_group = getattr(weapon, "weapon_group", "") if weapon else ""
        
        # TARKISTUS: Tukeeko ase uutta latausmekaniikkaa?
        has_charge_mech = getattr(weapon, "charge_enabled", False) if weapon else False
        
        is_ranged_charge_weapon = weapon_group in ["bow", "staff"]
        is_crossbow = weapon_group == "crossbow"
        is_book = weapon_group == "book"
        
        # Uudet lataavat melee-aseet
        is_spear = weapon_group == "spear"
        is_sword = weapon_group == "sword"
        is_axe = weapon_group == "axe"
        is_mace = weapon_group == "mace"
        is_dagger = weapon_group == "dagger"

        # --- RANGED WEAPON LOGIC (UUSI) ---
        # Käytetään vain jos ase tukee latausta. Muuten mennään vanhaan melee-logiikkaan (else).
        if (is_ranged_charge_weapon or is_crossbow or is_book or is_dagger) and has_charge_mech:
            # Käänny kohti kohdetta
            if abs(dx) > 0:
                self.unit.facing_right = (dx > 0)

            # --- PREDICTED TARGET POSITION ---
            # Arvioidaan ammuksen lentoaika etäisyyden ja aseen tyypin perusteella
            proj_speed = 15.0 # Oletusnopeus
            if is_crossbow: proj_speed = 25.0
            elif is_book: proj_speed = 15.0
            elif weapon_group == "staff": proj_speed = 12.0
            elif weapon_group == "bow": proj_speed = 20.0 # Oletetaan hyvä lataus
            
            time_to_hit = dist / max(1.0, proj_speed)
            prediction_frames = min(45, time_to_hit) # Rajoitetaan ennustus max 45 frameen
            
            predicted_x = target.rect.centerx + target_vx * prediction_frames
            predicted_y = target.rect.centery + target_vy * prediction_frames
            predicted_pos = (predicted_x, predicted_y)
            # ---------------------------------

            # A) Crossbow: Lataa ensin, ammu sitten
            if is_crossbow:
                # Käytetään getattr varmuuden vuoksi
                if not getattr(weapon, "is_loaded", False):
                    # Aloita lataus vain jos stamina riittää koko lataukseen
                    # (lataus vie ~0.7/frame * load_time). Jatka käynnissä
                    # olevaa latausta niin kauan kuin staminaa on jäljellä.
                    # (BUGIKORJAUS: aiempi versio putosi stamina loppuessa
                    #  ampumishaaraan, joka nollasi latauksen joka frame ->
                    #  varsijousi ei koskaan ampunut.)
                    loading = getattr(weapon, "load_progress", 0) > 0
                    # Latauksen kokonaiskustannus (sama kaava kuin update_chargessa),
                    # rajattuna yksikön maksimistaminaan
                    drain = max(0.2, 0.8 - self.unit.strength * 0.02)
                    need = drain * getattr(weapon, "load_time", 80) + 4
                    need = min(need, self.unit.max_stamina * 0.9)
                    if (loading and self.unit.current_stamina > 2) or \
                       (not loading and self.unit.current_stamina >= need):
                        self.state = "reloading"
                        self.unit.temp_speed_mult = 0.0 # Pakota pysähtymään
                        weapon.update_charge(self.unit, manager)
                    else:
                        # Palaudu paikallaan, älä yritä ampua lataamattomalla
                        self.state = "recovering"
                    return
                # Jos ladattu, jatka normaalisti ampumaan

            # B) Bow/Staff: Lataa kun kantamalla
            if is_ranged_charge_weapon:
                # PANIC SHOT: Jos vihollinen iholle, ammu heti ja peräänny
                if dist < 60 and self.charge_timer > 0:
                    weapon.release_charge(self.unit, manager, target.rect.center)
                    self.charge_timer = 0
                    # Yritä väistää taaksepäin (normaali liike, ei dash, säästää staminaa)
                    back_x = self.unit.rect.centerx - (dx * 2)
                    back_y = self.unit.rect.centery - (dy * 2)
                    self.navigate_to((back_x, back_y), obstacles, all_units, manager)
                    return

                if dist <= attack_range:
                    # UUSI: Tarkista stamina jouselle (Sauva ei vie staminaa latauksessa)
                    stamina_ok = True
                    if weapon_group == "bow" and self.unit.current_stamina < 15:
                        stamina_ok = False
                    
                    if stamina_ok:
                        self.state = "charging"
                        self.charge_timer += 1
                        weapon.update_charge(self.unit, manager)
                        # Ammu kun täynnä tai kohde karkaamassa
                        if self.unit.attack_cooldown <= 0 and self.charge_timer >= weapon.max_charge:
                            weapon.release_charge(self.unit, manager, predicted_pos)
                            self.charge_timer = 0
                        return # Pysy paikallaan ladatessa
                else:
                    # Jos oltiin lataamassa, ammu heikko laukaus ja lähde perään
                    if self.charge_timer > 10:
                        weapon.release_charge(self.unit, manager, predicted_pos)
                    self.charge_timer = 0
                    self.state = "chase"
                    self.navigate_to(target.rect.center, obstacles, all_units, manager)
                    return

            # C) Dagger Throw: Lataa jos kaukana, lyö jos lähellä
            if is_dagger:
                if dist > attack_range and dist < 300 and self.unit.attack_cooldown <= 0: # Heittoetäisyys + Cooldown check
                    self.state = "charging"
                    self.charge_timer += 1
                    weapon.update_charge(self.unit, manager)
                    if self.charge_timer >= 20: # Puoli latausta riittää heittoon
                        weapon.release_charge(self.unit, manager, predicted_pos)
                        self.charge_timer = 0
                    return
                # Jos lähellä, putoaa alas melee-logiikkaan (koska dagger on myös melee)
                if dist > attack_range: pass # Jatka liikkumista

            # D) Book/Crossbow (Loaded): Ammu heti kun kantamalla
            if dist <= attack_range:
                if self.unit.attack_cooldown <= 0:
                    weapon.release_charge(self.unit, manager, predicted_pos)
                return
            else:
                self.state = "chase"
                self.navigate_to(target.rect.center, obstacles, all_units, manager)
                return

        # --- MELEE WEAPON LOGIC (VANHA) ---
        else:
            # Blocking
            # Blokataan jos vihollinen lähellä JA (kilpi TAI vähän HP) JA staminaa riittää
            if dist < 80 and self.unit.current_stamina > 20:
                offhand = self.unit.equipment.get("off_hand")
                mainhand = self.unit.equipment.get("main_hand")
                
                has_shield = offhand and str(getattr(offhand, "type", "")).lower() == "shield"
                has_weapon = mainhand and getattr(mainhand, "type", "") == "melee" and getattr(mainhand, "name", "") != "Fists"
                
                can_block = has_shield or has_weapon
                
                # Blokataan jos vihollinen katsoo meihin (todennäköisesti lyömässä)
                if can_block and (self.unit.attack_cooldown > 10 or self.unit.current_hp < self.unit.max_hp * 0.4):
                    self.unit.set_blocking(True)

            # --- MELEE CHARGE LOGIC (Spear/Sword) ---
            is_heavy_melee = (is_spear or is_sword or is_axe or is_mace)
            # Vain jos staminaa on tarpeeksi (> 40) TAI lataus on jo käynnissä (ettei se katkea)
            if is_heavy_melee and has_charge_mech and (self.unit.current_stamina > 40 or self.charge_timer > 0):
                # Jos ollaan lähellä, voidaan ladata power hit / dash
                # Spear: Dash range on pidempi
                charge_dist = attack_range + (100 if is_spear else 0)
                
                if dist <= charge_dist or self.charge_timer > 0:
                    # Jos kohde karkaa liian kauas latauksen aikana, vapauta heti (älä peruuta)
                    if self.charge_timer > 0 and dist > charge_dist + 50:
                        weapon.release_charge(self.unit, manager, target.rect.center)
                        self.charge_timer = 0
                        return

                    self.unit.set_blocking(False) # Varmista ettei blokata latauksen aikana
                    self.state = "charging"
                    self.charge_timer += 1
                    weapon.update_charge(self.unit, manager)
                    # Vapauta kun täynnä JA cooldown on ohi (ettei hukata latausta)
                    if self.charge_timer >= weapon.max_charge:
                        if self.unit.attack_cooldown <= 0:
                            weapon.release_charge(self.unit, manager, target.rect.center)
                            self.charge_timer = 0
                    return

            # Attack or Move
            if dist <= attack_range:
                self.state = "attack"
                if abs(dx) > 0: self.unit.facing_right = (dx > 0)
                if self.unit.attack_cooldown <= 0:
                    self.unit.set_blocking(False)
                    self.unit.perform_attack(target, manager)
            else:
                self.state = "chase"
                
                # --- SMART CHASE LOGIC (UUSI) ---
                target_is_ranged = False
                if getattr(target, "weapon_type", "") == "ranged" or getattr(target, "max_spell_tier", 0) > 0:
                    target_is_ranged = True
                
                target_is_fleeing = False
                # Dot product: (target_v . to_target) > 0 means moving away
                if (target_vx * dx + target_vy * dy) > 0: 
                    target_is_fleeing = True

                # 1. Dash Logic (Gap Close / Dodge)
                # Käytä dashia jos kohde kaukana ja staminaa riittää hyökkäykseenkin
                if dist > 100 and self.unit.current_stamina > 50:
                    should_dash = False
                    dash_dx, dash_dy = dx, dy

                    if target_is_ranged:
                        should_dash = True
                        # Zig-zag lähestyminen (väistöliike)
                        if dist > 150:
                            angle = math.atan2(dy, dx)
                            offset = random.uniform(-0.5, 0.5) # +/- ~30 astetta
                            dash_dx = math.cos(angle + offset) * 100
                            dash_dy = math.sin(angle + offset) * 100
                    
                    elif target_is_fleeing:
                        should_dash = True
                    
                    if should_dash:
                        if self.unit.perform_dash(dash_dx, dash_dy):
                            return # Dash hoitaa liikkeen

                # 2. Sprint Logic
                # Sprinttaa herkemmin jos kohde on ranged tai pakenee
                sprint_limit = 200
                if target_is_ranged or target_is_fleeing:
                    sprint_limit = 80
                
                if dist > sprint_limit and self.unit.current_stamina > 35:
                    self.unit.set_sprinting(True)
                
                self.navigate_to(target.rect.center, obstacles, all_units, manager)

    def _is_valid_target(self, t):
        return t and not getattr(t, "is_dead", True) and not getattr(t, "is_structure", False)

    def find_best_target(self, all_units, manager=None):
        best = None
        best_score = -100000
        
        my_team = getattr(self.unit, "team_color", None)
        mx, my = self.unit.rect.center
        
        for other in all_units:
            if other == self.unit or getattr(other, "is_dead", False): continue
            if getattr(other, "is_structure", False): continue
            if my_team and getattr(other, "team_color", None) == my_team: continue
            
            ox, oy = other.rect.center
            d = math.hypot(ox - mx, oy - my)
            
            score = -d
            if other.current_hp < other.max_hp * 0.3:
                score += 150 
                
            # --- TEAMWORK: Suojele pelaajaa ---
            if manager and manager.player_character and self.unit.team_color == manager.player_character.team_color:
                if other in manager.player_character.attackers:
                    score += 200 # Korkea prioriteetti komentajan kimppuun käyville
            
            if score > best_score:
                best_score = score
                best = other
        return best

    def navigate_to(self, target_pos, obstacles, all_units, manager):
        """Älykäs liikkuminen: Käyttää pathfinderia jos saatavilla, muuten suoraa liikettä."""
        
        # Jos managerilla on pathfinder ja kohde on kaukana (> 200px), käytä reitinhakua
        use_pathfinding = False
        dist_sq = (target_pos[0] - self.unit.rect.centerx)**2 + (target_pos[1] - self.unit.rect.centery)**2
        
        if manager and getattr(manager, "pathfinder", None) and dist_sq > 40000: # > 200px
            use_pathfinding = True

        if use_pathfinding:
            # Päivitä reitti ajoittain (esim. 60 framea)
            if self.path_timer <= 0 or not self.current_path:
                self.current_path = manager.pathfinder.get_path(self.unit.rect.center, target_pos)
                self.path_timer = 60
            else:
                self.path_timer -= 1

            # Seuraa reittiä
            if self.current_path:
                # Ota seuraava piste
                next_point = self.current_path[0]
                
                # Jos ollaan lähellä pistettä, poista se ja ota seuraava
                d_to_point = math.hypot(next_point[0] - self.unit.rect.centerx, next_point[1] - self.unit.rect.centery)
                if d_to_point < 20:
                    self.current_path.pop(0)
                    if self.current_path:
                        next_point = self.current_path[0]
                    else:
                        # Reitti loppu, liiku suoraan kohteeseen
                        next_point = target_pos
                
                # Liiku kohti next_point
                dx = next_point[0] - self.unit.rect.centerx
                dy = next_point[1] - self.unit.rect.centery
                self._move_towards(dx, dy, math.hypot(dx, dy), obstacles, all_units, manager)
                return

        # Fallback: Suora liike
        dx = target_pos[0] - self.unit.rect.centerx
        dy = target_pos[1] - self.unit.rect.centery
        
        # FLANKING (Kevyt sivuttaisliike lähestyessä)
        # Lisätään pieni sivuttaisvektori perustuen yksikön ID:hen, jotta ne eivät jonoudu
        if math.hypot(dx, dy) > 60:
            flank_mod = (id(self.unit) % 20 - 10) * 2.0 # -20 ... +20
            dx += -dy * 0.05 * (1 if flank_mod > 0 else -1)
            dy += dx * 0.05 * (1 if flank_mod > 0 else -1)
            
        self._move_towards(dx, dy, math.hypot(dx, dy), obstacles, all_units, manager)

    def _move_towards(self, dx, dy, dist, obstacles, all_units, manager=None):
        if dist == 0: return
        
        # Normalisoitu suunta kohteeseen
        ndx = dx / dist
        ndy = dy / dist
        
        # --- WHISKER LOGIC (Viikset) ---
        # Tarkistetaan onko suora reitti tukossa. Jos on, kokeillaan viistosuuntia.
        # Tämä auttaa löytämään oviaukot ja kiertämään kulmat.
        if obstacles:
            look_ahead = 60 # Kuinka kauas katsotaan
            center = self.unit.rect.center
            
            # Tarkista suoraan eteen
            if self._raycast(center, (ndx, ndy), look_ahead, obstacles):
                # Tukossa! Kokeile vasenta ja oikeaa viistoa (45 astetta)
                angle = math.atan2(ndy, ndx)
                left_angle = angle - 0.78 # -45 deg
                right_angle = angle + 0.78 # +45 deg
                
                # Tarkista vasen
                if not self._raycast(center, (math.cos(left_angle), math.sin(left_angle)), look_ahead, obstacles):
                    ndx, ndy = math.cos(left_angle), math.sin(left_angle)
                # Tarkista oikea (jos vasenkin tukossa tai muuten vaan)
                elif not self._raycast(center, (math.cos(right_angle), math.sin(right_angle)), look_ahead, obstacles):
                    ndx, ndy = math.cos(right_angle), math.sin(right_angle)
                # Jos molemmat tukossa, luotetaan obstacle avoidanceen

        # 0. Escape Logic (Jos ollaan jumissa, peräännytään/kierretään hetki)
        if self.escape_timer > 0:
            self.escape_timer -= 1
            # Korvataan kohteen suunta pakenemissuunnalla
            ndx, ndy = self.escape_direction.x, self.escape_direction.y
        elif self._check_stuck():
            self.escape_timer = 45 # n. 0.75 sekuntia pakotettua liikettä
            # Lasketaan suunta joka on poikittain kohteeseen nähden (kierretään)
            # Lisätään hieman "taaksepäin" komponenttia jotta irrotaan seinästä
            to_target = pygame.math.Vector2(dx, dy).normalize() if dist > 0 else pygame.math.Vector2(1, 0)
            
            # Valitaan satunnaisesti vasen tai oikea kiertosuunta
            if random.random() < 0.5:
                perp = pygame.math.Vector2(-to_target.y, to_target.x)
            else:
                perp = pygame.math.Vector2(to_target.y, -to_target.x)
                
            # Sekoitetaan: 70% sivulle, 30% taaksepäin
            back = -to_target
            self.escape_direction = (perp * 0.7 + back * 0.3).normalize()
            
            ndx, ndy = self.escape_direction.x, self.escape_direction.y

        # 1. Separation (Väistetään muita yksiköitä)
        sep_x, sep_y = self._calculate_separation(all_units)
        
        # 2. Obstacle Avoidance (Väistetään seiniä pehmeästi)
        obs_x, obs_y = self._calculate_obstacle_avoidance(obstacles)
        
        # 3. Hazard Avoidance (UUSI: Vältä maassa olevia vaaroja kuten tulta/happoa)
        haz_x, haz_y = 0, 0
        if manager and hasattr(manager, "vfx") and hasattr(manager.vfx, "floor_particles"):
             haz_x, haz_y = self._calculate_hazard_avoidance(manager.vfx.floor_particles)
        
        # Yhdistetään vektorit painotuksilla
        # Nostettu separation painoarvoa (1.5 -> 4.0) jotta yksiköt eivät mene päällekkäin
        # Nostettu obstacle painoarvoa (2.5 -> 3.0)
        # Hazard painoarvo (6.0) - Erittäin korkea prioriteetti, jotta ei juosta läpi
        final_dx = ndx + (sep_x * 4.0) + (obs_x * 3.0) + (haz_x * 6.0)
        final_dy = ndy + (sep_y * 4.0) + (obs_y * 3.0) + (haz_y * 6.0)
        
        l = math.hypot(final_dx, final_dy) or 1
        
        speed = self.unit.speed
        move_x = (final_dx / l) * speed
        move_y = (final_dy / l) * speed
        
        self.unit.check_wall_collision(move_x, move_y, obstacles)
        
        if abs(move_x) > 0.1:
            self.unit.facing_right = (move_x > 0)

    def _calculate_separation(self, all_units):
        sep_x, sep_y = 0, 0
        mx, my = self.unit.rect.center
        count = 0
        for u in all_units:
            if u is self.unit or u.is_dead: continue
            is_friend = (getattr(u, "team_color", None) == self.unit.team_color)
            ux, uy = u.rect.center
            d = math.hypot(ux - mx, uy - my)
            # Kasvatettu radiusta jotta väistävät aiemmin (35 -> 50)
            radius = 50 if is_friend else 30
            if d > 0 and d < radius:
                push = (radius - d) / radius
                sep_x += (mx - ux) / d * push
                sep_y += (my - uy) / d * push
                count += 1
            elif d == 0:
                sep_x += random.uniform(-1, 1)
                sep_y += random.uniform(-1, 1)
                count += 1
        if count > 0: return sep_x / count, sep_y / count
        return 0, 0

    def _calculate_obstacle_avoidance(self, obstacles):
        if not obstacles: return 0, 0
        av_x, av_y = 0, 0
        mx, my = self.unit.rect.center
        count = 0
        detection_radius = 80 # Kasvatettu sädettä (oli 60)
        
        for obj in obstacles:
            if obj is self.unit: continue # Älä väistä itseäsi
            r = getattr(obj, "rect", obj)
            # Nopea etäisyystarkistus
            if abs(r.centerx - mx) > detection_radius + r.w/2: continue
            if abs(r.centery - my) > detection_radius + r.h/2: continue
            
            # Lähin piste suorakulmiossa
            cl_x = max(r.left, min(mx, r.right))
            cl_y = max(r.top, min(my, r.bottom))
            dx = mx - cl_x
            dy = my - cl_y
            dist = math.hypot(dx, dy)
            
            if dist < detection_radius:
                force = (detection_radius - dist) / detection_radius
                if dist > 0:
                    av_x += (dx / dist) * force
                    av_y += (dy / dist) * force
                else:
                    av_x += random.uniform(-1, 1)
                    av_y += random.uniform(-1, 1)
                count += 1
        if count > 0: return av_x / count, av_y / count
        return 0, 0

    def _calculate_hazard_avoidance(self, hazards):
        """Laskee vektorin poispäin vaarallisista maapintapartikkeleista."""
        av_x, av_y = 0, 0
        mx, my = self.unit.rect.center
        count = 0
        detection_radius = 120 # Havaitsee vaarat ajoissa
        
        for h in hazards:
            # Tarkista onko vaarallinen (eri tiimi tai neutraali)
            h_team = getattr(h, "team", None)
            my_team = getattr(self.unit, "team_color", None)
            if h_team is not None and h_team == my_team:
                continue # Oma efekti, ei vaarallinen
            
            # Tarkista etäisyys (Bounding box check first)
            if abs(h.rect.centerx - mx) > detection_radius + h.rect.w: continue
            if abs(h.rect.centery - my) > detection_radius + h.rect.h: continue
            
            dx = mx - h.rect.centerx
            dy = my - h.rect.centery
            dist = math.hypot(dx, dy)
            
            # Vaara-alueen säde (arvioidaan rectistä)
            hazard_radius = max(h.rect.w, h.rect.h) / 2
            
            # Jos ollaan lähellä vaaraa
            if dist < detection_radius + hazard_radius:
                # Voimakas työntö poispäin. Mitä lähempänä, sitä kovempi voima.
                force = (detection_radius + hazard_radius - dist) / detection_radius
                if dist > 0:
                    av_x += (dx / dist) * force
                    av_y += (dy / dist) * force
                else:
                    av_x += random.uniform(-1, 1)
                    av_y += random.uniform(-1, 1)
                count += 1
                
        if count > 0: return av_x / count, av_y / count
        return 0, 0

    def _raycast(self, start, direction, length, obstacles):
        """Yksinkertainen säteenseuranta esteitä varten."""
        end_x = start[0] + direction[0] * length
        end_y = start[1] + direction[1] * length
        
        # Tarkistetaan leikkaako viiva mitään estettä
        for obs in obstacles:
            if obs is self.unit: continue # Älä törmää itseesi
            r = getattr(obs, "rect", obs)
            # Nopea AABB check ensin
            if r.clipline(start, (end_x, end_y)):
                return True
        return False

    def _check_stuck(self):
        cur_pos = self.unit.rect.topleft
        if self.unit.rect.x == self.last_pos[0] and self.unit.rect.y == self.last_pos[1]:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
        self.last_pos = cur_pos
        return self.stuck_counter > 20