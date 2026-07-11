"""Potions brewed from Muckford farm herbs.

The item registry discovers this module automatically. The shared base class is
named ``Potion`` so the existing registry base filter ignores it, while the
concrete brews remain discoverable. Icons are procedural placeholders;
future art can be dropped into ``assets/items/potions`` without code changes.
"""

from __future__ import annotations

import os

import pygame

from items.base_item import Item
from sound_manager import sound_system


class Potion(Item):
    """Shared consumable behaviour for farm-brewed potions."""

    display_name = "Farm Potion"
    description_text = "A simple herbal draught."
    bottle_color = (100, 180, 110)
    rarity_name = "Common"
    price = 20
    image_path = ""
    cooldown_frames = 120

    def __init__(self):
        if type(self) is Potion:
            raise TypeError("Potion is an abstract potion base")
        super().__init__()
        self.name = self.display_name
        self.description = self.description_text
        self.rarity = self.rarity_name
        self.cost = self.price
        self.type = "potion"
        self.slot_type = "usable"
        self.cooldown_max = self.cooldown_frames
        self.image = None
        self._load_image()

    def _load_image(self):
        if not self.image_path or not os.path.exists(self.image_path):
            return
        try:
            raw = pygame.image.load(self.image_path)
            if pygame.display.get_surface():
                raw = raw.convert_alpha()
            self.image = raw
        except Exception:
            self.image = None

    def draw_card_icon(self, surface, x, y, size):
        if self.image:
            surface.blit(pygame.transform.smoothscale(self.image, (size, size)), (x, y))
            return

        # Placeholder bottle with a cork, glass highlight and herb-coloured liquid.
        pygame.draw.rect(surface, (35, 36, 42), (x, y, size, size), border_radius=5)
        neck_w = max(5, size // 5)
        neck_x = x + size // 2 - neck_w // 2
        neck_y = y + size // 7
        body = pygame.Rect(x + size // 4, y + size // 3,
                           size // 2, max(8, size // 2))
        pygame.draw.rect(surface, (126, 86, 48),
                         (neck_x, neck_y, neck_w, max(4, size // 9)),
                         border_radius=2)
        pygame.draw.rect(surface, (185, 205, 210),
                         (neck_x, neck_y + size // 10, neck_w, size // 4), 2,
                         border_radius=2)
        pygame.draw.rect(surface, self.bottle_color, body,
                         border_radius=max(3, size // 10))
        pygame.draw.rect(surface, (215, 230, 230), body, 2,
                         border_radius=max(3, size // 10))
        pygame.draw.line(surface, (255, 255, 255),
                         (body.x + max(2, size // 12), body.y + 4),
                         (body.x + max(2, size // 12), body.bottom - 7),
                         max(1, size // 18))

    def _consume(self, caster):
        equipment = getattr(caster, "equipment", {})
        for slot, item in list(equipment.items()):
            if item is self:
                equipment[slot] = None
                return

    def _play(self, sound_name="heal"):
        try:
            sound_system.play_sound(sound_name)
        except Exception:
            pass

    def apply_effect(self, caster, manager) -> bool:
        raise NotImplementedError

    def cast(self, caster, target=None, manager=None, target_pos=None):
        if caster is None or not self.apply_effect(caster, manager):
            return False
        self._consume(caster)
        self._play()
        return True


class BitterleafTonic(Potion):
    display_name = "Bitterleaf Tonic"
    description_text = "Restores 25% of maximum health."
    bottle_color = (82, 164, 78)
    price = 24
    image_path = "assets/items/potions/bitterleaf_tonic.png"

    def apply_effect(self, caster, manager):
        maximum = max(1, int(getattr(caster, "max_hp", 1)))
        before = float(getattr(caster, "current_hp", 0))
        caster.current_hp = min(maximum, before + max(1, int(maximum * 0.25)))
        if caster.current_hp >= maximum * 0.90:
            caster.injured = False
            caster.injury_severity = None
        return caster.current_hp > before


class MarshmintDraught(Potion):
    display_name = "Marshmint Draught"
    description_text = "Restores 55% of maximum stamina."
    bottle_color = (62, 184, 155)
    price = 28
    image_path = "assets/items/potions/marshmint_draught.png"

    def apply_effect(self, caster, manager):
        maximum = max(1, int(getattr(caster, "max_stamina", 1)))
        before = float(getattr(caster, "current_stamina", 0))
        caster.current_stamina = min(maximum, before + max(1, int(maximum * 0.55)))
        return caster.current_stamina > before


class MoonpetalElixir(Potion):
    display_name = "Moonpetal Elixir"
    description_text = "Restores 45% of maximum mana."
    bottle_color = (105, 105, 225)
    rarity_name = "Rare"
    price = 55
    image_path = "assets/items/potions/moonpetal_elixir.png"

    def apply_effect(self, caster, manager):
        maximum = max(1, int(getattr(caster, "max_mana", 1)))
        before = float(getattr(caster, "current_mana", 0))
        caster.current_mana = min(maximum, before + max(1, int(maximum * 0.45)))
        return caster.current_mana > before


class SiltrootAntidote(Potion):
    display_name = "Siltroot Antidote"
    description_text = "Clears poison-like effects and restores 10% health."
    bottle_color = (184, 150, 70)
    price = 38
    image_path = "assets/items/potions/siltroot_antidote.png"

    def apply_effect(self, caster, manager):
        changed = False
        for attr in ("poisoned", "is_poisoned", "venom_stacks", "poison_stacks"):
            if hasattr(caster, attr) and getattr(caster, attr):
                current = getattr(caster, attr)
                setattr(caster, attr, False if isinstance(current, bool) else 0)
                changed = True
        effects = getattr(caster, "status_effects", None)
        if isinstance(effects, list):
            kept = [e for e in effects if "poison" not in str(e).lower()
                    and "venom" not in str(e).lower()]
            changed = changed or len(kept) != len(effects)
            caster.status_effects = kept
        maximum = max(1, int(getattr(caster, "max_hp", 1)))
        before = float(getattr(caster, "current_hp", 0))
        caster.current_hp = min(maximum, before + max(1, int(maximum * 0.10)))
        return changed or caster.current_hp > before


class SunleafRestorative(Potion):
    display_name = "Sunleaf Restorative"
    description_text = "Restores 40% health and clears a minor injury."
    bottle_color = (232, 184, 66)
    rarity_name = "Rare"
    price = 70
    image_path = "assets/items/potions/sunleaf_restorative.png"

    def apply_effect(self, caster, manager):
        maximum = max(1, int(getattr(caster, "max_hp", 1)))
        before = float(getattr(caster, "current_hp", 0))
        was_injured = bool(getattr(caster, "injured", False))
        caster.current_hp = min(maximum, before + max(1, int(maximum * 0.40)))
        if getattr(caster, "injury_severity", None) in (None, "Minor"):
            caster.injured = False
            caster.injury_severity = None
        return caster.current_hp > before or (was_injured and not caster.injured)


class IronstemFortifier(Potion):
    display_name = "Ironstem Fortifier"
    description_text = "Restores 20% health and 35% stamina."
    bottle_color = (108, 122, 110)
    rarity_name = "Rare"
    price = 62
    image_path = "assets/items/potions/ironstem_fortifier.png"

    def apply_effect(self, caster, manager):
        max_hp = max(1, int(getattr(caster, "max_hp", 1)))
        max_stamina = max(1, int(getattr(caster, "max_stamina", 1)))
        old_hp = float(getattr(caster, "current_hp", 0))
        old_stamina = float(getattr(caster, "current_stamina", 0))
        caster.current_hp = min(max_hp, old_hp + max(1, int(max_hp * 0.20)))
        caster.current_stamina = min(
            max_stamina,
            old_stamina + max(1, int(max_stamina * 0.35)),
        )
        return caster.current_hp > old_hp or caster.current_stamina > old_stamina
