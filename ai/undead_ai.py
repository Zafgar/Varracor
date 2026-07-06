import pygame
import math
import random

class UndeadAI:
    def __init__(self, unit):
        self.unit = unit
        self.current_target = None
        self.reaction_timer = 0
        self.rethink_timer = 0
        
        # Stuck detection
        self.last_pos = (0, 0)
        self.stuck_counter = 0
        
        # Escape logic (kun jäädään jumiin)
        self.escape_timer = 0
        self.escape_direction = pygame.math.Vector2(0, 0)
        self.idle_timer = 0

    def execute_ai(self, all_units, obstacles=None, manager=None):
        if self.unit.is_dead: return

        # 0. Idle/Stuck behavior (Huojuminen paikallaan)
        if self.idle_timer > 0:
            self.idle_timer -= 1
            self.unit.animation_state = "idle"
            return

        # 1. Etsi kohde (Tarkistetaan useammin, jotta vaihdetaan lähimpään)
        self.rethink_timer -= 1
        if self.rethink_timer <= 0 or not self._is_valid_target(self.current_target):
            self.current_target = self.find_closest_enemy(all_units)
            self.rethink_timer = 15 # 0.25s välein uusi arvio
        
        target = self.current_target
        if not target:
            return

        # 2. Laske etäisyys
        dx = target.rect.centerx - self.unit.rect.centerx
        dy = target.rect.centery - self.unit.rect.centery
        dist = math.hypot(dx, dy)
        
        attack_range = getattr(self.unit, "attack_range", 40)
        is_archer = "Archer" in getattr(self.unit, "name", "")
        melee_range = 50

        # 3. Hyökkäys
        if dist <= attack_range and getattr(self.unit, "attack_cooldown", 0) <= 0:
            if is_archer and dist < melee_range:
                if hasattr(self.unit, "perform_attack"):
                    try:
                        self.unit.perform_attack(target, manager, force_melee=True)
                    except TypeError:
                        self.unit.perform_attack(target, manager)
            else:
                if hasattr(self.unit, "perform_attack"):
                    self.unit.perform_attack(target, manager)
        
        # 4. Liikkuminen
        move_threshold = attack_range * 0.8 if is_archer else (attack_range - 5)
        
        if dist > move_threshold:
            speed = self.unit.speed
            
            if dist > 0:
                ndx = dx / dist
                ndy = dy / dist
            else:
                ndx, ndy = 0, 0
            
            # Escape Logic (Jos ollaan jumissa, peräännytään/kierretään hetki)
            if self.escape_timer > 0:
                self.escape_timer -= 1
                ndx, ndy = self.escape_direction.x, self.escape_direction.y
            
            elif self._check_stuck():
                # Jos jumissa pitkään (> 40 framea), huojutaan paikallaan hetki
                if self.stuck_counter > 40:
                    self.idle_timer = random.randint(40, 90) # 0.7s - 1.5s tauko
                    self.stuck_counter = 0
                    return

                # Muuten yritetään kiertää
                self.escape_timer = 30
                to_target = pygame.math.Vector2(dx, dy).normalize() if dist > 0 else pygame.math.Vector2(1, 0)
                
                if random.random() < 0.5:
                    perp = pygame.math.Vector2(-to_target.y, to_target.x)
                else:
                    perp = pygame.math.Vector2(to_target.y, -to_target.x)
                    
                back = -to_target
                self.escape_direction = (perp * 0.6 + back * 0.4).normalize()
                ndx, ndy = self.escape_direction.x, self.escape_direction.y
            
            # Separation
            sep_x, sep_y = self._calculate_separation(all_units)
            
            # Obstacle Avoidance
            obs_x, obs_y = self._calculate_obstacle_avoidance(obstacles)
            
            final_dx = ndx + (sep_x * 2.5) + (obs_x * 3.0)
            final_dy = ndy + (sep_y * 2.5) + (obs_y * 3.0)
            
            l = math.hypot(final_dx, final_dy) or 1
            move_x = (final_dx / l) * speed
            move_y = (final_dy / l) * speed
            
            self.unit.check_wall_collision(move_x, move_y, obstacles)
            
            if abs(move_x) > 0.1:
                self.unit.facing_right = (move_x > 0)

    def _is_valid_target(self, target):
        return target and not getattr(target, "is_dead", True) and not getattr(target, "is_structure", False)

    def find_closest_enemy(self, all_units):
        closest = None
        min_dist = float('inf')
        my_team = getattr(self.unit, "team_color", None)
        mx, my = self.unit.rect.center
        
        for other in all_units:
            if other == self.unit or getattr(other, "is_dead", False): continue
            if getattr(other, "is_structure", False): continue
            if my_team and getattr(other, "team_color", None) == my_team: continue
            
            d2 = (other.rect.centerx - mx)**2 + (other.rect.centery - my)**2
            if d2 < min_dist:
                min_dist = d2
                closest = other
        return closest

    def _calculate_separation(self, all_units):
        sep_x, sep_y = 0, 0
        mx, my = self.unit.rect.center
        count = 0
        
        for u in all_units:
            if u is self.unit or u.is_dead: continue
            if getattr(u, "team_color", None) == self.unit.team_color:
                d = math.hypot(u.rect.centerx - mx, u.rect.centery - my)
                if d > 0 and d < 30:
                    push = (30 - d) / 30
                    sep_x += (mx - u.rect.centerx) / d * push
                    sep_y += (my - u.rect.centery) / d * push
                    count += 1
        
        if count > 0:
            sep_x /= count
            sep_y /= count
            
        return sep_x, sep_y

    def _calculate_obstacle_avoidance(self, obstacles):
        if not obstacles: return 0, 0
        av_x, av_y = 0, 0
        mx, my = self.unit.rect.center
        count = 0
        detection_radius = 60 
        
        for obj in obstacles:
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

    def _check_stuck(self):
        cur_pos = self.unit.rect.topleft
        if self.unit.rect.x == self.last_pos[0] and self.unit.rect.y == self.last_pos[1]:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
        self.last_pos = cur_pos
        # Jos paikallaan > 15 framea (0.25s), ollaan jumissa
        return self.stuck_counter > 15