# ai/orc_ai.py
from ai.base_ai import BaseAI


class OrcAI(BaseAI):
    """
    Orc AI: Rage-mekaniikka.
    Kun HP putoaa alle 40%, orkki raivostuu kerran per taistelu:
    +4 STR, +15% liikenopeus, eikä koskaan pakene (no_retreat).
    Muuten delegoi BaseAI:lle.
    """

    def __init__(self, unit):
        super().__init__(unit)
        self.enraged = False

    def execute_ai(self, all_units, obstacles, manager=None):
        u = self.unit
        if (not self.enraged and not u.is_dead
                and u.current_hp < u.max_hp * 0.40):
            self.enraged = True
            self.no_retreat = True
            u.strength += 4
            u.walk_speed *= 1.15
            if manager:
                manager.vfx.show_damage(u.rect.centerx, u.rect.top - 40,
                                        "ENRAGED!", color=(255, 60, 60))
        super().execute_ai(all_units, obstacles, manager)
