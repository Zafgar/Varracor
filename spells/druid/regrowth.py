import pygame
from items.base_item import Spell
from sound_manager import sound_system


class Regrowth(Spell):
    """Verdant Covenantin ensimmäinen loitsu: luonnon uudistava voima.
    Asettaa liittolaiseen (tai itseen) parannuksen-yli-ajan (Regen): pieni
    parannus joka sekunti muutaman sekunnin ajan. 'Kivi' hahmolle jolla on
    Druid-suunta auki.

    Kouluportti (tuleva): school='druidism'."""

    def __init__(self):
        super().__init__()
        self.name = "Regrowth"
        self.tier = 1
        self.rarity = "Rare"
        self.cost = 300
        self.school = "druidism"
        self.description = ("Wrap an ally in living green: heals a little "
                            "each second for several seconds.")
        self.mana_cost = 22
        self.cooldown_max = 180   # 3 s
        self.range = 300
        self.is_skillshot = False
        self.heal_per_tick = 8    # + INT-skaalaus
        self.ticks = 5            # sekuntia (Regen tikittää /60 framea)
        self.icon_color = (110, 210, 120)

    def cast(self, caster, target, manager, target_pos=None):
        if caster.current_mana < self.mana_cost:
            return False
        # Kohde: annettu liittolainen, muuten loitsija itse
        ally = target if target is not None and not getattr(target, "is_dead",
                                                            False) else caster
        # Ei paranneta vihollista: jos kohde on eri joukkuetta, käännä itseen
        if getattr(ally, "team_color", None) != getattr(caster, "team_color", None):
            ally = caster
        caster.current_mana -= self.mana_cost

        per = int(self.heal_per_tick + caster.intelligence * 0.3)
        # Druidin Life-haara (hot_power): +30% per piste HoT-tehoon
        hot = int((getattr(caster, "school_effects", {}) or {})
                  .get("hot_power", 0))
        if hot > 0:
            per = int(per * (1.0 + 0.30 * hot))
        duration = self.ticks * 60 + 1   # +1 jotta ensitikki osuu %60==0 kohtaan
        try:
            ally.apply_status("Regen", duration, per)
        except Exception:
            # Jos kohteella ei ole status-järjestelmää, paranna kertaheitolla
            if hasattr(ally, "heal"):
                ally.heal(per * self.ticks, manager=manager)

        try:
            manager.vfx.create_heal_effect(ally.rect.centerx, ally.rect.centery)
        except Exception:
            pass
        try:
            sound_system.play_sound("heal")
        except Exception:
            pass
        return True

    def draw_card_icon(self, surface, x, y, size):
        rect = pygame.Rect(x, y, size, size)
        pygame.draw.rect(surface, (16, 30, 18), rect, border_radius=8)
        pygame.draw.rect(surface, (110, 210, 120), rect, 2, border_radius=8)
        cx, cy = x + size // 2, y + size // 2
        # lehti/verso
        pygame.draw.line(surface, (120, 200, 130), (cx, cy + size // 3),
                         (cx, cy - size // 4), 3)
        pygame.draw.circle(surface, (140, 230, 150),
                           (cx - 6, cy - size // 6), int(size * 0.12))
        pygame.draw.circle(surface, (140, 230, 150),
                           (cx + 6, cy - size // 8), int(size * 0.12))
