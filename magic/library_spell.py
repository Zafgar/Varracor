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
        self.buff = d.get("buff")                    # {"type","duration"}
        self.summon = d.get("summon")                # class name
        self.summon_count = int(d.get("summon_count", 1))
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

    def _summon(self, caster, manager):
        import random
        from settings import PLAYER_TEAM
        from units.undead_skeleton import UndeadSkeleton
        cls_map = {"UndeadSkeleton": UndeadSkeleton}
        cls = cls_map.get(self.summon or "UndeadSkeleton", UndeadSkeleton)
        on_player = getattr(caster, "team_color", None) == PLAYER_TEAM
        grp = manager.my_team if on_player else manager.enemy_team
        aw = getattr(getattr(manager, "current_arena", None), "width", 1920) or 1920
        ah = getattr(getattr(manager, "current_arena", None), "height", 1080) or 1080
        for _ in range(self.summon_count):
            x = min(aw - 20, max(20, caster.rect.centerx + random.randint(-60, 60)))
            y = min(ah - 20, max(20, caster.rect.centery + random.randint(-60, 60)))
            minion = cls("Servant", x, y, caster.team_color)
            grp.add(minion)
            manager.all_units.add(minion)
            manager.vfx.create_spawn_fog(x, y)

    def cast(self, caster, target, manager, target_pos=None):
        if manager is None:
            return False

        # Abyssal Weave (heron Vortex-taika): kyla huomaa ja pelastyy.
        if self.school == "abyssal":
            if (getattr(manager, "player_character", None) is caster
                    and hasattr(manager, "notice_vortex_use")):
                manager.notice_vortex_use("abyssal")

        # --- WARP (Warping-puu): lyhyt siirto ilman teleporttia ---
        if self.kind == "warp":
            if not target_pos and target is not None:
                target_pos = target.rect.center
            if target_pos:
                import math
                dx = target_pos[0] - caster.rect.centerx
                dy = target_pos[1] - caster.rect.centery
                dist = math.hypot(dx, dy) or 1
                r = min(self.range, dist)
                caster.rect.centerx += int(dx / dist * r)
                caster.rect.centery += int(dy / dist * r)
                manager.vfx.create_shockwave(caster.rect.centerx, caster.rect.centery,
                                             color=self.projectile_color, max_radius=60)
            return True

        # --- DISPEL (Severing-puu): purkaa suojat ja vahingoittaa ---
        if self.kind == "dispel":
            if target is not None and not getattr(target, "is_dead", False):
                target.status_effects = [e for e in target.status_effects
                                         if e.get("type") not in ("Warded", "Shielded")]
                target.take_damage(self._amount(caster), "Magic",
                                   attacker=caster, manager=manager)
                manager.vfx.show_damage(target.rect.centerx, target.rect.top - 20,
                                        "SEVERED", color=self.projectile_color)
            return True

        # --- DRAIN (Taint-puu): korruptio + elamansiirto ---
        if self.kind == "drain":
            if target is not None and not getattr(target, "is_dead", False):
                dmg = self._amount(caster)
                target.take_damage(dmg, "Poison", attacker=caster, manager=manager)
                if self.status:
                    st = self.status
                    target.apply_status(st[0], int(st[1]), int(st[2]) if len(st) > 2 else 0)
                heal = int(dmg * 0.5)
                if hasattr(caster, "heal"):
                    caster.heal(heal, manager)
            return True

        # --- BUFF (Warded/Barkskin ym.) - kohdistuu itseen ---
        if self.kind == "buff":
            b = self.buff or {"type": "Warded", "duration": 300}
            caster.apply_status(b.get("type", "Warded"), int(b.get("duration", 300)), 0)
            manager.vfx.show_damage(caster.rect.centerx, caster.rect.top - 20,
                                    self.name, color=self.projectile_color)
            return True

        # --- SUMMON (Raise Servant ym.) ---
        if self.kind == "summon":
            self._summon(caster, manager)
            manager.vfx.show_damage(caster.rect.centerx, caster.rect.top - 20,
                                    self.name, color=self.projectile_color)
            return True

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
