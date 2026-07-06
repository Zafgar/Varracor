import pygame
import os
import random
from gladiator import Gladiator
from settings import *
from ai.tavern_ai import TavernAI
from sound_manager import sound_system

class MardaShant(Gladiator):
    def __init__(self, x, y):
        super().__init__("Marda Shant", "Human", x, y, team_color=(150, 50, 50))
        
        # Hitbox
        self.rect = pygame.Rect(x, y, 40, 60)
        
        # Stats (Vahva nainen)
        self.max_hp = 200
        self.current_hp = 200
        self.strength = 12
        self.dexterity = 8
        self.intelligence = 14
        self.speed = 1.0
        
        # Grafiikat
        self.sprites = {}
        self._load_sprites()
        
        # Oletuskuva
        self.image = self.sprites.get("idle", pygame.Surface((40, 60)))
        if not self.sprites:
            self.image.fill((100, 50, 50)) # Fallback punainen
            
        # Portrait UI:ta varten (käytetään idle-kuvaa jos muuta ei ole)
        if "idle" in self.sprites:
            self.big_image = pygame.transform.smoothscale(self.sprites["idle"], (120, 180))
        
        # AI (TavernAI pitää hänet tiskin takana tai touhuamassa)
        self.ai_controller = TavernAI(self)
        self.facing_right = False # Katsoo oletuksena vasemmalle (asiakkaisiin päin)

    def load_assets(self):
        return True

    def _load_sprites(self):
        base_path = "assets/races/human/mardashant"
        
        # Kartta: Pelimoottorin tila -> Tiedostonimi
        mapping = {
            "idle": "marda_idle.png",
            "run": "walking.png",
            "attack": "shouting.png", # Huutaa hyökätessään
            "work": "working.png",
            "laugh": "laughing.png"
        }
        
        for state, fname in mapping.items():
            path = os.path.join(base_path, fname)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    # Skaalataan hieman isommaksi (Marda on iso persoona)
                    target_h = 80
                    ratio = img.get_width() / img.get_height()
                    target_w = int(target_h * ratio)
                    
                    scaled = pygame.transform.smoothscale(img, (target_w, target_h))
                    self.sprites[state] = scaled
                except Exception as e:
                    print(f"[Marda] Error loading sprite {fname}: {e}")

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        
        # Animaatiotilan valinta
        state = self.animation_state
        
        # Erikoistilat AI:lta
        if getattr(self.ai_controller, "state", "") == "working":
            state = "work"
        
        # Valitse kuva
        img = self.sprites.get(state)
        if not img:
            # Fallbackit
            if state == "run": img = self.sprites.get("idle")
            elif state == "attack": img = self.sprites.get("idle")
            else: img = self.sprites.get("idle")
            
        if img:
            self.image = img
            # Käännä jos katsoo oikealle (oletuskuvat katsovat vasemmalle/eteen?)
            if not self.facing_right:
                self.image = pygame.transform.flip(self.image, True, False)

    def perform_attack(self, target, manager=None, damage_mult=1.0, range_override=None, target_pos=None):
        if super().perform_attack(target, manager, damage_mult, range_override, target_pos):
            if random.random() < 0.4:
                sound_system.play_sound('marda_shouting')
            return True
        return False

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        dmg = super().take_damage(amount, damage_type, attacker, manager)
        if dmg > 0 and random.random() < 0.4:
            sound_system.play_sound('marda_pissed')
        return dmg