# items/tiered_weapons.py
"""Tier-aseet L30 asti (pelitesti 27) - sama runko kuin tier-panssareilla.

RATKAISU: jokainen tier-ase PERII perheensä weak_-toteutuksesta, joten
LMB-hold-erikoiset (LUNGE SLASH / WHIRLWIND / GROUND SLAM / FAN OF
KNIVES / DASH-THRUST / CLEAN SHOT / OVERLOAD / ARCANE STREAM), äänet,
swing-hitboxit, kaksikätisyys ja AI-käyttö tulevat automaattisesti
KOKO pelin läpi - vain numerot ja identiteetti vaihtuvat.

Vahinko johdetaan asebudjetista (25 % tason gear-budjetista, sama
käyrä kuin panssareilla): dmg(t) = anchor x budget(t)/budget(2),
missä anchor = weak-aseen vahinko (weak ~ tier 2). Tier 8 -miekka lyö
satoja - linjassa L30-statikäyrään ja T8-loitsuihin.

Grafiikka: weak-luokkien koodipiirretty kädessä-grafiikka + kortti-
ikoni toimivat placeholdereina (oikeat kuvat tulevat myöhemmin);
kortti-ikoniin lisätään rarity-värinen kehys jotta tier erottuu.
"""

import pygame

from progression.stat_curve import gear_stat_budget
from items.gear_scaling import (gear_tier_level, gear_price,
                                gear_level_req)
from items.tiered_gear import RARITY_BY_TIER

from items.swords.weak_sword import WeakSword
from items.daggers.weak_dagger import WeakDagger
from items.axes.weak_axe import WeakAxe
from items.maces.weak_mace import WeakMace
from items.spears.weak_spear import WeakSpear
from items.bows.weak_bow import WeakBow
from items.crossbows.weak_crossbow import WeakCrossbow
from items.staves.weak_staff import WeakStaff
from items.books.weak_book import WeakBook

RARITY_COLORS = {
    "Common": (150, 150, 150), "Uncommon": (110, 190, 110),
    "Rare": (110, 140, 230), "Epic": (190, 120, 230),
    "Legendary": (240, 180, 80),
}

# Perheen ankkurit: weak-aseen vahinko (= tier 2 -taso) ja kantama
FAMILY_ANCHOR = {
    "sword":    {"base": WeakSword, "dmg": 8, "range": 40,
                 "special": "Lunge Slash (full charge): step in + 2.4x cut"},
    "dagger":   {"base": WeakDagger, "dmg": 7, "range": 28,
                 "special": "Fan of Knives (full charge): throw 3 blades"},
    "axe":      {"base": WeakAxe, "dmg": 11, "range": 38,
                 "special": "Whirlwind (full charge): hit ALL around you"},
    "mace":     {"base": WeakMace, "dmg": 10, "range": 34,
                 "special": "Ground Slam (full charge): damage, daze and "
                            "shove everything near"},
    "spear":    {"base": WeakSpear, "dmg": 11, "range": 60,
                 "special": "Dash-Thrust (full charge): pierce forward "
                            "through the line"},
    "bow":      {"base": WeakBow, "dmg": 9, "range": 300,
                 "special": "Clean Shot (full draw): +25% and the "
                            "fastest arrow"},
    "crossbow": {"base": WeakCrossbow, "dmg": 15, "range": 320,
                 "special": "Heavy bolt: slow crank, brutal alpha strike"},
    "staff":    {"base": WeakStaff, "dmg": 7, "range": 280,
                 "special": "Overload (full charge): the bolt explodes "
                            "on impact"},
    "book":     {"base": WeakBook, "dmg": 8, "range": 245,
                 "special": "Arcane Stream (hold LMB): a torrent of "
                            "small bolts"},
}


def weapon_budget(tier):
    """Aseen osuus (25 %) tason gear-budjetista."""
    return max(1, gear_stat_budget(gear_tier_level(tier)) * 0.25)


def weapon_damage(family, tier):
    """Perheen vahinko tierillä: ankkuri x käyräsuhde (t1 = 60 %)."""
    anchor = FAMILY_ANCHOR[family]["dmg"]
    if tier <= 1:
        return max(3, int(round(anchor * 0.6)))
    ratio = weapon_budget(tier) / weapon_budget(2)
    return max(3, int(round(anchor * ratio)))


