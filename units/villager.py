import pygame
import os
import random
import math
from gladiator import Gladiator
from ai.villager_ai import VillagerAI
from settings import *
from items.tools.bucket import BucketEmpty
from items.tools.weak_pickaxe import WeakPickaxe
from items.tools.woodcutters_axe import WoodcuttersAxe

class Villager(Gladiator):
    def __init__(self, name, race, x, y, team_color=GREEN):
        # Varmistetaan että race on isolla alkukirjaimella (Goblin, Dwarf)
        race = race.capitalize()
        super().__init__(name, race, x, y, team_color)
        
        # Feet Hitbox
        self.rect = pygame.Rect(x, y + 32, 28, 16)
        
        # Statsit (Heikkoja siviilejä)
        self.max_hp = 30
        self.current_hp = 30
        self.strength = 2
        self.dexterity = 4
        self.speed = 1.1 # Hieman nopeampia pakenemaan
        self.cost = 10 # Halpoja (jos niitä voisi ostaa)
        
        # Inventory & Tools
        self.inventory = []
        self.inventory.append(WeakPickaxe())
        self.inventory.append(WoodcuttersAxe())
        self.inventory.append(BucketEmpty())
        
        # Grafiikat
        self.sprites = {}
        self._load_villager_sprites(race)
        
        # Aseta oletuskuva
        self.image = self.sprites.get("idle", pygame.Surface((32, 48)))
        if not self.sprites:
            # Fallback värit rodun mukaan
            if race == "Goblin": self.image.fill((100, 200, 50))
            elif race == "Dwarf": self.image.fill((150, 100, 50))
            else: self.image.fill((200, 200, 200))
            
        # Portrait
        if not getattr(self, "big_image", None):
            self.big_image = pygame.transform.smoothscale(self.image, (self.rect.w * 3, self.rect.h * 3))

        self.facing_right = True
        self.hurt_timer = 0
        # AI
        self.ai_controller = VillagerAI(self)
        # FIX: Initialize work_target if missing to prevent crash in AI logic
        if not hasattr(self.ai_controller, "work_target"):
            self.ai_controller.work_target = None
        self.dialogue_cooldown = 0

    def load_assets(self):
        return True

    def _load_villager_sprites(self, race):
        # Oletetaan polku: assets/races/{race}/villager_{state}.png
        # Esim: assets/races/goblin/villager_idle.png
        base_path = os.path.join("assets", "races", race.lower())
        
        states = ["idle", "run", "scared", "hurt", "working"]
        
        for state in states:
            # Kokeillaan paria eri nimeämistapaa varmuuden vuoksi
            filenames = [
                f"villager_{state}.png",
                f"{race.lower()}_villager_{state}.png",
                f"{state}.png" # Jos kansio on assets/races/goblin/villager/
            ]
            
            for fname in filenames:
                path = os.path.join(base_path, fname)
                if os.path.exists(path):
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        
                        # Tallenna korkearesoluutioinen kuva dialogia varten (Idle-tilasta)
                        if state == "idle":
                            self.big_image = img

                        self.sprites[state] = pygame.transform.smoothscale(img, (32, 48)) # Kapeampi ja korkeampi
                        break # Löytyi, siirry seuraavaan tilaan
                    except: pass
        
        # Ladataan työkalut ja esineet
        self.img_bucket_empty = self._load_extra("assets/gear/tools/bucket_empty.png")
        self.img_bucket_milk = self._load_extra("assets/gear/tools/bucket_milk.png")
        self.img_manure = self._load_extra("assets/tiles/farm/manure.png")
        self.img_bucket_water = self._load_extra("assets/gear/tools/bucket_water.png")
        self.img_meat = self._load_extra("assets/icons/materials/meat.png") # Tai geneerinen liha
        self.img_egg = self._load_extra("assets/icons/materials/egg.png")
        self.img_scrap = self._load_extra("assets/icons/materials/scrap_iron.png") # Tai joku muu romu-ikoni
        self.img_crate = self._load_extra("assets/tiles/muckford/barrel.png") # Käytetään tynnyriä/laatikkoa

    def _load_extra(self, path):
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(img, (24, 24))
            except: pass
        return None

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        dmg = super().take_damage(amount, damage_type, attacker, manager)
        if dmg > 0:
            self.hurt_timer = 15
        return dmg

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        
        if getattr(self, "hurt_timer", 0) > 0:
            self.hurt_timer -= 1

        if self.dialogue_cooldown > 0:
            self.dialogue_cooldown -= 1

        # Sprite State Machine (Villager specific)
        state = self.animation_state # AI asettaa tämän (idle, working, scared, run)
        
        # Jos otetaan vahinkoa, pakota hurt
        if self.animation_state == "hurt":
            state = "hurt"
        
        img = self.sprites.get(state)
        if not img: img = self.sprites.get("idle") # Fallback
        
        if img:
            self.image = img
            if not self.facing_right:
                self.image = pygame.transform.flip(self.image, True, False)

    def draw_on_screen(self, surface, offset=(0, 0)):
        super().draw_on_screen(surface, offset)
        
        if not self.ai_controller: return
        
        # Piirretään kannettavat esineet
        img_to_draw = None
        
        if getattr(self.ai_controller, "has_milk", False):
            img_to_draw = getattr(self, "img_bucket_milk", None)
        elif getattr(self.ai_controller, "has_water", False):
            img_to_draw = getattr(self, "img_bucket_water", None)
        elif getattr(self.ai_controller, "carrying_manure", False):
            img_to_draw = getattr(self, "img_manure", None)
        elif getattr(self.ai_controller, "carrying_meat", False):
            img_to_draw = getattr(self, "img_meat", None)
        elif getattr(self.ai_controller, "carrying_egg", False):
            img_to_draw = getattr(self, "img_egg", None)
        elif getattr(self.ai_controller, "carrying_scrap", False):
            img_to_draw = getattr(self, "img_scrap", None)
        elif getattr(self.ai_controller, "carrying_crate", False):
            img_to_draw = getattr(self, "img_crate", None)
        elif getattr(self.ai_controller, "state", "") in ["milking_approach", "milking"]:
            img_to_draw = getattr(self, "img_bucket_empty", None)
            
        if img_to_draw:
            x = self.rect.centerx - offset[0] + (12 if self.facing_right else -24)
            y = self.rect.centery - offset[1] + 5
            surface.blit(img_to_draw, (x, y))