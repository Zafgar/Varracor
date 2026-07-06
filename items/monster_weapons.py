import pygame
from items.base_item import Weapon

class ZombieClaws(Weapon):
    def __init__(self):
        super().__init__()
        self.name = "Rotting Claws"
        self.rarity = "Common"
        self.type = "melee"
        self.slot_type = "main_hand"
        self.damage = 9
        self.attack_range = 35
        self.speed_bonus = 0.0
        self.description = "Filthy claws capable of tearing flesh."
        self.weapon_group = "fists"