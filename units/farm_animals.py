import pygame
import os
import random
import math
from gladiator import Gladiator
from ai.farm_animal_ai import FarmAnimalAI
from settings import *

class Cow(Gladiator):
    def __init__(self, x, y, team_color=(200, 200, 200)):
        super().__init__("Bessie", "Animal", x, y, team_color=team_color)
        
        self.rect = pygame.Rect(x, y, 64, 48)
        
        # Stats
        self.max_hp = 100
        self.current_hp = 100
        self.speed = 0.5
        self.milk_ready = False # Alussa EI ole maitoa (kerääntyy syömällä)
        self.farm_rect = None # Alue, jonka sisällä pysytään
        
        # AI
        self.ai_controller = FarmAnimalAI(self)
        
        # Grafiikat
        self.sprites = {}
        self._load_cow_sprites()
        self.image = self.sprites.get("idle", pygame.Surface((64, 48)))
        self.facing_right = True

    def load_assets(self):
        return True

    def _load_cow_sprites(self):
        base_path = "assets/races/animals"
        
        # Määritellään mitä tiedostoja etsitään kullekin tilalle
        # Kokeillaan useita vaihtoehtoja, jotta se löytää varmasti oikean
        search_map = {
            "idle": ["idle.png", "cow_1_idle.png", "cow_idle.png"],
            "walk": ["walk.png", "cow_1_walk.png", "cow_walk.png"],
            "eat":  ["cow_1_eat.png", "eat.png", "cow_eat.png"],
            "moo":  ["moo.png", "cow_1_moo.png", "cow_moo.png"]
        }
        
        for state, filenames in search_map.items():
            for fname in filenames:
                path = os.path.join(base_path, fname)
                if os.path.exists(path):
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        self.sprites[state] = pygame.transform.smoothscale(img, (64, 48))
                        print(f"[Cow] Loaded {state}: {fname}")
                        break # Löytyi, siirry seuraavaan tilaan
                    except Exception: pass
        
        if not self.sprites:
            s = pygame.Surface((64, 48))
            s.fill((200, 200, 200)) # Harmaa laatikko
            self.sprites["idle"] = s

    def update(self, obstacles=None, manager=None):
        # Päivitä AI ja liike
        if self.ai_controller:
            self.ai_controller.execute_ai(None, obstacles, manager)
        
        # Animaatio
        state = self.animation_state # AI asettaa: idle, walk, eat, moo
        img = self.sprites.get(state, self.sprites.get("idle"))
        
        if img:
            self.image = img
            if not self.facing_right:
                self.image = pygame.transform.flip(self.image, True, False)

    def draw_on_screen(self, surface, offset=(0, 0)):
        # Kutsu peruspiirtoa (GladiatorRenderer)
        super().draw_on_screen(surface, offset)
        
        # Piirrä maito-indikaattori staattisesti jos valmis (ei vilku)
        if self.milk_ready:
            x = self.rect.centerx - offset[0]
            y = self.rect.top - 15 - offset[1]
            
            # Kelluva liike
            bob = int(math.sin(pygame.time.get_ticks() * 0.005) * 3)
            
            # Valkoinen pisara sinisellä reunalla
            pygame.draw.circle(surface, (200, 200, 255), (x, y + bob), 6)
            pygame.draw.circle(surface, (255, 255, 255), (x, y + bob), 4)

class Chicken(Gladiator):
    def __init__(self, x, y, team_color=(200, 200, 200)):
        super().__init__("Cluck", "Animal", x, y, team_color=team_color)
        self.rect = pygame.Rect(x, y, 24, 24)
        self.max_hp = 10
        self.current_hp = 10
        self.speed = 0.8
        
        self.ai_controller = FarmAnimalAI(self)
        self.ai_controller.is_chicken = True # Flag AI:lle

        # Poikanen: pienempi, nopeampi, kasvaa aikuiseksi ajan kanssa
        self.is_baby = False
        self.grow_timer = 0

        self.sprites = {}
        self._load_sprites()
        self.image = self.sprites.get("idle", pygame.Surface((24, 24)))
        if not self.sprites:
            self.image.fill((200, 200, 200))

    def make_baby(self):
        """Muuttaa kanan vastakuoriutuneeksi poikaseksi."""
        self.is_baby = True
        self.grow_timer = 60 * 90  # ~1.5 min aikuiseksi
        c = self.rect.center
        self.rect = pygame.Rect(0, 0, 12, 12)
        self.rect.center = c
        self.max_hp = 5
        self.current_hp = 5
        self.speed = 1.0
        # Poikanen ei muni ennen aikuistumista
        self.ai_controller.egg_timer = 999999
        # Pieni keltainen untuvikko (procedural)
        s = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 230, 120), (6, 7), 5)
        pygame.draw.circle(s, (255, 200, 80), (9, 5), 2)
        self.image = s
        self._baby_image = s

    def _grow_up(self):
        self.is_baby = False
        c = self.rect.center
        self.rect = pygame.Rect(0, 0, 24, 24)
        self.rect.center = c
        self.max_hp = 10
        self.current_hp = 10
        self.speed = 0.8
        self.ai_controller.egg_timer = 3000 + int(3000 * (0.5 + 0.5 * (id(self) % 100) / 100))
        self.image = self.sprites.get("idle", pygame.Surface((24, 24)))
        if not self.sprites:
            self.image.fill((200, 200, 200))

    def _load_sprites(self):
        # Placeholder lataus, oletetaan että kuvat on assets/races/animals/chicken_*.png
        # Jos ei ole, käytetään valkoista laatikkoa
        pass

    def update(self, obstacles=None, manager=None):
        if self.ai_controller:
            self.ai_controller.execute_ai(None, obstacles, manager)

        # Poikanen kasvaa aikuiseksi
        if self.is_baby:
            self.grow_timer -= 1
            if self.grow_timer <= 0:
                self._grow_up()
                if manager:
                    manager.vfx.show_damage(self.rect.centerx, self.rect.top - 10,
                                            "*cluck!*", color=(255, 240, 150))

        # Yksinkertainen kääntö
        if not self.facing_right:
            pass # Käännä kuva jos on sprite
