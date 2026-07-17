import pygame
import os
import random
from settings import *
from gladiator import Gladiator
from ai.undead_ai import UndeadAI
from sound_manager import sound_system

class UndeadZombie(Gladiator):
    def __init__(self, name, x, y, team_color):
        super().__init__(name, "Undead", x, y, team_color)
        
        # Stats (Hidas, tankki)
        self.max_hp = 120
        self.current_hp = 120
        self.strength = 12
        self.dexterity = 2
        self.defense = 2
        # Hidas laahustaja - vaarallinen vain laumassa/ahtaissa paikoissa
        self.speed = self.walk_speed = 1.7
        
        self.attack_range = 35
        self.ai_controller = UndeadAI(self)
        
        # Grafiikat
        self.show_main_hand = False # Piilotetaan nyrkit/aseet
        self.rect = pygame.Rect(x, y, 48, 64)
        self.sprites = {}
        self.hurt_timer = 0
        self.last_pos = self.rect.topleft
        
        self._load_sprites()
        self.image = self.sprites.get("idle", pygame.Surface((48, 64)))
        # Portrait UI:ta varten
        self.big_image = pygame.transform.smoothscale(self.image, (self.rect.w * 3, self.rect.h * 3))

    def load_assets(self):
        return True

    def _load_sprites(self):
        # Ladataan assets/races/undead/zombie_*.png
        base_path = "assets/races/undead/zombie/zombie"
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
        
        # Fallback: koodipiirretty siluetti PUUTTUVIIN tiloihin
        from units.placeholder_sprites import humanoid_frames
        placeholder = humanoid_frames(
            (target_w, target_h),
            body=(96, 128, 84),     # mädäntynyt vihreä
            accent=(62, 88, 58),
            eye=(224, 220, 120),
            weapon="none",
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

    def get_loot(self):
        """Generoi crafting-materiaaleja (Crypt-teema) kun zombie kuolee."""
        # 10 erilaista crafting-materiaalia
        materials = [
            "Bone Shard", "Rotten Flesh", "Grave Dust", "Crypt Moss", 
            "Rusty Scrap", "Spirit Essence", "Zombie Tooth", "Cursed Fabric", 
            "Necrotic Goo", "Ancient Bone"
        ]
        
        loot = []
        # Valitaan satunnainen materiaali
        item_name = random.choice(materials)
        # Arvotaan määrä 0-10
        amount = random.randint(0, 10)
        
        if amount > 0:
            loot.append({"name": item_name, "amount": amount, "type": "material"})
        return loot

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