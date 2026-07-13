# items/tools/fishing_rod.py
import os

import pygame

from items.base_item import Weapon


class FishingRod(Weapon):
    """Yksinkertainen suokalastusvapa. tool_type 'fishing' avaa kalastuksen
    laiturilla (systems/fishing.py tunnistaa vavan kädestä tai repusta)."""

    def __init__(self):
        super().__init__()
        self.name = "Fishing Rod"
        self.rarity = "Common"
        self.cost = 18
        self.description = "Bent reed, waxed line, rusty hook. The marsh provides."

        self.type = "melee"
        self.slot_type = "main_hand"
        self.weapon_group = "fishing_rod"

        self.damage = 1
        self.attack_range = 44
        self.scaling = {"DEX": 0.2}

        self.tool_type = "fishing"
        self.tool_tier = 1

        self.image = None
        self._load_image()

    def _load_image(self):
        path = "assets/gear/tools/fishing_rod.png"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (16, 52))
            except Exception:
                self.image = None

    def draw_card_icon(self, surface, x, y, size):
        if self.image:
            ratio = self.image.get_width() / self.image.get_height()
            new_h = size
            new_w = max(1, int(new_h * ratio))
            scaled = pygame.transform.smoothscale(self.image, (new_w, new_h))
            surface.blit(scaled, (x + (size - new_w) // 2, y))
        else:
            # Koodigrafiikka: vapa + siima + koukku
            pygame.draw.line(surface, (122, 88, 54),
                             (x + size * 0.2, y + size * 0.9),
                             (x + size * 0.75, y + size * 0.12), 3)
            pygame.draw.line(surface, (200, 200, 205),
                             (x + size * 0.75, y + size * 0.12),
                             (x + size * 0.78, y + size * 0.55), 1)
            pygame.draw.arc(surface, (180, 180, 188),
                            (x + size * 0.72, y + size * 0.52,
                             size * 0.12, size * 0.12), 3.0, 6.0, 1)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_timer,
                      total_cooldown=60, attack_vector=None):
        if not self.image:
            return
        hand_x = unit_rect.centerx + (11 if facing_right else -11)
        hand_y = unit_rect.centery + 4
        img = self.image if facing_right else pygame.transform.flip(
            self.image, True, False)
        rot = pygame.transform.rotate(img, -35 if facing_right else 35)
        surface.blit(rot, rot.get_rect(center=(hand_x, hand_y - 10)))
