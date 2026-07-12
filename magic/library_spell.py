# magic/library_spell.py
"""
LibrarySpell - yksi generinen Spell-luokka joka lukee tietonsa
SPELL_LIBRARYsta (magic/spell_data.py). Nain satoja loitsuja saa ilman
satoja luokkatiedostoja.

Tukee kolmea perustyyppia:
  damage : taikaprojektiili (koulun vari), voi lisata statuksen osuessa
  heal   : parantaa kohteen (kaveri) - ei projektiili
  debuff : projektiili joka lisaa statuksen (Slow/Silence/Burn/...)
"""
from items.base_item import Spell
from magic.spell_data import SPELL_LIBRARY
from magic.schools import school_color


class LibrarySpell(Spell):
    def __init__(self, spell_name):
        super().__init__()
        d = SPELL_LIBRARY[spell_name]
        self.spell_id = spell_name
        self.name = spell_name
        self.school = d.get("school", "pure")
        self.tier = int(d.get("tier", 1))
        self.cast_type = d.get("cast", "instant")
        self.kind = d.get("kind", "damage")
        self.is_heal = (self.kind == "heal")

        self.mana_cost = int(d.get("mana", 10))
        self.strain = float(d.get("strain", 5))
        self.cooldown_max = int(d.get("cooldown", 90))
        self.range = int(d.get("range", 300))
        self.damage = int(d.get("power", 12))       # vahinko TAI parannus
        self.scaling = dict(d.get("scaling", {"INT": 1.0}))
        self.status = d.get("status")               # (type, duration, dmg)
        self.rarity = d.get("rarity", "Common")
        self.cost = int(d.get("cost", 40 * self.tier))
        self.description = d.get("desc", "")

        # VFX
        self.projectile_color = school_color(self.school)
        self.projectile_speed = 11
        self.projectile_size = 9 + min(8, self.tier)
        self.is_skillshot = (self.kind in ("damage", "debuff"))

    def _amount(self, caster):
        return int(self.damage + caster.intelligence * self.scaling.get("INT", 0.0))

    def cast(self, caster, target, manager, target_pos=None):
        if manager is None:
            return False

        # --- HEAL ---
        if self.kind == "heal":
            tgt = target or caster
            amt = self._amount(caster)
            if hasattr(tgt, "heal"):
                tgt.heal(amt, manager)
            else:
                tgt.current_hp = min(tgt.max_hp, tgt.current_hp + amt)
            manager.vfx.show_damage(tgt.rect.centerx, tgt.rect.top - 20,
                                    f"+{amt}", color=self.projectile_color)
            return True

        # --- DAMAGE / DEBUFF (projektiili) ---
        if not target_pos and target is not None:
            target_pos = target.rect.center
        if not target_pos:
            return False

        dmg = self._amount(caster)
        from vfx import MagicProjectile
        proj = MagicProjectile(caster.rect.centerx, caster.rect.centery, target_pos,
                               self.projectile_speed, dmg, caster, manager,
                               color=self.projectile_color, size=self.projectile_size)
        manager.vfx.add_projectile(proj)

        # Debuff: lisaa status kohteeseen (flavor: loitsun osuessa)
        if self.status and target is not None and not getattr(target, "is_dead", False):
            st = self.status
            try:
                target.apply_status(st[0], int(st[1]), int(st[2]) if len(st) > 2 else 0)
            except Exception:
                pass
        return True


def create_library_spell(name):
    """Palauttaa LibrarySpellin jos nimi on kirjastossa, muuten None."""
    if name in SPELL_LIBRARY:
        return LibrarySpell(name)
    return None
