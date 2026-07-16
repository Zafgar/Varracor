# items/tiered_gear.py
"""Data-vetoinen tier-varuste (sama idea kuin TieredSpell).

Numerot johdetaan gear_scaling-budjeteista; identiteetti (nimi, linja,
flavor) tulee katalogista. Jokaisella varusteella on RIKAS selite
(describe): slot, tier, statit, koulubonukset, tasovaatimus, hinta.

Linjat = erikoistumisreitit:
- Vartalot: warrior (heavy STR+DEF), skirmisher (medium DEX),
  arcanist robe (cloth INT+mana)
- Relikvit (off_hand, magia on oma iso alue):
  pure focus, necro summoner, necro leech, druid life, druid wild,
  holy light - kukin tukee eri koulusuuntaa (school_bonuses kertyy
  unit.school_effects-sanakirjaan varusteista)."""

import pygame

from items.base_item import Item
from items.gear_scaling import (piece_budget, gear_price, gear_level_req,
                                gear_tier_level)

RARITY_BY_TIER = {1: "Common", 2: "Common", 3: "Uncommon", 4: "Uncommon",
                  5: "Rare", 6: "Rare", 7: "Epic", 8: "Legendary"}

# Linjamääritykset: slot, tyyppi/panssariryhmä, statipainot (osuus
# budjetista), kiinteät lisät ja koulubonukset tier-funktiona.
LINES = {
    "warrior": {
        "slot": "body", "kind": "armor", "armor_group": "heavy",
        "weights": {"str": 0.65}, "defense_share": 0.35,
        "hp_per_tier": 30,
        "color": (170, 150, 130),
        "theme": "Forged plate for the front line",
    },
    "skirmisher": {
        "slot": "body", "kind": "armor", "armor_group": "medium",
        "weights": {"dex": 0.70, "str": 0.15}, "defense_share": 0.15,
        "hp_per_tier": 18,
        "color": (150, 170, 140),
        "theme": "Supple leathers for fast blades",
    },
    "arcanist": {
        "slot": "body", "kind": "armor", "armor_group": "cloth",
        "school": "pure",
        "weights": {"int": 0.80}, "defense_share": 0.05,
        "mana_per_tier": 25,
        "color": (140, 150, 220),
        "theme": "Woven robes humming with the Weave",
    },
    "pure_focus": {
        "slot": "off_hand", "kind": "relic", "school": "pure",
        "weights": {"int": 0.85}, "mana_per_tier": 15,
        "mana_regen_per_tier": 0.03,
        "color": (120, 150, 255),
        "theme": "A prism focus of the Collegium",
    },
    "necro_summoner": {
        "slot": "off_hand", "kind": "relic", "school": "necromancy",
        "weights": {"int": 0.70},
        "school_bonuses": lambda t: {"summon_max": 1 if t >= 5 else 0,
                                     "summon_tier": 1 if t >= 8 else 0},
        "color": (150, 210, 160),
        "theme": "A bound-soul vessel that swells your legion",
    },
    "necro_leech": {
        "slot": "off_hand", "kind": "relic", "school": "necromancy",
        "weights": {"int": 0.70},
        "school_bonuses": lambda t: {"lifesteal_pct": round(0.02 * t, 2)},
        "color": (110, 190, 130),
        "theme": "A thirsting fetish that drinks what you wound",
    },
    "druid_life": {
        "slot": "off_hand", "kind": "relic", "school": "druidism",
        "weights": {"int": 0.70},
        "school_bonuses": lambda t: {"hot_power": t // 2,
                                     "heal_power": t // 4},
        "color": (120, 210, 120),
        "theme": "A living seed-charm of endless spring",
    },
    "druid_wild": {
        "slot": "off_hand", "kind": "relic", "school": "druidism",
        "weights": {"int": 0.60, "str": 0.15},
        "school_bonuses": lambda t: {"form_upkeep_cut":
                                     min(0.40, round(0.05 * t, 2))},
        "color": (150, 180, 100),
        "theme": "A beast-bone totem that steadies your forms",
    },
    "holy_light": {
        "slot": "off_hand", "kind": "relic", "school": "holy",
        "weights": {"int": 0.70},
        "school_bonuses": lambda t: {"heal_power": t // 2},
        "color": (255, 240, 170),
        "theme": "A dawn-blessed censer of the Synod",
    },
}


class TieredGear(Item):
    def __init__(self, spec):
        super().__init__()
        self.spec = dict(spec)
        self.gear_id = spec["id"]
        self.name = spec["name"]
        self.tier = int(spec["tier"])
        self.line = spec["line"]
        line = LINES[self.line]
        self.slot_type = line["slot"]
        self.type = line["kind"]
        self.school = line.get("school")
        self.armor_group = line.get("armor_group", "")
        self.flavor = spec.get("flavor", "")
        self.rarity = RARITY_BY_TIER.get(self.tier, "Rare")
        self.cost = gear_price(self.tier)
        self.level_req = gear_level_req(self.tier)
        self.level_required = self.level_req   # can_equip lukee tämän
        self.icon_color = line.get("color", (160, 160, 170))
        # Kauppalistan alaotsikko
        self.damage_type = "Gear"
        self.archetype = line["kind"]

        # Statit budjetista
        budget = piece_budget(self.tier, self.slot_type)
        w = line.get("weights", {})
        self.str_bonus = int(budget * w.get("str", 0.0))
        self.dex_bonus = int(budget * w.get("dex", 0.0))
        self.int_bonus = int(budget * w.get("int", 0.0))
        self.defense = int(budget * line.get("defense_share", 0.0))
        self.health_bonus = int(line.get("hp_per_tier", 0) * self.tier)
        self.mana_bonus = int(line.get("mana_per_tier", 0) * self.tier)
        mr = line.get("mana_regen_per_tier", 0.0)
        self.passive_bonuses = ({"mana_regen": round(mr * self.tier, 2)}
                                if mr else {})
        sb = line.get("school_bonuses")
        self.school_bonuses = {k: v for k, v in (sb(self.tier) if sb else {}).items()
                               if v}
        self.description = self.short_line()

    def short_line(self):
        return (f"{LINES[self.line]['theme']} — Tier {self.tier} "
                f"{self.slot_type.replace('_', '-')} piece.")

    _SB_LABELS = {
        "summon_max": "+{v} max summons",
        "summon_tier": "+{v} summon quality",
        "lifesteal_pct": "+{p}% necrotic life steal",
        "hot_power": "+{v} heal-over-time power",
        "heal_power": "+{v} healing power",
        "form_upkeep_cut": "-{p}% shapeshift mana upkeep",
    }

    def describe(self):
        lines = []
        if self.flavor:
            lines.append(self.flavor)
            lines.append("")
        slot_lbl = "Body armor" if self.slot_type == "body" else "Off-hand relic"
        lines.append(f"Slot: {slot_lbl}   Tier: {self.tier}   ({self.rarity})")
        if self.armor_group:
            lines.append(f"Armor class: {self.armor_group.capitalize()}")
        if self.school:
            lines.append(f"School: {self.school.capitalize()}")
        stats = []
        for lbl, v in (("STR", self.str_bonus), ("DEX", self.dex_bonus),
                       ("INT", self.int_bonus), ("DEF", self.defense),
                       ("HP", self.health_bonus), ("Mana", self.mana_bonus)):
            if v:
                stats.append(f"+{v} {lbl}")
        mr = self.passive_bonuses.get("mana_regen")
        if mr:
            stats.append(f"+{mr}/s mana regen")
        if stats:
            lines.append("Stats: " + ", ".join(stats))
        for k, v in self.school_bonuses.items():
            tpl = self._SB_LABELS.get(k, k + " +{v}")
            lines.append("Specialization: "
                         + tpl.format(v=v, p=int(round(float(v) * 100))))
        lines.append(f"Requires: Level {self.level_req}   "
                     f"Price: {self.cost} SP")
        lines.append("")
        lines.append(f"Made for level ~{gear_tier_level(self.tier)} "
                     f"fighters; higher tiers dwarf it.")
        return "\n".join(lines)

    def draw_card_icon(self, surface, x, y, size):
        rect = pygame.Rect(x, y, size, size)
        pygame.draw.rect(surface, (20, 20, 26), rect, border_radius=8)
        pygame.draw.rect(surface, self.icon_color, rect, 2, border_radius=8)
        cx, cy = x + size // 2, y + size // 2
        if self.slot_type == "body":
            # Rintapanssari/kaapu
            pygame.draw.polygon(surface, self.icon_color, [
                (cx - size // 4, y + 8), (cx + size // 4, y + 8),
                (cx + size // 3, cy), (cx + size // 5, y + size - 8),
                (cx - size // 5, y + size - 8), (cx - size // 3, cy)])
        else:
            # Relikvi (kide)
            pygame.draw.polygon(surface, self.icon_color, [
                (cx, y + 8), (cx + size // 4, cy), (cx, y + size - 8),
                (cx - size // 4, cy)])
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 3)