def weapon_range(family, tier):
    """Kantama kasvaa maltillisesti tierillä (melee +2/t, ranged +10/t)."""
    base = FAMILY_ANCHOR[family]["range"]
    step = 10 if base >= 200 else 2
    return base + max(0, tier - 2) * step


class _TierWeaponMixin:
    """Yhteinen spec-sovitus + rikas describe + rarity-kehys korttiin."""

    def _apply_spec(self, spec):
        self.spec = dict(spec)
        self.gear_id = spec["id"]
        self.tier = int(spec["tier"])
        self.line = spec["family"]
        self.name = spec["name"]
        self.flavor = spec.get("flavor", "")
        self.rarity = RARITY_BY_TIER.get(self.tier, "Rare")
        self.damage = weapon_damage(self.line, self.tier)
        self.attack_range = weapon_range(self.line, self.tier)
        self.cost = int(gear_price(self.tier) * 1.1)   # aseet arvokkaimpia
        self.level_req = gear_level_req(self.tier)
        self.level_required = self.level_req
        self.icon_color = RARITY_COLORS.get(self.rarity, (160, 160, 160))
        self.description = (f"Tier {self.tier} {self.line} - "
                            f"{FAMILY_ANCHOR[self.line]['special']}")
        # Kauppalistan alaotsikkokentät
        self.damage_type = "Weapon"
        self.archetype = self.line

    def describe(self):
        lines = []
        if self.flavor:
            lines.append(self.flavor)
            lines.append("")
        lines.append(f"Weapon: {self.line.capitalize()}   "
                     f"Tier: {self.tier}   ({self.rarity})")
        lines.append(f"Damage: {self.damage}   Range: {self.attack_range}")
        sc = getattr(self, "scaling", {}) or {}
        if sc:
            lines.append("Scaling: " + ", ".join(
                f"{k} x{v}" for k, v in sc.items()))
        if getattr(self, "two_handed", False):
            lines.append("Two-handed: no shield or off-hand")
        lines.append("Hold LMB: " + FAMILY_ANCHOR[self.line]["special"])
        lines.append(f"Requires: Level {self.level_req} + "
                     f"{self.line.capitalize()} Training   "
                     f"Price: {self.cost} SP")
        lines.append("")
        lines.append(f"Made for level ~{gear_tier_level(self.tier)} "
                     f"fighters; higher tiers dwarf it.")
        return "\n".join(lines)

    def draw_card_icon(self, surface, x, y, size):
        # Perheen placeholder-piirto + rarity-kehys (tier erottuu heti)
        try:
            super().draw_card_icon(surface, x, y, size)
        except Exception:
            pygame.draw.rect(surface, (70, 70, 75), (x, y, size, size))
        pygame.draw.rect(surface, self.icon_color, (x, y, size, size), 3)
        if self.tier >= 5:
            pygame.draw.rect(surface, self.icon_color,
                             (x + 3, y + 3, size - 6, size - 6), 1)


class TieredSword(_TierWeaponMixin, WeakSword):
    def __init__(self, spec):
        super().__init__()
        self._apply_spec(spec)


class TieredDagger(_TierWeaponMixin, WeakDagger):
    def __init__(self, spec):
        super().__init__()
        self._apply_spec(spec)


class TieredAxe(_TierWeaponMixin, WeakAxe):
    def __init__(self, spec):
        super().__init__()
        self._apply_spec(spec)


class TieredMace(_TierWeaponMixin, WeakMace):
    def __init__(self, spec):
        super().__init__()
        self._apply_spec(spec)


class TieredSpear(_TierWeaponMixin, WeakSpear):
    def __init__(self, spec):
        super().__init__()
        self._apply_spec(spec)


class TieredBow(_TierWeaponMixin, WeakBow):
    def __init__(self, spec):
        super().__init__()
        self._apply_spec(spec)


class TieredCrossbow(_TierWeaponMixin, WeakCrossbow):
    def __init__(self, spec):
        super().__init__()
        self._apply_spec(spec)


class TieredStaff(_TierWeaponMixin, WeakStaff):
    def __init__(self, spec):
        super().__init__()
        self._apply_spec(spec)


class TieredBook(_TierWeaponMixin, WeakBook):
    def __init__(self, spec):
        super().__init__()
        self._apply_spec(spec)


FAMILY_CLASS = {
    "sword": TieredSword, "dagger": TieredDagger, "axe": TieredAxe,
    "mace": TieredMace, "spear": TieredSpear, "bow": TieredBow,
    "crossbow": TieredCrossbow, "staff": TieredStaff, "book": TieredBook,
}
