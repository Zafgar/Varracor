"""Harvesting tools used by the Muckford farming expansion.

The item registry discovers these classes automatically.  All three tools use
one proficiency group (``harvest_tool``), while ``tool_tier`` controls which
crops can be harvested and how much high-quality produce can be found.
"""

import math
import os

import pygame

from items.base_item import Weapon
from sound_manager import sound_system


class _HarvestTool(Weapon):
    display_name = "Harvest Tool"
    rarity_name = "Common"
    price = 40
    tier = 1
    damage_value = 3
    description_text = "A simple tool for harvesting crops."
    image_path = ""

    def __init__(self):
        super().__init__()
        self.name = self.display_name
        self.rarity = self.rarity_name
        self.cost = self.price
        self.description = self.description_text
        self.type = "melee"
        self.slot_type = "main_hand"
        self.weapon_group = "harvest_tool"
        self.tool_type = "harvest"
        self.tool_tier = self.tier
        self.damage = self.damage_value
        self.attack_range = 50
        self.speed_bonus = 0.0
        self.scaling = {"DEX": 0.35, "STR": 0.2}
        self.image = None
        self._load_image()

    def _load_image(self):
        if not self.image_path or not os.path.exists(self.image_path):
            return
        try:
            raw = pygame.image.load(self.image_path)
            if pygame.display.get_surface():
                raw = raw.convert_alpha()
            self.image = pygame.transform.smoothscale(raw, (24, 42))
        except Exception:
            self.image = None

    def draw_card_icon(self, surface, x, y, size):
        if self.image:
            ratio = self.image.get_width() / max(1, self.image.get_height())
            h = size
            w = max(1, int(h * ratio))
            scaled = pygame.transform.smoothscale(self.image, (w, h))
            surface.blit(scaled, (x + (size - w) // 2, y))
            return

        # Procedural sickle fallback: wooden grip and a curved steel blade.
        grip = (118, 77, 42)
        blade = (190, 198, 205)
        pygame.draw.line(surface, grip,
                         (x + int(size * 0.35), y + int(size * 0.82)),
                         (x + int(size * 0.55), y + int(size * 0.30)),
                         max(3, size // 12))
        arc = pygame.Rect(x + int(size * 0.35), y + int(size * 0.08),
                          int(size * 0.48), int(size * 0.48))
        pygame.draw.arc(surface, blade, arc, math.radians(195), math.radians(350),
                        max(3, size // 14))

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown):
        hand_x = unit_rect.centerx + (7 if facing_right else -7)
        hand_y = unit_rect.centery + 5
        swing = 0
        if attack_cooldown > 0:
            progress = max(0.0, 1.0 - attack_cooldown / 60.0)
            swing = math.sin(progress * math.tau) * 70
        base = -35 if facing_right else 35
        angle = base + (swing if facing_right else -swing)

        if self.image:
            img = self.image if facing_right else pygame.transform.flip(self.image, True, False)
            img = pygame.transform.rotate(img, angle)
            rect = img.get_rect(center=(hand_x, hand_y - 8))
            surface.blit(img, rect)
            return

        # Small procedural fallback in the character's hand.
        length = 28
        rad = math.radians(angle)
        end_x = hand_x + math.cos(rad) * length
        end_y = hand_y - math.sin(rad) * length
        pygame.draw.line(surface, (118, 77, 42), (hand_x, hand_y), (end_x, end_y), 3)
        pygame.draw.arc(surface, (195, 202, 210),
                        (int(end_x) - 9, int(end_y) - 9, 18, 18),
                        math.radians(180), math.radians(350), 3)

    def on_attack_start(self, attacker, target, manager):
        sound_system.play_sound("attack_melee")


class CrudeHarvestSickle(_HarvestTool):
    display_name = "Crude Harvest Sickle"
    rarity_name = "Common"
    price = 35
    tier = 1
    damage_value = 3
    description_text = "A rough sickle for Tier 1 crops. Requires Harvesting I."
    image_path = "assets/gear/tools/crude_harvest_sickle.png"


class IronHarvestSickle(_HarvestTool):
    display_name = "Iron Harvest Sickle"
    rarity_name = "Rare"
    price = 140
    tier = 2
    damage_value = 6
    description_text = "A balanced iron sickle for Tier 2 crops and better yields."
    image_path = "assets/gear/tools/iron_harvest_sickle.png"


class GuildHarvestScythe(_HarvestTool):
    display_name = "Guild Harvest Scythe"
    rarity_name = "Epic"
    price = 420
    tier = 3
    damage_value = 10
    description_text = "A guild-made scythe for master harvesters and prime produce."
    image_path = "assets/gear/tools/guild_harvest_scythe.png"
