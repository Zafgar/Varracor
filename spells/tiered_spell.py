# spells/tiered_spell.py
"""Data-vetoinen tier-loitsu. Yksi luokka joka toteuttaa kaikki
katalogin loitsut: numerot (vahinko/kerroin/mana/hinta) johdetaan
tier-perustasta (spell_scaling), käyttäytyminen arkkityypistä.

Arkkityypit:
- nuke          : yhden kohteen ammus
- aoe           : ammus joka räjähtää (aluevahinko)
- dot           : ammus joka sytyttää/myrkyttää (vahinko yli ajan)
- heal          : parantaa liittolaista
- utility       : oma alue-pulssi (vähän vahinkoa + hidastus/tainnutus)

Jokaisella loitsulla on RIKAS selite (describe()) jonka kauppa näyttää:
vahinkotyyppi, kantama, vahinko+INT-kerroin, mana, hinta ja erityisefekti.
"""
import math
import pygame

from items.base_item import Spell
from sound_manager import sound_system
from vfx import MagicProjectile
from spells.spell_scaling import (
    scaled_damage, tier_base, tier_int_coef, tier_mana, tier_price)


# Vahinkotyypin väri (VFX). Kaikki ei-fyysisiä -> ohittavat torjunnan.
DAMAGE_COLORS = {
    "Arcane": (170, 110, 240),
    "Fire": (255, 110, 50),
    "Frost": (120, 200, 255),
    "Lightning": (130, 220, 255),
    "Holy": (255, 240, 170),
    "Necrotic": (150, 210, 160),
    "Nature": (120, 210, 120),
    "Poison": (150, 220, 120),
    "Magic": (150, 150, 255),
}

SCHOOL_COLORS = {
    "pure": (120, 150, 255),
    "holy": (255, 240, 170),
    "necromancy": (150, 210, 160),
    "druidism": (120, 210, 120),
}

RARITY_BY_TIER = {1: "Common", 2: "Common", 3: "Uncommon", 4: "Uncommon",
                  5: "Rare", 6: "Rare", 7: "Epic", 8: "Legendary"}

# Arkkityypin oletuskäyttäytyminen (kantama, cooldown-framet, statukset)
_ARCH_DEFAULTS = {
    "nuke":    {"range": 400, "cd": 90,  "skillshot": True},
    "aoe":     {"range": 380, "cd": 150, "skillshot": True, "radius": 100},
    "dot":     {"range": 380, "cd": 130, "skillshot": True},
    "heal":    {"range": 320, "cd": 180, "skillshot": False},
    "utility": {"range": 180, "cd": 240, "skillshot": False},
}

# DoT-status vahinkotyypin mukaan
_DOT_STATUS = {
    "Fire": "Burn", "Poison": "Poison", "Nature": "Poison",
    "Necrotic": "Poison",
}


