import random
import math
import pygame
from ai.base_ai import BaseAI
from assets.tiles.farm_objects import GrassPatch, Manure, Egg
from sound_manager import sound_system

class FarmAnimalAI(BaseAI):
    def __init__(self, unit):
        super().__init__(unit)
        self.state = "idle" # idle, wander, find_food, eating
        self.timer = 0
        self.target_grass = None
        self.digest_timer = 0
        self.is_chicken = False
        self.egg_timer = random.randint(1000, 3000)

    def execute_ai(self, all_units, obstacles, manager=None):
        if self.unit.is_dead: return

        self.timer -= 1
        self.digest_timer -= 1
        
        # Kanan muninta
        if self.is_chicken:
            self.egg_timer -= 1
            if self.egg_timer <= 0:
                self._lay_egg(manager)
        
        # Kakkauslogiikka
        if self.digest_timer <= 0 and random.random() < 0.01:
            self._poop(manager)
            self.digest_timer = random.randint(1200, 2400) # Uusi kakka 20-40s päästä

        # Tilakone
        if self.state == "idle":
            self.unit.animation_state = "idle"
            if self.timer <= 0:
                # Arvo uusi toiminto: Kävele, Syö tai Moo
                r = random.random()
                if r < 0.4:
                    self._start_wander()
                elif r < 0.7:
                    self._find_food(manager)
                elif r < 0.9:
                    self.state = "moo"
                    self.timer = 60
                    self.unit.animation_state = "moo"
                    sound_system.play_sound("moo")
                else:
                    self.timer = random.randint(60, 180)

        elif self.state == "moo":
            if self.timer <= 0:
                self.state = "idle"
                self.timer = 30

        elif self.state == "wander":
            self.unit.animation_state = "walk"
            if self.timer <= 0 or self._has_reached_target():
                self.state = "idle"
                self.timer = random.randint(30, 90)
            else:
                self._move_to_target(obstacles)

        elif self.state == "find_food":
            if self.target_grass and not self.target_grass.is_eaten:
                self.unit.animation_state = "walk"
                dist = math.hypot(self.target_grass.rect.centerx - self.unit.rect.centerx,
                                  self.target_grass.rect.centery - self.unit.rect.centery)
                if dist < 60: # Kasvatettu etäisyyttä (koska lehmä on iso ja ruoho pieni)
                    self.state = "eating"
                    self.timer = 120 # Syö 2 sekuntia
                    self.unit.animation_state = "eat"
                else:
                    self.target_pos = self.target_grass.rect.center
                    self._move_to_target(obstacles)
            else:
                # Ruoho katosi tai syötiin
                self.state = "idle"

        elif self.state == "eating":
            self.unit.animation_state = "eat"
            if self.timer <= 0:
                if self.target_grass:
                    if self.target_grass.eat():
                        self.unit.milk_ready = True # Maito valmis syömisen jälkeen
                        self.digest_timer = max(100, self.digest_timer - 500) # Kakka tulee nopeammin
                self.state = "idle"
                self.timer = 60

    def _start_wander(self):
        self.state = "wander"
        self.timer = random.randint(60, 180)
        
        # Jos lehmällä on määritelty laidunalue, pysy siellä
        if getattr(self.unit, "farm_rect", None):
            fr = self.unit.farm_rect
            rx = random.randint(fr.left + 20, fr.right - 20)
            ry = random.randint(fr.top + 20, fr.bottom - 20)
            self.target_pos = (rx, ry)
        else:
            rx = self.unit.rect.x + random.randint(-100, 100)
            ry = self.unit.rect.y + random.randint(-100, 100)
            self.target_pos = (rx, ry)

    def _find_food(self, manager):
        if not manager or not manager.current_arena: 
            self.state = "idle"
            return

        # Etsi lähin syömätön ruoho
        best_grass = None
        min_dist = 500 # Näköetäisyys
        
        # Oletetaan että ruohot ovat floor_props listassa
        candidates = [p for p in getattr(manager.current_arena, "floor_props", []) if isinstance(p, GrassPatch) and not p.is_eaten]
        
        for g in candidates:
            d = math.hypot(g.rect.centerx - self.unit.rect.centerx, g.rect.centery - self.unit.rect.centery)
            if d < min_dist and d < 800: # Kasvatettu hakusädettä (oli 500)
                min_dist = d
                best_grass = g
        
        if best_grass:
            self.target_grass = best_grass
            self.state = "find_food"
        else:
            self.state = "idle"

    def _poop(self, manager):
        if manager:
            # Rajoita lannan määrää kartalla (Max 30)
            manures = [p for p in manager.current_arena.props if isinstance(p, Manure)]
            if len(manures) >= 30:
                # Poista vanhin (ensimmäinen listassa)
                oldest = manures[0]
                if oldest in manager.current_arena.props:
                    manager.current_arena.props.remove(oldest)
                if oldest in manager.all_units:
                    manager.all_units.remove(oldest)

            # Luo lantaa pepun kohdalle
            mx = self.unit.rect.x if self.unit.facing_right else self.unit.rect.right
            my = self.unit.rect.bottom - 10
            manure = Manure(mx, my)
            manager.current_arena.props.append(manure)
            # Lisää myös all_unitsiin jotta interaction toimii (GameManagerin logiikka)
            manager.all_units.add(manure)

    def _lay_egg(self, manager):
        if manager:
            egg = Egg(self.unit.rect.centerx, self.unit.rect.centery)
            manager.current_arena.props.append(egg)
            manager.all_units.add(egg)
            self.egg_timer = random.randint(3000, 6000) # Uusi muna

    def _has_reached_target(self):
        if not self.target_pos: return True
        dx = self.target_pos[0] - self.unit.rect.centerx
        dy = self.target_pos[1] - self.unit.rect.centery
        return math.hypot(dx, dy) < 10

    def _move_to_target(self, obstacles):
        if not self.target_pos: return
        
        tx, ty = self.target_pos
        dx = tx - self.unit.rect.centerx
        dy = ty - self.unit.rect.centery
        dist = math.hypot(dx, dy)
        
        if dist > 0:
            speed = self.unit.speed
            move_x = (dx / dist) * speed
            move_y = (dy / dist) * speed
            
            self.unit.facing_right = move_x > 0
            
            # KORJAUS: Käytetään check_wall_collision jos mahdollista (tukee alle 1.0 nopeutta)
            if hasattr(self.unit, "check_wall_collision"):
                self.unit.check_wall_collision(move_x, move_y, obstacles)
            else:
                # Fallback (tämä ei toimi hyvin pienillä nopeuksilla)
                self.unit.rect.x += int(move_x) if abs(move_x) >= 1 else 0
                self.unit.rect.y += int(move_y) if abs(move_y) >= 1 else 0
                
                if obstacles:
                    for obs in obstacles:
                        if self.unit.rect.colliderect(obs.rect):
                            self.unit.rect.x -= int(move_x)
                            self.unit.rect.y -= int(move_y)
                            self.state = "idle"
                            break
