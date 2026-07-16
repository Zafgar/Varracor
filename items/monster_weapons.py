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

class NaturalWeapon(Weapon):
    """Monsterin luonnollinen ase (kynnet/leuat/raajat) - pelitesti 28.

    Klassiset Gladiator-bossit löivät nyrkeillä: fists-perhekerroin
    (x0.6) + tier-panssarin flat-defense söi osumat 1-4 %:n uhkaksi.
    Luonnollinen ase mitoitetaan alueen tier-panssaria vasten.
    weapon_group jätetään tyhjäksi -> ei proficiency-sakkoa eikä
    fists-nerfiä (weapon_feel-oletukset)."""

    def __init__(self, name="Claws", damage=20, attack_range=45,
                 str_scale=0.8, speed_bonus=0.0):
        super().__init__()
        self.name = name
        self.rarity = "Common"
        self.type = "melee"
        self.slot_type = "main_hand"
        self.damage = int(damage)
        self.attack_range = int(attack_range)
        self.speed_bonus = float(speed_bonus)
        self.scaling = {"STR": float(str_scale)}
        self.weapon_group = ""   # ei sakkoja, ei perhekertoimia
        self.description = "Natural weaponry - fangs, claws or worse."
