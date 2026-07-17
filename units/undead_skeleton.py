import pygame
import os
import random
from settings import *
from gladiator import Gladiator
from ai.undead_ai import UndeadAI
from sound_manager import sound_system
from items.swords.weak_sword import WeakSword

class UndeadSkeleton(Gladiator):
    def __init__(self, name, x, y, team_color):
        super().__init__(name, "Undead", x, y, team_color)
        
        # Stats (Nopea, heikko)
        self.max_hp = 60
        self.current_hp = 60
        self.strength = 8
        self.dexterity = 12
        self.defense = 0

        self.attack_range = 40
        self.ai_controller = UndeadAI(self)
        
        # Grafiikat
        self.show_main_hand = False # Piilotetaan nyrkit/aseet, käytetään vain spritejä
        self.rect = pygame.Rect(x, y, 40, 64)
        self.sprites = {}
        self.hurt_timer = 0
        self.last_pos = self.rect.topleft
        
        self._load_sprites()
        self.image = self.sprites.get("idle", pygame.Surface((40, 64)))
        # Portrait UI:ta varten
        self.big_image = pygame.transform.smoothscale(self.image, (self.rect.w * 3, self.rect.h * 3))

        # Annetaan luurangolle miekka (jotta se pitää ääntä ja tekee vahinkoa)
        self.equip_item(WeakSword())

        # Nopea rivivihollinen. Asetetaan equipin JÄLKEEN, koska
        # calculate_final_stats nollaisi walk_speedin dex-kaavaan.
        self.speed = self.walk_speed = 2.5

    def load_assets(self):
        return True

    def calculate_final_stats(self):
        """Varmistetaan että luuranko osaa käyttää miekkaa."""
        super().calculate_final_stats()
        self.weapon_masteries.add("sword")

    def _load_sprites(self):
        # Ladataan assets/races/undead/skeleton_*.png
        base_path = "assets/races/undead/skeleton/skeleton"
        actions = ["idle", "run", "attack", "hit"]
        target_w, target_h = self.rect.w, self.rect.h
        
        for act in actions:
            path = f"{base_path}_{act}.png"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    # Käytetään smoothscalea paremman laadun saamiseksi
                    scaled = pygame.transform.smoothscale(img, (target_w, target_h))
                    self.sprites[act] = scaled
                except Exception: pass
        
        # Fallback: koodipiirretty siluetti PUUTTUVIIN tiloihin (oikeat
        # spritet ohittavat placeholderit automaattisesti kun ne lisätään)
        from units.placeholder_sprites import humanoid_frames
        placeholder = humanoid_frames(
            (target_w, target_h),
            body=(214, 208, 186),   # luunvalkoinen
            accent=(126, 118, 100),
            eye=(205, 70, 60),      # hehkuvat silmäkuopat
            weapon="sword",
        )
        for state, surf in placeholder.items():
            self.sprites.setdefault(state, surf)

    def perform_attack(self, target, manager=None):
        """Ylikirjoitetaan hyökkäys käyttämään omaa raapaisua."""
        if self.attack_cooldown > 0: return False
        self.attack_cooldown = self.attack_speed
        if random.random() < 0.4:
            sound_system.play_sound(random.choice(['undead_attack_1', 'undead_attack_2', 'undead_attack_3', 'undead_attack_4']))
        if target:
            target.take_damage(self.strength, "Physical", attacker=self, manager=manager)
        return True

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        dmg = super().take_damage(amount, damage_type, attacker, manager)
        if dmg > 0:
            self.hurt_timer = 15
        return dmg

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        if self.is_dead: return

        # Animaatiotila
        state = "idle"
        
        if self.hurt_timer > 0:
            self.hurt_timer -= 1
            state = "hit"
        elif self.attack_cooldown > 30:
            state = "attack"
        elif self.rect.topleft != self.last_pos:
            state = "run"
        
        # Päivitä kuva
        if state in self.sprites:
            self.image = self.sprites[state]

        self.last_pos = self.rect.topleft