import pygame
import os
from settings import *
from gladiator import Gladiator
from ai.undead_ai import UndeadAI
from sound_manager import sound_system
from items.bows.weak_bow import WeakBow

class UndeadSkeletonArcher(Gladiator):
    def __init__(self, name, x, y, team_color):
        super().__init__(name, "Undead", x, y, team_color)
        
        # Stats (Ranged)
        self.max_hp = 50
        self.current_hp = 50
        self.strength = 6
        self.dexterity = 10
        self.speed = 1.8
        self.defense = 0
        
        self.attack_range = 300 # Ranged
        self.is_archer = True   # AI tunnistaa tästä
        self.ai_controller = UndeadAI(self)
        
        # Grafiikat
        self.show_main_hand = False # Piilotetaan varusteet, koska spritet sisältävät jo jousen
        self.rect = pygame.Rect(x, y, 40, 64)
        self.sprites = {}
        self.hurt_timer = 0
        self.last_pos = self.rect.topleft
        
        self._load_sprites()
        self.image = self.sprites.get("idle", pygame.Surface((40, 64)))
        # Portrait UI:ta varten
        self.big_image = pygame.transform.smoothscale(self.image, (self.rect.w * 3, self.rect.h * 3))

        # Equip Weapon
        self.equip_item(WeakBow())

    def load_assets(self):
        return True

    def calculate_final_stats(self):
        """Varmistetaan että luuranko osaa käyttää jousta ilman skill tree -taitoja."""
        super().calculate_final_stats()
        self.weapon_masteries.add("bow")

    def _load_sprites(self):
        # Ladataan assets/races/undead/skeleton_archer_*.png
        base_path = "assets/races/undead/skeleton_archer/skeleton_archer"
        # Huom: attack on melee-isku, aim+shoot on jousi
        actions = ["idle", "run", "attack", "hit", "aim", "shoot"]
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
        
        if not self.sprites:
            s = pygame.Surface((target_w, target_h))
            s.fill((180, 180, 160))
            self.sprites["idle"] = s

    def perform_attack(self, target, manager=None, force_melee=False):
        """
        Ylikirjoitetaan hyökkäys, jotta voidaan tukea melee-iskua jousimiehellä.
        """
        if self.attack_cooldown > 0: return False
        
        if force_melee:
            # Lähitaistelu (käsin)
            self.attack_cooldown = 45
            sound_system.play_sound('attack_melee')
            # Tee vahinkoa
            dmg = self.strength
            if target:
                target.take_damage(dmg, "Physical", attacker=self, manager=manager)
            # Aseta tila melee-animaatiota varten (käsitellään update:ssa)
            self._last_attack_type = "melee"
            return True
        else:
            # Normaali ranged (Gladiator hoitaa nuolen luonnin jos ase on jousi)
            # Mutta varmistetaan ääni ja animaatiotila
            self._last_attack_type = "ranged"
            return super().perform_attack(target, manager)

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        dmg = super().take_damage(amount, damage_type, attacker, manager)
        if dmg > 0:
            self.hurt_timer = 15
        return dmg

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        if self.is_dead: return

        state = "idle"
        
        if self.hurt_timer > 0:
            self.hurt_timer -= 1
            state = "hit"
        elif self.attack_cooldown > 0:
            # Hyökkäysanimaatiot
            if getattr(self, "_last_attack_type", "ranged") == "melee":
                # Melee isku
                state = "attack"
            else:
                # Ranged: Aim -> Shoot
                # Jos cooldown on alussa (iso luku), tähtää. Lopussa ammu.
                if self.attack_cooldown > 20:
                    state = "aim"
                else:
                    state = "shoot"
        elif self.rect.topleft != self.last_pos:
            state = "run"
        
        # Päivitä kuva
        if state in self.sprites:
            self.image = self.sprites[state]

        self.last_pos = self.rect.topleft