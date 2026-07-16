import pygame
import math
from items.base_item import Spell
from sound_manager import sound_system


class RaiseSkeleton(Spell):
    """Necromancian ensimmäinen loitsu: nostaa yhden luurankosoturin
    taistelemaan loitsijan puolella. 'Kivi' jonka voi antaa hahmolle jolla
    on Necro-suunta auki taitopuussa.

    Kouluportti (tuleva): school='necromancy'. Vahinkotyyppi ei olennainen
    - tämä on summon."""

    def __init__(self):
        super().__init__()
        self.name = "Raise Skeleton"
        self.tier = 1
        self.rarity = "Rare"
        self.cost = 400
        self.school = "necromancy"
        self.description = ("Bind a restless bone-servant to fight at your "
                            "side until it falls.")
        self.mana_cost = 25
        self.cooldown_max = 360   # 6 s
        self.range = 200
        self.is_skillshot = False
        self.icon_color = (150, 210, 160)  # kalpea vihreä

    def _team_group(self, caster, manager):
        """Palauttaa ryhmän johon summon lisätään (loitsijan puoli)."""
        my = getattr(manager, "my_team", None)
        if my is not None and caster in my:
            return my
        return getattr(manager, "enemy_team", None)

    # --- Summon-cap: montako olentoa loitsija saa pitää yllä ---
    @staticmethod
    def summon_cap(caster):
        """1 perusolento + Summoner-puun nodet (summon_max)."""
        eff = getattr(caster, "school_effects", {}) or {}
        return 1 + int(eff.get("summon_max", 0))

    @staticmethod
    def living_summons(caster, manager):
        out = []
        for u in list(getattr(manager, "all_units", [])):
            if getattr(u, "is_summon", False) \
                    and getattr(u, "summon_owner", None) is caster \
                    and not getattr(u, "is_dead", False):
                out.append(u)
        return out

    def cast(self, caster, target, manager, target_pos=None):
        if caster.current_mana < self.mana_cost:
            return False

        # CAP-tarkistus ENNEN manan kulutusta: AI ei tuhlaa manaa turhaan.
        # Poikkeus: jos heikoin oma summon on matalilla HP:illa (<35%),
        # se kannattaa korvata tuoreella - vanha vapautetaan.
        cap = self.summon_cap(caster)
        alive = self.living_summons(caster, manager)
        if len(alive) >= cap:
            weakest = min(alive, key=lambda s: s.current_hp / max(1, s.max_hp))
            if weakest.current_hp / max(1, weakest.max_hp) < 0.35:
                weakest.is_dead = True
                weakest.current_hp = 0
                try:
                    manager.vfx.create_impact_sparks(
                        weakest.rect.centerx, weakest.rect.centery,
                        color=(120, 180, 130), count=8)
                except Exception:
                    pass
            else:
                return False   # täysi eikä korvattavaa -> ei castia

        caster.current_mana -= self.mana_cost

        from units.undead_skeleton import UndeadSkeleton
        # Spawnaa loitsijan viereen (hieman kohti kursoria/kohdetta)
        cx, cy = caster.rect.center
        ox = 60 if getattr(caster, "facing_right", True) else -60
        sx, sy = cx + ox, cy
        skelly = UndeadSkeleton("Risen Servant", sx, sy,
                                team_color=getattr(caster, "team_color", None))
        # Nostatettu luuranko on heikompi kuin villi (tasapaino).
        # Grave Legion (summon_tier) nostaa laatua: +HP ja +voima.
        eff = getattr(caster, "school_effects", {}) or {}
        tier_up = int(eff.get("summon_tier", 0))
        skelly.max_hp = 45 + tier_up * 45        # tier 1 -> 90 HP
        skelly.current_hp = skelly.max_hp
        skelly.strength += tier_up * 6
        skelly.is_summon = True
        skelly.summon_owner = caster
        if hasattr(skelly, "assign_manager"):
            try:
                skelly.assign_manager(manager)
            except Exception:
                pass

        group = self._team_group(caster, manager)
        if group is not None:
            group.add(skelly)
        if getattr(manager, "all_units", None) is not None:
            manager.all_units.add(skelly)

        # VFX + ääni
        try:
            manager.vfx.create_shockwave(sx, sy, color=(120, 200, 150),
                                         max_radius=50, width=4)
            manager.vfx.create_impact_sparks(sx, sy, color=(150, 230, 170),
                                             count=12)
        except Exception:
            pass
        try:
            sound_system.play_sound("recruit")
        except Exception:
            pass
        return True

    def draw_card_icon(self, surface, x, y, size):
        rect = pygame.Rect(x, y, size, size)
        pygame.draw.rect(surface, (18, 24, 18), rect, border_radius=8)
        pygame.draw.rect(surface, (120, 200, 150), rect, 2, border_radius=8)
        cx, cy = x + size // 2, y + size // 2
        # kallo
        pygame.draw.circle(surface, (210, 230, 210), (cx, cy - 4), int(size * 0.20))
        pygame.draw.rect(surface, (210, 230, 210),
                         (cx - int(size * 0.12), cy, int(size * 0.24), int(size * 0.18)))
        pygame.draw.circle(surface, (20, 30, 20), (cx - 5, cy - 5), 3)
        pygame.draw.circle(surface, (20, 30, 20), (cx + 5, cy - 5), 3)
