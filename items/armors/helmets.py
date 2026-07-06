import pygame
from items.base_item import Armor

class Helmet(Armor):
    def __init__(self):
        super().__init__()
        self.slot_type = "head"

class LeatherCap(Helmet):
    def __init__(self):
        super().__init__()
        self.name = "Leather Cap"
        self.defense = 1
        self.cost = 40
        self.rarity = "Common"
        self.description = "Simple leather protection."

class IronHelm(Helmet):
    def __init__(self):
        super().__init__()
        self.name = "Iron Helm"
        self.defense = 3
        self.cost = 120
        self.rarity = "Rare"
        self.description = "Sturdy iron helmet."