class TieredSpell(Spell):
    def __init__(self, spec):
        super().__init__()
        self.spec = dict(spec)
        self.spell_id = spec["id"]
        self.name = spec["name"]
        self.tier = int(spec["tier"])
        self.school = spec.get("school", "pure")
        self.archetype = spec.get("archetype", "nuke")
        self.damage_type = spec.get("damage_type", "Arcane")
        self.flavor = spec.get("flavor", "")

        d = _ARCH_DEFAULTS.get(self.archetype, _ARCH_DEFAULTS["nuke"])
        self.range = int(spec.get("range", d["range"]))
        self.cooldown_max = int(spec.get("cooldown", d["cd"]))
        self.is_skillshot = bool(spec.get("skillshot", d["skillshot"]))
        self.radius = int(spec.get("radius", d.get("radius", 100)))

        self.mana_cost = int(spec.get("mana", tier_mana(self.tier)))
        self.cost = int(spec.get("price", tier_price(self.tier)))  # kauppahinta
        self.rarity = spec.get("rarity", RARITY_BY_TIER.get(self.tier, "Rare"))
        self.icon_color = DAMAGE_COLORS.get(self.damage_type, (150, 150, 255))
        self.description = self.short_line()

    # ---- Selitetekstit (kaupan "iso selite") ----
    def _range_label(self):
        r = self.range
        if r <= 90:
            return "self / melee"
        if r <= 280:
            return "short"
        if r <= 450:
            return "medium"
        return "long"

    def _effect_line(self):
        a = self.archetype
        if a == "aoe":
            return f"Bursts on impact, hitting all foes within {self.radius}px."
        if a == "dot":
            st = _DOT_STATUS.get(self.damage_type, "Burn")
            word = "burns" if st == "Burn" else "poisons"
            return f"On hit it {word} the target, dealing damage over time."
        if a == "heal":
            return "Restores health to the chosen ally (or yourself)."
        if a == "utility":
            return (f"Erupts around you within {self.radius}px: light damage "
                    f"and slows every enemy caught in it.")
        return "Strikes a single target for direct damage."

    def short_line(self):
        verb = "Heals" if self.archetype == "heal" else "Deals"
        return (f"{verb} {self.damage_type} — Tier {self.tier} "
                f"{self.school.capitalize()} spell.")

    def describe(self):
        """Kaupan iso selite: flavor + mekaniikka (tyyppi, kantama,
        vahinko+INT, mana, hinta, erityisefekti)."""
        base = int(tier_base(self.tier, self.archetype))
        coef = round(tier_int_coef(self.tier, self.archetype), 2)
        amount_word = "Healing" if self.archetype == "heal" else "Damage"
        lines = []
        if self.flavor:
            lines.append(self.flavor)
            lines.append("")
        lines.append(f"School: {self.school.capitalize()}   "
                     f"Tier: {self.tier}   ({self.rarity})")
        lines.append(f"Type: {self.damage_type}"
                     + ("" if self.archetype == "heal"
                        else "  (ignores blocking)"))
        lines.append(f"Range: {self.range}px ({self._range_label()})")
        lines.append(f"{amount_word}: {base} + INT x {coef}")
        lines.append(f"Mana: {self.mana_cost}   "
                     f"Cooldown: {self.cooldown_max / 60:.1f}s   "
                     f"Price: {self.cost} SP")
        lines.append("")
        lines.append(self._effect_line())
        return "\n".join(lines)

    # ---- Casting ----
    def _amount(self, caster):
        return scaled_damage(self.tier, getattr(caster, "intelligence", 0),
                             self.archetype)

    def cast(self, caster, target, manager, target_pos=None):
        if caster.current_mana < self.mana_cost:
            return False

        if self.archetype == "heal":
            ally = target if (target is not None
                              and not getattr(target, "is_dead", False)
                              and getattr(target, "team_color", None)
                              == getattr(caster, "team_color", None)) else caster
            caster.current_mana -= self.mana_cost
            ally.heal(self._amount(caster), manager)
            try:
                manager.vfx.create_heal_effect(ally.rect.centerx,
                                               ally.rect.centery)
            except Exception:
                pass
            return True

        if self.archetype == "utility":
            caster.current_mana -= self.mana_cost
            self._cast_utility(caster, manager)
            return True

        # nuke / aoe / dot -> tähdätty ammus
        if not target_pos and target:
            target_pos = target.rect.center
        if not target_pos:
            return False
        caster.current_mana -= self.mana_cost
        dmg = self._amount(caster)
        proj = _TieredProjectile(
            caster.rect.centerx, caster.rect.centery, target_pos,
            speed=14, damage=dmg, owner=caster, manager=manager, spell=self)
        manager.vfx.add_projectile(proj)
        return True

    def _cast_utility(self, caster, manager):
        cx, cy = caster.rect.center
        dmg = self._amount(caster)
        try:
            manager.vfx.create_shockwave(cx, cy, color=self.icon_color,
                                         max_radius=self.radius, width=5)
        except Exception:
            pass
        my = getattr(caster, "team_color", None)
        for u in list(getattr(manager, "all_units", [])):
            if u is caster or getattr(u, "is_dead", False):
                continue
            if getattr(u, "team_color", None) == my:
                continue
            if math.hypot(u.rect.centerx - cx, u.rect.centery - cy) > self.radius:
                continue
            u.take_damage(dmg, self.damage_type, attacker=caster, manager=manager)
            try:
                u.apply_status("Slow", 120)
            except Exception:
                pass

    def draw_card_icon(self, surface, x, y, size):
        rect = pygame.Rect(x, y, size, size)
        sc = SCHOOL_COLORS.get(self.school, (140, 140, 160))
        pygame.draw.rect(surface, (18, 18, 24), rect, border_radius=8)
        pygame.draw.rect(surface, sc, rect, 2, border_radius=8)
        cx, cy = x + size // 2, y + size // 2
        pygame.draw.circle(surface, self.icon_color, (cx, cy), int(size * 0.26))
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), int(size * 0.10))
        # Tier-pisteet alalaidassa
        for i in range(self.tier):
            px = x + 6 + i * 6
            if px < x + size - 4:
                pygame.draw.circle(surface, sc, (px, y + size - 6), 2)


class _TieredProjectile(MagicProjectile):
    def __init__(self, x, y, target_pos, speed, damage, owner, manager, spell):
        col = spell.icon_color
        super().__init__(x, y, target_pos, speed, damage, owner, manager,
                         color=col, size=11)
        self.spell = spell

    def on_hit(self, target):
        a = self.spell.archetype
        dtype = self.spell.damage_type
        if a == "aoe":
            self._explode()
            return
        target.take_damage(self.damage, dtype, self.owner, self.manager)
        if a == "dot":
            st = _DOT_STATUS.get(dtype, "Burn")
            per = max(1, int(self.damage * 0.35))
            try:
                target.apply_status(st, 180, per)
            except Exception:
                pass
        try:
            self.manager.vfx.create_impact_sparks(
                self.rect.centerx, self.rect.centery, color=self.color, count=6)
        except Exception:
            pass

    def on_wall_hit(self):
        if self.spell.archetype == "aoe":
            self._explode()
        else:
            self.kill()

    def _explode(self):
        cx, cy = self.rect.center
        try:
            self.manager.vfx.create_shockwave(cx, cy, color=self.color,
                                              max_radius=self.spell.radius,
                                              width=5)
        except Exception:
            pass
        owner_team = getattr(self.owner, "team_color", None)
        for u in list(self.manager.all_units):
            if u is self.owner or getattr(u, "is_dead", False):
                continue
            if getattr(u, "team_color", None) == owner_team:
                continue
            if math.hypot(u.rect.centerx - cx, u.rect.centery - cy) <= self.spell.radius:
                u.take_damage(self.damage, self.spell.damage_type,
                              self.owner, self.manager)
        self.kill()
